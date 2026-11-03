//! Verdict, run record, signing, and the measurements both roles report.

use std::{
    fs,
    io::{Read, Write},
    os::unix::fs::OpenOptionsExt,
    path::Path,
    time::Instant,
};

use anyhow::{Context, Result, anyhow, bail};
use ed25519_dalek::{Signature, Signer, SigningKey, VerifyingKey};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};

#[derive(Serialize, Deserialize, Clone, Copy)]
pub struct Limits {
    pub max_sent: usize,
    pub max_recv: usize,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct VerdictRequest {
    pub forwarded_headers_sha256: String,
    pub method: String,
    pub host: String,
    pub path: String,
    pub body_sha256: String,
    pub body_bytes: usize,
    /// Present only for withheld credentials.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub withheld: Option<Withheld>,
}

/// The sent bytes left unrevealed (the selected credential header value), as offsets into
/// the session's sent bytes, and the SHA-256 of the circuit whose proof showed
/// that they, with the session's other withheld values, hold no CR or LF.
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug)]
pub struct Withheld {
    /// Public header name, canonical lower case; the value alone is withheld.
    pub header: String,
    pub start: usize,
    pub end: usize,
    pub no_cr_lf: String,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct VerdictResponse {
    #[serde(deserialize_with = "Option::<String>::deserialize")]
    pub content_type: Option<String>,
    pub status: u16,
    pub body_sha256: String,
    pub body_bytes: usize,
    pub transfer: String,
    /// Base64 images inline in the body, decoded: a delivered image file is
    /// checked against these.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub images: Vec<VerdictImage>,
}

#[derive(Serialize, Deserialize, Clone, PartialEq, Debug)]
pub struct VerdictImage {
    /// From the data URL, or a `b64_json` field's sibling `media_type`;
    /// empty if neither gives one.
    pub media_type: String,
    pub sha256: String,
    pub bytes: usize,
}

impl VerdictImage {
    pub fn of(image: &crate::http::InlineImage) -> Self {
        Self {
            media_type: image.media_type.clone(),
            sha256: sha256_hex(&image.bytes),
            bytes: image.bytes.len(),
        }
    }
}

/// One exchange of a session, as the witness saw it: a leaf of the session's
/// Merkle tree is the SHA-256 of this record in canonical JSON. The salt is
/// random per record, so a sibling's hash on another customer's path reveals
/// nothing about this exchange, however guessable its prompt.
#[derive(Serialize, Deserialize, Clone)]
pub struct ExchangeRecord {
    pub session_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub operator_pub: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub operator_statement_sha256: Option<String>,
    /// The exchange's place in the session, from 1 in the order sent; also
    /// its place among the tree's leaves.
    pub n: usize,
    pub job_id: String,
    pub outcome: String,
    pub request: VerdictRequest,
    pub response: VerdictResponse,
    /// 32 random bytes, hex.
    pub salt: String,
}

impl ExchangeRecord {
    pub fn leaf(&self) -> Result<crate::merkle::Hash> {
        let value = serde_json::to_value(self)?;
        Ok(Sha256::digest(canonical_bytes(&value)).into())
    }
}

/// One per witnessed session: the server's identity once, and the root of a
/// Merkle tree whose leaves are the session's exchange records, in order.
#[derive(Serialize, Deserialize, Clone)]
pub struct Verdict {
    pub profile: crate::Profile,
    pub v: u32,
    pub session_id: String,
    pub mode: String,
    pub server_name: String,
    /// Leaves under `root`.
    pub exchanges: usize,
    pub root: String,
    pub limits: Limits,
    pub verified_at: String,
    pub verifier_pub: String,
    #[serde(default)]
    pub sig: String,
}

/// What a customer gets for its own exchange: the exchange record, with its
/// salt, the sibling hashes from its leaf to the session root, and the
/// signed session verdict. It holds no other exchange's record or salt.
#[derive(Serialize, Deserialize, Clone)]
pub struct Receipt {
    pub v: u32,
    pub record: ExchangeRecord,
    pub path: Vec<String>,
    pub verdict: Value,
}

/// Canonical JSON: object keys sorted, no whitespace.
pub fn canonical_bytes(value: &Value) -> Vec<u8> {
    let mut out = String::new();
    canonical(value, &mut out);
    out.into_bytes()
}

/// The signed message: the object without `sig`, as JSON with object keys
/// sorted and no whitespace. Verdicts and seals are both signed this way.
fn signing_bytes(value: &Value) -> Vec<u8> {
    let mut value = value.clone();
    if let Value::Object(map) = &mut value {
        map.remove("sig");
    }
    canonical_bytes(&value)
}

fn canonical(value: &Value, out: &mut String) {
    match value {
        Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            out.push('{');
            for (i, key) in keys.into_iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                out.push_str(&Value::String(key.clone()).to_string());
                out.push(':');
                canonical(&map[key], out);
            }
            out.push('}');
        }
        Value::Array(items) => {
            out.push('[');
            for (i, item) in items.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                canonical(item, out);
            }
            out.push(']');
        }
        other => out.push_str(&other.to_string()),
    }
}

/// Sets `pub_field` to the key's public half and `sig` to its signature over
/// everything else.
pub fn sign(value: &mut Value, pub_field: &str, key: &SigningKey) {
    value[pub_field] = Value::String(hex::encode(key.verifying_key().as_bytes()));
    let sig = hex::encode(key.sign(&signing_bytes(value)).to_bytes());
    value["sig"] = Value::String(sig);
}

/// Checks `sig` against the key named in the object's own `pub_field`, over
/// every field as written. Whether that key is the expected one is the
/// caller's question.
pub fn verify_signature(value: &Value, pub_field: &str) -> Result<()> {
    let text = |field: &str| {
        value[field]
            .as_str()
            .ok_or_else(|| anyhow!("{field} is missing or not a string"))
    };
    let public: [u8; 32] = hex::decode(text(pub_field)?)?
        .try_into()
        .map_err(|_| anyhow!("{pub_field} is not 32 bytes"))?;
    let sig: [u8; 64] = hex::decode(text("sig")?)?
        .try_into()
        .map_err(|_| anyhow!("sig is not 64 bytes"))?;
    VerifyingKey::from_bytes(&public)?
        .verify_strict(&signing_bytes(value), &Signature::from_bytes(&sig))
        .map_err(|_| anyhow!("signature is invalid"))
}

/// Loads a signing key (a verifier's or a customer's), creating it (mode 600)
/// and its `.pub` on first use.
pub fn load_or_create_key(path: &Path) -> Result<SigningKey> {
    if path.exists() {
        let text =
            fs::read_to_string(path).with_context(|| format!("reading {}", path.display()))?;
        let seed: [u8; 32] = hex::decode(text.trim())
            .ok()
            .and_then(|b| b.try_into().ok())
            .ok_or_else(|| anyhow!("{} is not a hex 32-byte key", path.display()))?;
        return Ok(SigningKey::from_bytes(&seed));
    }
    if let Some(dir) = path.parent() {
        fs::create_dir_all(dir)?;
    }
    let seed: [u8; 32] = random_bytes::<32>()?;
    let mut file = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(path)
        .with_context(|| format!("creating {}", path.display()))?;
    writeln!(file, "{}", hex::encode(seed))?;
    let key = SigningKey::from_bytes(&seed);
    fs::write(
        path.with_extension("pub"),
        format!("{}\n", hex::encode(key.verifying_key().as_bytes())),
    )?;
    Ok(key)
}

pub fn random_bytes<const N: usize>() -> Result<[u8; N]> {
    let mut buf = [0u8; N];
    fs::File::open("/dev/urandom")?.read_exact(&mut buf)?;
    Ok(buf)
}

pub fn sha256_hex(data: &[u8]) -> String {
    hex::encode(Sha256::digest(data))
}

pub fn now_rfc3339() -> String {
    chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Secs, true)
}

/// To the millisecond: when a session's record was written decides the
/// epoch it is counted in.
pub fn now_ms_rfc3339() -> String {
    chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Millis, true)
}

/// Milliseconds since `t`, to 0.1 ms.
pub fn ms(t: Instant) -> f64 {
    (t.elapsed().as_secs_f64() * 10_000.0).round() / 10.0
}

/// The `N` of the nearest `phase-N` directory in `dir`, if any. The phase is
/// a property of where a run is filed, not of the code.
pub fn phase_of(dir: &Path) -> Option<u32> {
    let dir = std::path::absolute(dir).ok()?;
    dir.components()
        .rev()
        .find_map(|c| c.as_os_str().to_str()?.strip_prefix("phase-")?.parse().ok())
}

/// The error and its causes on one line. tlsn's messages already include
/// their cause, so a cause whose text is already present is not repeated.
pub fn describe(e: &anyhow::Error) -> String {
    let mut out = String::new();
    for cause in e.chain() {
        let text = cause.to_string();
        if out.contains(&text) {
            continue;
        }
        if !out.is_empty() {
            out.push_str(": ");
        }
        out.push_str(&text);
    }
    out
}

/// Writes `value` as indented JSON and a newline; returns the bytes written.
pub fn write_json(path: &Path, value: &impl Serialize) -> Result<usize> {
    let mut text = serde_json::to_string_pretty(value)?;
    text.push('\n');
    fs::write(path, &text).with_context(|| format!("writing {}", path.display()))?;
    Ok(text.len())
}

/// Writes `path` whole or not at all, by renaming a finished file into
/// place, so a process stopped mid-write leaves the earlier version.
pub fn write_json_atomic(path: &Path, value: &impl Serialize) -> Result<usize> {
    let tmp = path.with_extension("tmp");
    let bytes = write_json(&tmp, value)?;
    fs::rename(&tmp, path).with_context(|| format!("renaming {} into place", path.display()))?;
    Ok(bytes)
}

fn rusage() -> libc::rusage {
    // SAFETY: getrusage fills the struct it is given; zeroed is a valid value.
    unsafe {
        let mut usage: libc::rusage = std::mem::zeroed();
        libc::getrusage(libc::RUSAGE_SELF, &mut usage);
        usage
    }
}

/// Process CPU time and wall time at named points of a session, to split
/// what a session costs among its steps. CPU time is the whole process's, so
/// a step's share is its own only when nothing else ran meanwhile.
pub struct Marks {
    start: Instant,
    marks: Vec<Value>,
}

impl Marks {
    pub fn new(start: Instant) -> Self {
        Self {
            start,
            marks: Vec::new(),
        }
    }

    pub fn mark(&mut self, at: &str) {
        self.mark_at(at, Instant::now(), cpu_seconds());
    }

    /// A point observed earlier, at `when` with `cpu` process CPU seconds.
    pub fn mark_at(&mut self, at: &str, when: Instant, cpu: f64) {
        let wall = when.saturating_duration_since(self.start).as_secs_f64() * 1000.0;
        self.marks.push(serde_json::json!({
            "at": at,
            "cpu_s": (cpu * 1000.0).round() / 1000.0,
            "ms": (wall * 10.0).round() / 10.0,
            "threads": threads_now(),
        }));
    }

    pub fn value(&self) -> Value {
        Value::Array(self.marks.clone())
    }
}

/// Threads in this process now.
pub fn threads_now() -> Option<usize> {
    fs::read_dir("/proc/self/task").ok().map(|d| d.count())
}

/// User plus system CPU time of this process so far.
pub fn cpu_seconds() -> f64 {
    let u = rusage();
    let tv = |t: libc::timeval| t.tv_sec as f64 + t.tv_usec as f64 / 1e6;
    tv(u.ru_utime) + tv(u.ru_stime)
}

/// Peak resident set size. Reads `VmHWM`, which `reset_peak_rss` can reset
/// between verifier sessions; falls back to getrusage's lifetime peak.
pub fn peak_rss_mb() -> f64 {
    let hwm_kb = fs::read_to_string("/proc/self/status").ok().and_then(|s| {
        s.lines()
            .find_map(|l| l.strip_prefix("VmHWM:"))
            .and_then(|v| v.trim().trim_end_matches("kB").trim().parse::<f64>().ok())
    });
    let kb = hwm_kb.unwrap_or(rusage().ru_maxrss as f64);
    (kb / 1024.0 * 10.0).round() / 10.0
}

pub fn reset_peak_rss() {
    let _ = fs::write("/proc/self/clear_refs", "5");
}

#[derive(Serialize, Default)]
pub struct Timings {
    pub prewarm: Option<f64>,
    pub user: Option<f64>,
    pub ttfb: Option<f64>,
    /// Streaming: when the final `data: [DONE]` line was on disk, from the
    /// same start as `user` and `ttfb`.
    pub done: Option<f64>,
    pub prove: Option<f64>,
    pub total: Option<f64>,
}

#[derive(Serialize, Default)]
pub struct Bytes {
    pub to_verifier: u64,
    pub from_verifier: u64,
    pub request_body: Option<usize>,
    pub response_body: Option<usize>,
}

#[derive(Serialize)]
pub struct Resources {
    pub peak_rss_mb: f64,
    pub cpu_seconds: f64,
}

#[derive(Serialize)]
pub struct RunRecord {
    pub role: &'static str,
    /// The job, when the session carried at most one; per exchange in
    /// `exchanges` either way.
    pub job_id: Option<String>,
    pub phase: Option<u32>,
    pub label: Option<String>,
    pub mode: Option<&'static str>,
    pub prewarm: bool,
    pub stream: bool,
    pub host: Option<String>,
    pub limits: Option<Limits>,
    pub timings_ms: Timings,
    pub bytes: Bytes,
    pub resources: Resources,
    pub outcome: &'static str,
    pub error: Option<String>,
    /// Whether a connection to the server was opened; `null` when the writer
    /// cannot tell. The basis is in `detail.upstream_called_basis`.
    pub upstream_called: Option<bool>,
    pub rtt_to_verifier_ms: Option<f64>,
    pub started_at: String,
    /// When this record was written, to the millisecond.
    pub recorded_at: String,
    /// Each request sent or meant for the session, in order, with its own job
    /// id, outcome and timings.
    pub exchanges: Vec<Value>,
    /// Role-specific facts: file paths, addresses, hidden ranges.
    pub detail: Value,
}

pub fn ensure_dir(dir: &Path) -> Result<()> {
    if dir.exists() && !dir.is_dir() {
        bail!("{} is not a directory", dir.display());
    }
    fs::create_dir_all(dir).with_context(|| format!("creating {}", dir.display()))
}

/// Effective local cgroup controls, read by the measured process itself.
pub fn cgroup_caps() -> Value {
    let membership = fs::read_to_string("/proc/self/cgroup").unwrap_or_default();
    let path = membership.lines().find_map(|line| line.strip_prefix("0::")).unwrap_or("");
    let base = std::path::Path::new("/sys/fs/cgroup").join(path.trim_start_matches('/'));
    let read = |name: &str| fs::read_to_string(base.join(name)).ok().map(|s| s.trim().to_owned());
    serde_json::json!({"path":path,"cpu_max":read("cpu.max"),"memory_max":read("memory.max")})
}
