//! Prover: witnessed HTTPS calls for customers' seals, one or more on one
//! connection. Refuses a request file its seal does not match, commits with
//! caps, sends each request as its file arrives, writes each response body as
//! it completes, proves everything except the `Authorization` values, commits
//! to those values and proves they hold no CR or LF, and keeps the verifier's
//! signed verdict for the session. The verdict signs a Merkle root over the
//! session's exchange records; the prover checks every record against what
//! it sent and received and the root against the records, then writes each
//! job a receipt that proves its own record and holds no other.

use std::{
    fs, future::IntoFuture, io::Write as _, path::PathBuf, pin::Pin, sync::Mutex, time::Duration,
    time::Instant,
};

use anyhow::{Context, Result, anyhow, bail};
use futures::{AsyncRead, AsyncReadExt as _, AsyncWrite, AsyncWriteExt as _};
use serde::Deserialize;
use serde_json::{Map, Value, json};
use tlsn::rangeset::set::RangeSet;
use tlsn::{
    Session,
    config::{
        prove::ProveConfig,
        prover::ProverConfig,
        tls::TlsClientConfig,
        tls_commit::{mpc::MpcTlsConfig, proxy::ProxyTlsConfig},
    },
    connection::{DnsName, ServerName},
    hash::HashAlgId,
    prover::{
        Prover, ProverOutput,
        state::{CommitAccepted, Committed},
    },
    transcript::{
        Direction, TranscriptCommitConfig, TranscriptCommitment, TranscriptCommitmentKind,
        TranscriptSecret,
    },
};
use tokio::net::TcpStream;
use tokio_util::compat::TokioAsyncReadCompatExt;

use crate::{
    Profile, Mode, ProverArgs, http,
    io::{
        AbortOnDrop, AppData, Counters, Counting, Hello, HelloTap, RecordTap, connect_upstream,
        process_facts, read_frame, server_hello, session_ended, step, write_frame,
    },
    merkle,
    record::{
        Bytes, ExchangeRecord, Limits, Marks, Receipt, Resources, RunRecord, Timings, Verdict,
        VerdictImage, Withheld, cpu_seconds, describe, ensure_dir, ms, now_ms_rfc3339, now_rfc3339,
        peak_rss_mb, phase_of, random_bytes, reset_peak_rss, sha256_hex, verify_signature,
        write_json,
    },
    seal, zk,
};

#[derive(Default)]
struct State {
    /// The session's files are `<stem>.*`: the first job id and this run's
    /// id, since a job id may be presented more than once.
    stem: String,
    /// Each request sent or meant for the session, in order.
    exchanges: Vec<Exchange>,
    host: Option<String>,
    rtt_ms: Option<f64>,
    counters: Counters,
    timings: Timings,
    /// MPC mode: this prover opened TCP to the server.
    dialed: bool,
    /// MPC mode: the first bytes from the server, for the negotiated suite.
    hello: Option<Hello>,
    /// The TLS connection to the server has been started.
    tls_started: bool,
    /// MPC mode: application-data records on this prover's server connection.
    app_data: Option<AppData>,
    /// Response bytes received from the TLS connection.
    received: usize,
    /// Request bytes written to the TLS connection.
    sent: usize,
    /// --stream: the response body as it was written to disk.
    live: Option<Live>,
    /// Pre-warmed, the session is waiting for its first request file.
    waiting: bool,
    marks: Option<Marks>,
    detail: Map<String, Value>,
    /// Session-only memory. Never serialized, hashed, or printed.
    temporary_credential: Option<String>,
    obtained: Value,
    session_name: String,
    cleanup_pending: bool,
    dead_template: Option<crate::management::Template>,
    router: Option<std::sync::Arc<crate::router::Call>>,
    safe_retry: bool,
    witness_session_id: String,
}

impl State {
    fn mark(&mut self, at: &str) {
        if let Some(marks) = self.marks.as_mut() {
            marks.mark(at);
        }
    }

    /// Whether the request reached the network: `no` when it cannot have,
    /// `yes` when it did, `possibly` when this prover cannot tell.
    fn request_sent(&self) -> &'static str {
        if !self.tls_started {
            return "no";
        }
        if self.received > 0 {
            return "yes";
        }
        match &self.app_data {
            // The prover holds the server connection and sees every record.
            Some(records) if records.sent() > 0 || records.recv() > 0 => "yes",
            Some(_) => "no",
            // Proxy mode: the verifier relays the records. A TLS 1.2 client
            // sends no application data before its handshake completes.
            None if proxy_handshake().is_some() => "possibly",
            None => "no",
        }
    }

    /// Whether a connection to the server was opened, and how this prover
    /// knows; `None` when it cannot tell.
    fn upstream_called(&self, mode: Mode) -> (Option<bool>, &'static str) {
        match mode {
            Mode::Mpc if self.dialed => (Some(true), "this prover opened TCP to the server"),
            Mode::Mpc => (
                Some(false),
                "this prover opened no connection to the server",
            ),
            Mode::Proxy if !self.tls_started => (
                Some(false),
                "this prover handed the verifier no TLS bytes, and the verifier dials the server only on them",
            ),
            // The server's certificate and handshake can only have come over
            // a connection the verifier opened.
            Mode::Proxy if self.received > 0 || proxy_handshake().is_some() => (
                Some(true),
                "the TLS handshake with the server completed through the verifier, so the verifier had connected to it",
            ),
            Mode::Proxy => (
                None,
                "unknown: this prover handed its first TLS bytes to the verifier, which dials the server on them, but the handshake did not complete, and whether the verifier dialed is not visible here",
            ),
        }
    }
}

/// One request of the session and what became of it.
struct Exchange {
    n: usize,
    /// From the seal, once it is read and its job id checked.
    job_id: Option<String>,
    request: Option<http::BuiltRequest>,
    body_sha256: Option<String>,
    /// Where the request starts in the session's sent bytes.
    sent_at: Option<usize>,
    /// When the request file arrived; `user` runs from here.
    arrived: Option<Instant>,
    /// The response body's SHA-256 and inline images, once it is on disk.
    response: Option<(String, Vec<VerdictImage>)>,
    error: Option<String>,
    detail: Map<String, Value>,
}

impl Exchange {
    fn new(n: usize) -> Self {
        Self {
            n,
            job_id: None,
            request: None,
            body_sha256: None,
            sent_at: None,
            arrived: None,
            response: None,
            error: None,
            detail: Map::new(),
        }
    }

    /// The bytes withheld from the verifier, as offsets into the session's
    /// sent bytes.
    fn withheld(&self) -> Option<std::ops::Range<usize>> {
        let (request, at) = (self.request.as_ref()?, self.sent_at?);
        Some(request.auth_value.start + at..request.auth_value.end + at)
    }

    /// `verified` is the session's; it covers only the requests the session
    /// sent and got a response to. A request refused before sending stays
    /// `not_sent` whatever became of the rest.
    fn record(mut self, verified: bool, sent: &'static str) -> Value {
        let outcome = if self.sent_at.is_none() || sent == "no" {
            "not_sent"
        } else if self.response.is_none() {
            "response_lost"
        } else if verified {
            "verified"
        } else {
            "delivered_unwitnessed"
        };
        let mut out = Map::new();
        out.insert("n".into(), json!(self.n));
        out.insert("job_id".into(), json!(self.job_id));
        out.insert("outcome".into(), json!(outcome));
        out.insert("error".into(), json!(self.error));
        out.append(&mut self.detail);
        Value::Object(out)
    }
}

/// `path` with `{n}` standing for the request's place in the session.
fn nth(path: &std::path::Path, n: usize) -> PathBuf {
    PathBuf::from(path.to_string_lossy().replace("{n}", &n.to_string()))
}

/// When tlsn's proxy-mode TLS client finished its handshake in the current
/// session, with the process CPU seconds then.
static PROXY_HANDSHAKE: Mutex<Option<(Instant, f64)>> = Mutex::new(None);

fn proxy_handshake() -> Option<(Instant, f64)> {
    *PROXY_HANDSHAKE.lock().unwrap_or_else(|e| e.into_inner())
}

/// In proxy mode the prover's TLS client runs inside tlsn on a stream the
/// prover cannot wrap, so whether its handshake completed is read from tlsn's
/// own debug event. At alpha.15 that is "inner client is transitioning to
/// connected", logged once `is_handshaking()` turns false.
pub struct ProxyHandshake;

impl<S: tracing::Subscriber> tracing_subscriber::Layer<S> for ProxyHandshake {
    fn on_event(&self, event: &tracing::Event<'_>, _: tracing_subscriber::layer::Context<'_, S>) {
        if crate::stop::message(event) == "inner client is transitioning to connected" {
            *PROXY_HANDSHAKE.lock().unwrap_or_else(|e| e.into_inner()) =
                Some((Instant::now(), cpu_seconds()));
        }
    }
}

/// A response body written to disk as it arrives, with when each part landed,
/// in milliseconds from the request being ready to send.
struct Live {
    file: fs::File,
    start: Instant,
    /// `start` as Unix time, to line up with observations from outside.
    start_unix_ms: f64,
    written: usize,
    /// The incomplete last line, for finding server-sent-event lines.
    line: Vec<u8>,
    ttfb: Option<f64>,
    last_write: Option<f64>,
    first_data: Option<f64>,
    first_token: Option<f64>,
    last_token: Option<f64>,
    done: Option<f64>,
    closed: Option<f64>,
    data_lines: usize,
    /// Milliseconds and bytes on disk after each write; the first 2000.
    writes: Vec<(f64, usize)>,
}

impl Live {
    fn new(path: &std::path::Path, start: Instant) -> Result<Self> {
        Ok(Self {
            file: fs::File::create(path).with_context(|| format!("creating {}", path.display()))?,
            start,
            start_unix_ms: {
                let now = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap_or_default();
                ((now - start.elapsed()).as_secs_f64() * 1000.0).round()
            },
            written: 0,
            line: Vec::new(),
            ttfb: None,
            last_write: None,
            first_data: None,
            first_token: None,
            last_token: None,
            done: None,
            closed: None,
            data_lines: 0,
            writes: Vec::new(),
        })
    }

    /// Appends whatever more of the body `received` now holds.
    fn update(&mut self, received: &[u8]) -> std::io::Result<()> {
        let mut skip = self.written;
        let mut new = Vec::new();
        for range in http::body_so_far(received) {
            let part = &received[range];
            if skip >= part.len() {
                skip -= part.len();
                continue;
            }
            new.extend_from_slice(&part[skip..]);
            skip = 0;
        }
        if new.is_empty() {
            return Ok(());
        }
        self.file.write_all(&new)?;
        let at = ms(self.start);
        self.written += new.len();
        self.ttfb.get_or_insert(at);
        self.last_write = Some(at);
        if self.writes.len() < 2000 {
            self.writes.push((at, self.written));
        }
        self.line.extend_from_slice(&new);
        while let Some(end) = self.line.iter().position(|&b| b == b'\n') {
            let line: Vec<u8> = self.line.drain(..=end).collect();
            let line = String::from_utf8_lossy(&line);
            let Some(data) = line.trim_end().strip_prefix("data:") else {
                continue;
            };
            let data = data.trim_start();
            self.data_lines += 1;
            self.first_data.get_or_insert(at);
            if data == "[DONE]" {
                self.done.get_or_insert(at);
            } else if serde_json::from_str::<Value>(data).ok().and_then(|v| {
                v["choices"][0]["delta"]["content"]
                    .as_str()
                    .map(|c| !c.is_empty())
            }) == Some(true)
            {
                self.first_token.get_or_insert(at);
                self.last_token = Some(at);
            }
        }
        Ok(())
    }

    fn facts(&self) -> Value {
        json!({
            "start_unix_ms": self.start_unix_ms,
            "first_body_byte_ms": self.ttfb,
            "last_body_byte_ms": self.last_write,
            "first_data_line_ms": self.first_data,
            "first_token_ms": self.first_token,
            "last_token_ms": self.last_token,
            "done_ms": self.done,
            "connection_closed_ms": self.closed,
            "data_lines": self.data_lines,
            "bytes_on_disk": self.written,
            "writes": self.writes.len(),
            "write_log": self.writes,
        })
    }
}

/// After the session or tlsn fails, the response bytes already decrypted are
/// still read for this long.
const DRAIN: Duration = Duration::from_secs(3);

#[derive(Deserialize)]
struct Reply {
    verdict: Option<Value>,
    /// The session's exchange records, with their salts, under the verdict's
    /// root.
    #[serde(default)]
    records: Vec<ExchangeRecord>,
    error: Option<String>,
}

/// Serves `--sessions` sessions, one after another, each on its own
/// connection with its own verdict and run record, and stops early once a
/// pre-warmed session's first request does not arrive in time, or once a
/// session is abandoned at --timeout. Returns whether every session served
/// ended verified.
static SHUTDOWN: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);

extern "C" fn stop_sequence(_: libc::c_int) {
    SHUTDOWN.store(true, std::sync::atomic::Ordering::Relaxed);
}

async fn shutdown() {
    while !SHUTDOWN.load(std::sync::atomic::Ordering::Relaxed) {
        tokio::time::sleep(Duration::from_millis(100)).await;
    }
}

pub async fn run(args: ProverArgs, started: Instant) -> Result<bool> {
    if args.is_sequence() {
        // A graceful process exit cancels witness work, then runs cleanup outside
        // the session timeout. SIGKILL and host loss cannot run application code.
        unsafe {
            let mut action: libc::sigaction = std::mem::zeroed();
            action.sa_sigaction = stop_sequence as *const () as usize;
            libc::sigemptyset(&mut action.sa_mask);
            if libc::sigaction(libc::SIGINT, &action, std::ptr::null_mut()) != 0
                || libc::sigaction(libc::SIGTERM, &action, std::ptr::null_mut()) != 0
            {
                bail!("cannot install credential cleanup shutdown handler");
            }
        }
    }
    if args.sessions > 1 {
        let numbered = |p: &std::path::Path| p.to_string_lossy().contains("{s}");
        if args.prewarm.is_none()
            || ![&args.request, &args.seal, &args.out_dir]
                .iter()
                .all(|p| numbered(p))
        {
            bail!(
                "--sessions above 1 needs --prewarm and {{s}} in --request, --seal and --out-dir"
            );
        }
    }
    let mut loaded = Loaded::default();
    let mut all = true;
    for s in 1..=args.sessions {
        let start = if s == 1 { started } else { Instant::now() };
        let (verified, last, _) =
            session(&for_session(&args, s), s, start, &mut loaded, None).await?;
        all &= verified;
        if last {
            break;
        }
    }
    Ok(all)
}

/// `args` for the `s`-th session: `s` in curly braces in --request, --seal
/// and --out-dir stands for it.
fn for_session(args: &ProverArgs, s: u32) -> ProverArgs {
    let sub = |p: &PathBuf| PathBuf::from(p.to_string_lossy().replace("{s}", &s.to_string()));
    ProverArgs {
        request: sub(&args.request),
        seal: sub(&args.seal),
        out_dir: sub(&args.out_dir),
        obtain_request: args.obtain_request.as_ref().map(sub),
        revoke_request: args.revoke_request.as_ref().map(sub),
        dead_check_request: args.dead_check_request.as_ref().map(sub),
        ..args.clone()
    }
}

fn stamp() -> String {
    chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Micros, true)
}

/// Three attempts, each at most ten seconds, independent of session timeout.
/// Only status/error/timing and the already-safe provider hash are persisted.
async fn cleanup(args: &ProverArgs, st: &mut State, loaded: &mut Loaded) {
    let mut attempts = Vec::new();
    let mut succeeded = false;
    for attempt in 1..=3 {
        let t = Instant::now();
        let started_at = stamp();
        let result = async {
            let template =
                crate::management::load(args.revoke_request.as_ref().expect("sequence template"))?;
            let spec = args
                .ca_cert
                .as_ref()
                .map_or("webpki".into(), |p| p.display().to_string());
            let (roots, _) = loaded.roots(&spec).await?;
            crate::management::request(
                &template,
                &roots,
                &st.obtained,
                false,
                &st.session_name,
                Duration::from_secs(args.management_timeout.clamp(1, 10)),
            )
            .await
        }
        .await;
        let (status, error) = match result {
            Ok((status, _)) => {
                succeeded = (200..300).contains(&status);
                (Some(status), None)
            }
            Err(e) => (None, Some(describe(&e))),
        };
        attempts.push(json!({"attempt": attempt, "started_at": started_at,
            "response_received_at": stamp(), "status": status, "error": error, "ms": ms(t)}));
        if succeeded {
            break;
        }
        if attempt < 3 {
            tokio::time::sleep(Duration::from_millis(500)).await;
        }
    }
    st.cleanup_pending = !succeeded;
    st.detail["credential_sequence"]["cleanup"] =
        json!({"succeeded": succeeded, "attempts": attempts});
    st.detail["credential_sequence"]["credential_status"] = json!(if succeeded {
        "cleanup_revoke_accepted"
    } else {
        "cleanup_failed"
    });
    st.mark("cleanup_finished");
}

async fn check_dead(
    args: &ProverArgs,
    st: &mut State,
    loaded: &mut Loaded,
    revoked_at: Instant,
) -> Result<()> {
    let spec = args
        .ca_cert
        .as_ref()
        .map_or("webpki".into(), |p| p.display().to_string());
    let (roots, _) = loaded.roots(&spec).await?;
    let deadline = revoked_at + Duration::from_secs(args.dead_check_timeout.min(10));
    let mut consecutive_refusals = 0;
    let mut accepted_probes = 0;
    st.detail["credential_sequence"]["first_refusal_ms"] = Value::Null;
    st.detail["credential_sequence"]["second_consecutive_refusal_ms"] = Value::Null;
    st.detail["credential_sequence"]["accepted_probe_count"] = json!(0);
    st.detail["credential_sequence"]["poll_interval_ms"] = json!(500);
    loop {
        let remaining = deadline.saturating_duration_since(Instant::now());
        if st.detail["credential_sequence"]["dead_checks"].as_array().map_or(0,Vec::len) as u64 >= args.max_dead_check_attempts {
            bail!("refusal-probe request budget exhausted; no reveal");
        }
        if remaining.is_zero() {
            bail!("credential still accepted at dead-check deadline; no reveal");
        }
        // Record before awaiting: timeout/cancellation still counts this attempt.
        let checks = st.detail["credential_sequence"]["dead_checks"]
            .as_array_mut()
            .expect("initialized");
        checks.push(
            json!({"started_at": stamp(), "since_revoke_ms": ms(revoked_at),
            "response_received_at": null, "status": null, "error": null}),
        );
        let t = Instant::now();
        let result = crate::management::dead_check(
            st.dead_template.as_ref().expect("prepared"),
            &roots,
            st.temporary_credential.as_deref().expect("obtained"),
            remaining.min(Duration::from_secs(args.management_timeout)),
        )
        .await;
        let check = st.detail["credential_sequence"]["dead_checks"]
            .as_array_mut()
            .unwrap()
            .last_mut()
            .unwrap();
        check["response_received_at"] = json!(stamp());
        check["ms"] = json!(ms(t));
        check["response_since_revoke_ms"] = json!(ms(revoked_at));
        let status = match result {
            Ok((status, cost, code, completion, generation_id)) => {
                check["status"] = json!(status);
                check["provider_cost_usd"] = json!(cost);
                check["provider_error_code"] = json!(code);
                check["completion"] = json!(completion);
                check["generation_id"] = json!(generation_id);
                status
            }
            Err(e) => {
                check["error"] = json!(describe(&e));
                return Err(e);
            }
        };
        let accepted = (200..300).contains(&status);
        check["accepted"] = json!(accepted);
        if status == 401 {
            consecutive_refusals += 1;
        } else if accepted {
            consecutive_refusals = 0;
            accepted_probes += 1;
        } else {
            bail!("dead-check returned status {status}; credential death unconfirmed");
        }
        check["consecutive_refusals"] = json!(consecutive_refusals);
        let elapsed = ms(revoked_at);
        let seq = &mut st.detail["credential_sequence"];
        seq["accepted_probe_count"] = json!(accepted_probes);
        if consecutive_refusals > 0 && seq["first_refusal_ms"].is_null() {
            seq["first_refusal_ms"] = json!(elapsed);
        }
        if Instant::now() >= deadline {
            bail!("dead-check deadline reached; no reveal");
        }
        if consecutive_refusals == 2 {
            seq["second_consecutive_refusal_ms"] = json!(elapsed);
            seq["propagation_delay_ms"] = json!(elapsed);
            st.mark("dead_check_refused");
            return Ok(());
        }
        let remaining = deadline.saturating_duration_since(Instant::now());
        if remaining.is_zero() {
            bail!("credential still accepted at dead-check deadline; no reveal");
        }
        // Probe starts are at least 500 ms apart; a slow response can make
        // the interval longer. No request or sleep extends the deadline.
        let delay = Duration::from_millis(500).saturating_sub(t.elapsed());
        tokio::time::sleep(remaining.min(delay)).await;
    }
}

/// What a process sets up once and keeps for every session it serves: the
/// SRS checked against its pin, each circuit with its verification key, and
/// the roots.
#[derive(Clone, Default)]
struct Loaded {
    // Only immutable setup is shared. Protocol/session state stays in State.
    shared: std::sync::Arc<std::sync::Mutex<Setup>>,
}

#[derive(Default)]
struct Setup {
    srs: Option<zk::Srs>,
    circuits: Vec<(zk::Circuit, Value)>,
    roots: Option<(String, tlsn::webpki::RootCertStore, Value)>,
}

impl Loaded {
    async fn circuit(
        &mut self,
        path: &std::path::Path,
        def: &'static zk::Def,
    ) -> Result<(zk::Circuit, Value)> {
        let shared = self.shared.clone();
        let path = path.to_path_buf();
        // Serialize cache misses, not sessions. A concurrent first call must
        // not build the same verification key a second time.
        tokio::task::spawn_blocking(move || {
            let mut setup = shared.lock().unwrap_or_else(|e| e.into_inner());
            if let Some((circuit, about)) = setup.circuits.iter()
                .find(|(c, _)| c.def().sha256 == def.sha256)
            {
                let mut about = about.clone();
                about["set_up_earlier"] = json!(true);
                return Ok((circuit.clone(), about));
            }
            if setup.srs.is_none() {
                setup.srs = Some(zk::srs(&path)?);
            }
            let srs = setup.srs.as_ref().unwrap();
            let (circuit, mut about) = srs.setup(def)?;
            about["srs"] = srs.about().clone();
            setup.circuits.push((circuit.clone(), about.clone()));
            Ok((circuit, about))
        }).await.context("loading the circuit")?
    }

    async fn roots(&mut self, spec: &str) -> Result<(tlsn::webpki::RootCertStore, Value)> {
        let shared = self.shared.clone();
        let spec = spec.to_string();
        tokio::task::spawn_blocking(move || {
            let mut setup = shared.lock().unwrap_or_else(|e| e.into_inner());
            if let Some((loaded, roots, about)) = &setup.roots
                && loaded == &spec
            {
                return Ok((roots.clone(), about.clone()));
            }
            let (roots, about) = crate::roots(&spec)?;
            setup.roots = Some((spec, roots.clone(), about.clone()));
            Ok((roots, about))
        }).await.context("loading root certificates")?
    }
}

/// One session. Returns whether it ended verified, and whether the process
/// serves no more: the session ended waiting for its first request, or was
/// abandoned at --timeout. An abandoned session's proof may still be running
/// on a blocking thread; its result is dropped, but it would share the
/// process's CPU, memory and proving library with a later session, so none
/// starts. Every attempt writes a run record.
async fn session(
    args: &ProverArgs,
    s: u32,
    started: Instant,
    loaded: &mut Loaded,
    router: Option<std::sync::Arc<crate::router::Call>>,
) -> Result<(bool, bool, bool)> {
    *PROXY_HANDSHAKE.lock().unwrap_or_else(|e| e.into_inner()) = None;
    // The first session's CPU time and peak RSS count from the process's
    // start; a later one's from its own.
    let cpu_start = if router.is_some() {
        cpu_seconds()
    } else if s == 1 {
        0.0
    } else {
        reset_peak_rss();
        cpu_seconds()
    };
    ensure_dir(&args.out_dir)?;
    let started_at = now_rfc3339();
    let run_id = hex::encode(random_bytes::<4>()?);
    let mut st = State {
        router,
        stem: format!("unsealed.{run_id}"),
        session_name: format!("tlsw-temp-{}", hex::encode(random_bytes::<16>()?)),
        marks: Some(Marks::new(started)),
        ..State::default()
    };
    if s > 1 {
        st.mark("session_start");
    }
    st.detail.insert(
        "session".into(),
        json!({ "index": s, "of": args.sessions, "process_cpu_seconds_at_start": (cpu_start * 1000.0).round() / 1000.0 }),
    );
    // A pre-warmed prover reads its seal only once the request arrives; the
    // path ties a call refused or failed before then to its job.
    if st.router.is_some() { st.detail.insert("cpu_scope".into(), json!("whole-process delta; concurrent router sessions overlap; use process aggregate for cost")); }
    st.detail.insert("seal_file".into(), json!(args.seal));
    st.detail.insert("batch_max".into(), json!(args.batch_max));
    st.detail
        .insert("tlsn_threads".into(), json!(args.tlsn_threads));
    st.detail
        .insert("batch_window_ms".into(), json!(args.batch_window_ms));

    let limit = Duration::from_secs(args.timeout);
    let router_deadline = st.router.as_ref().map(|call| call.deadline);
    let cancelled = async {
        match router_deadline {
            Some(at) => tokio::time::sleep_until(at.into()).await,
            None => std::future::pending().await,
        }
    };
    let (result, abandoned) = tokio::select! {
        biased;
        _ = cancelled => (Err(anyhow!("evidence deadline exceeded; routing future cancelled")), true),
        _ = shutdown(), if args.is_sequence() => (Err(anyhow!("process shutdown; witnessed session cancelled for credential cleanup")), true),
        result = tokio::time::timeout(limit, witness(args, &run_id, &mut st, loaded)) => match result {
        Ok(result) => (result, false),
        Err(_) => (
            Err(anyhow!(
                "the session did not finish within --timeout {} s and was abandoned",
                args.timeout
            )),
            true,
        ),
        },
    };
    // The witness future (and its transport) is dropped before cleanup. This
    // also covers request rejection, upstream failure and unused prewarm.
    if abandoned {
        if let Some(call) = &st.router {
            call.cancel_delivery().await;
        }
        st.detail
            .insert("routing_cancelled_at".into(), json!(stamp()));
    }
    if st.cleanup_pending {
        cleanup(args, &mut st, loaded).await;
        if st.router.is_some()
            && !st.cleanup_pending
            && st.temporary_credential.is_some()
            && st.dead_template.is_some()
        {
            let result = check_dead(args, &mut st, loaded, Instant::now()).await;
            st.detail["credential_sequence"]["credential_status"] = json!(if result.is_ok() {
                "dead_confirmed"
            } else {
                "death_unconfirmed"
            });
            if let Err(e) = result {
                st.detail["credential_sequence"]["failure"] = json!(describe(&e));
            }
        }
    }
    if let Some(call) = &st.router {
        if !args.is_sequence() {
            call.cleanup_record(json!({"state":"not_applicable","profile":args.profile})).await?;
        } else {
            call.cleanup_record(
                json!({"state":st.detail["credential_sequence"]["credential_status"],
                "disable_accepted":st.detail["credential_sequence"]["cleanup"]["succeeded"] == true
                    || st.detail["credential_sequence"]["credential_status"] == "dead_confirmed"}),
            ).await?;
        }
    }
    if abandoned && s < args.sessions {
        st.detail["session"]["serves_no_more"] = json!("abandoned at --timeout");
    }
    st.timings.total = Some(ms(started));

    let sent = st.request_sent();
    let delivered = st.exchanges.iter().any(|ex| ex.response.is_some());
    let (outcome, error) = match &result {
        Ok(()) => ("verified", None),
        Err(e) => {
            let outcome = if delivered {
                "delivered_unwitnessed"
            } else if sent == "no" {
                "not_sent"
            } else {
                "response_lost"
            };
            (outcome, Some(describe(e)))
        }
    };
    if let (Some(call), Some(reason)) = (&st.router, &error) { call.failure(reason); }
    st.detail.insert("request_sent".into(), json!(sent));
    let (upstream_called, basis) = st.upstream_called(args.mode);
    st.detail
        .insert("upstream_called_basis".into(), json!(basis));
    st.detail
        .insert("response_bytes_received".into(), json!(st.received));
    st.detail
        .insert("request_bytes_sent".into(), json!(st.sent));
    if let Some(records) = &st.app_data {
        st.detail.insert(
            "app_data_records".into(),
            json!({ "to_server": records.sent(), "from_server": records.recv() }),
        );
        // On the wire, beside when the plaintext reached the file.
        if let Some(live) = &st.live {
            let (first, last) = records.recv_times();
            let since = |t: Option<Instant>| {
                t.map(|t| t.saturating_duration_since(live.start).as_secs_f64() * 1e3)
            };
            st.detail.insert(
                "server_records_ms".into(),
                json!({ "first_app_data": since(first), "last_bytes": since(last) }),
            );
        }
    }
    if st.tls_started && matches!(args.mode, Mode::Proxy) {
        st.detail.insert(
            "proxy_handshake_complete".into(),
            json!(proxy_handshake().is_some()),
        );
    }
    if let Some(live) = &st.live {
        st.timings.ttfb = live.ttfb;
        st.timings.done = live.done;
        st.detail.insert("stream".into(), live.facts());
    }
    let record_path = args.out_dir.join(format!("{}.record.json", st.stem));
    let last = st.waiting
        || abandoned
        || SHUTDOWN.load(std::sync::atomic::Ordering::Relaxed)
        || st
            .detail
            .get("credential_sequence")
            .and_then(|v| v.get("hard_stop"))
            .and_then(Value::as_bool)
            == Some(true);
    st.detail.insert("verifier".into(), json!(args.verifier));
    st.detail.insert("process".into(), process_facts());
    if let Some(hello) = &st.hello {
        st.detail.insert("tls".into(), server_hello(hello));
    }
    st.detail.insert("record_file".into(), json!(record_path));
    let job_id = match st.exchanges.as_slice() {
        [only] if args.batch_max == 1 => only.job_id.clone(),
        _ => None,
    };
    let sum = |f: fn(&Exchange) -> Option<usize>| -> Option<usize> {
        st.exchanges.iter().filter_map(f).reduce(|a, b| a + b)
    };
    let request_body = sum(|ex| {
        ex.request
            .as_ref()
            .and(ex.detail.get("request_body_bytes")?.as_u64())
            .map(|n| n as usize)
    });
    let response_body = sum(|ex| {
        ex.detail
            .get("response_body_bytes")?
            .as_u64()
            .map(|n| n as usize)
    });
    st.mark("recorded");
    if let Some(marks) = st.marks.take() {
        st.detail.insert("cpu_marks".into(), marks.value());
    }
    st.detail.insert(
        "process_cpu_seconds".into(),
        json!((cpu_seconds() * 1000.0).round() / 1000.0),
    );
    if args.is_sequence() {
        st.detail.insert("inference_calls".into(), json!({
            "witnessed_attempts": st.exchanges.iter().filter(|ex| ex.sent_at.is_some()).count(),
            "dead_check_attempts": st.detail["credential_sequence"]["dead_checks"].as_array().map_or(0, Vec::len),
            "live_check_attempts": usize::from(st.detail["credential_sequence"].get("live_check").is_some()),
            "basis": "attempts counted before sending; cancelled/transport-failed attempts count conservatively",
        }));
        for ex in &mut st.exchanges {
            ex.detail.insert(
                "credential_status".into(),
                st.detail["credential_sequence"]["credential_status"].clone(),
            );
            if result.is_err() && ex.error.is_none() {
                ex.error = error.clone();
            }
        }
    }
    let exchanges = std::mem::take(&mut st.exchanges)
        .into_iter()
        .map(|ex| ex.record(result.is_ok(), sent))
        .collect();
    let record = RunRecord {
        role: "prover",
        job_id,
        phase: phase_of(&args.out_dir),
        label: args.label.clone(),
        mode: Some(args.mode.as_str()),
        prewarm: args.prewarm.is_some(),
        stream: args.stream,
        host: st.host,
        limits: Some(Limits {
            max_sent: args.max_sent,
            max_recv: args.max_recv,
        }),
        timings_ms: st.timings,
        bytes: Bytes {
            to_verifier: st.counters.written(),
            from_verifier: st.counters.read(),
            request_body,
            response_body,
        },
        resources: Resources {
            peak_rss_mb: peak_rss_mb(),
            cpu_seconds: ((cpu_seconds() - cpu_start) * 1000.0).round() / 1000.0,
        },
        outcome,
        error: error.clone(),
        upstream_called,
        rtt_to_verifier_ms: st.rtt_ms,
        started_at,
        recorded_at: now_ms_rfc3339(),
        exchanges,
        detail: Value::Object(st.detail),
    };
    write_json(&record_path, &record)?;

    println!("outcome: {outcome}");
    if let Some(e) = &error {
        println!("error:   {e}");
    }
    println!("record:  {}", record_path.display());
    Ok((result.is_ok(), last, st.safe_retry))
}

/// Reads the n-th seal and request file, refuses a mismatch, and builds the
/// request bytes with the key, which is read here, immediately before use.
/// The exchange is added to the session whether or not it is refused.
fn prepare(args: &ProverArgs, run_id: &str, st: &mut State, n: usize) -> Result<()> {
    st.exchanges.push(Exchange::new(n));
    let result = prepare_exchange(args, run_id, st, n);
    if let Err(e) = &result {
        st.exchanges[n - 1].error = Some(describe(e));
    }
    result
}

fn prepare_exchange(args: &ProverArgs, run_id: &str, st: &mut State, n: usize) -> Result<()> {
    let (seal_path, request_path) = (nth(&args.seal, n), nth(&args.request, n));
    let ex = &mut st.exchanges[n - 1];
    ex.detail.insert("seal_file".into(), json!(seal_path));
    ex.detail.insert("request_file".into(), json!(request_path));
    let (req, job_id) = if let Some(call) = &st.router {
        (call.request.clone(), call.id.clone())
    } else {
        let (seal, _) = seal::load(&seal_path)?;
        seal::check_job_id(&seal.job_id)?;
        ex.detail.insert("seal_nonce".into(), json!(seal.nonce));
        let req = seal::read_request(&request_path)?;
        let mismatched = seal::mismatches(&seal, &req);
        if !mismatched.is_empty() {
            bail!("request does not match seal: {}", mismatched.join(", "));
        }
        (req, seal.job_id)
    };
    ex.job_id = Some(job_id.clone());
    if args.stream
        && serde_json::from_slice::<Value>(req.body_bytes())
            .ok()
            .map(|b| b["stream"] == json!(true))
            != Some(true)
    {
        bail!("--stream needs a JSON request body with \"stream\": true; nothing was sent");
    }
    let body_sha256 = sha256_hex(req.body_bytes());
    ex.detail
        .insert("request_body_bytes".into(), json!(req.body_bytes().len()));
    ex.detail
        .insert("request_body_sha256".into(), json!(body_sha256));
    match (&args.prewarm, &st.host) {
        (Some(host), _) if *host != req.host => {
            bail!(
                "the session was pre-warmed for {host}, but the request is for {}; nothing was sent",
                req.host
            )
        }
        (None, Some(host)) if *host != req.host => {
            bail!(
                "the session is with {host}, but the request is for {}; nothing was sent",
                req.host
            )
        }
        _ => {}
    }

    let api_key = if args.is_sequence() {
        st.temporary_credential.clone().ok_or_else(|| anyhow!("no temporary credential obtained"))?
    } else {
        args.profile.credential()?
    };
    let keep_alive = n < args.batch_max;
    let request = http::build_request(&req, &api_key, &job_id, keep_alive, args.credential_header)?;
    drop(api_key);
    let withheld: usize = st
        .exchanges
        .iter()
        .filter_map(|ex| ex.request.as_ref())
        .map(|r| r.auth_value.len())
        .sum::<usize>()
        + request.auth_value.len();
    if args.profile == Profile::CredentialHidden && withheld > zk::max_value_len() {
        bail!(
            "the credential header values come to {withheld} bytes; the no-CR/LF proof takes at most {}; nothing was sent",
            zk::max_value_len()
        );
    }
    if st.sent + request.bytes.len() > args.max_sent {
        bail!(
            "the session's requests come to {} bytes with this one, over --max-sent {}; nothing was sent",
            st.sent + request.bytes.len(),
            args.max_sent
        );
    }
    if n == 1 {
        if args.is_sequence() {
            let route = args
                .dead_check_request
                .as_ref()
                .map(|p| crate::management::load(p))
                .transpose()?;
            st.dead_template = Some(crate::management::dead_template(&req, route)?);
        }
        st.stem = format!("{job_id}.{run_id}");
        st.host = Some(req.host.clone());
    }
    let ex = &mut st.exchanges[n - 1];
    ex.detail
        .insert("request_bytes".into(), json!(request.bytes.len()));
    ex.detail.insert("keep_alive".into(), json!(keep_alive));
    ex.body_sha256 = Some(body_sha256);
    ex.request = Some(request);
    Ok(())
}

/// Polls for the request file. Returns when it was first seen.
async fn arrival(path: &std::path::Path) -> std::io::Result<Instant> {
    loop {
        if tokio::fs::try_exists(path).await? {
            return Ok(Instant::now());
        }
        tokio::time::sleep(Duration::from_millis(1)).await;
    }
}

/// When a file was put in place, as an `Instant`: its status-change time,
/// which renaming it into place sets.
fn placed_at(path: &std::path::Path) -> std::io::Result<Instant> {
    use std::os::unix::fs::MetadataExt as _;
    let meta = fs::metadata(path)?;
    let placed = std::time::UNIX_EPOCH
        + Duration::new(meta.ctime().max(0) as u64, meta.ctime_nsec().max(0) as u32);
    let ago = std::time::SystemTime::now()
        .duration_since(placed)
        .unwrap_or_default();
    Ok(Instant::now().checked_sub(ago).unwrap_or_else(Instant::now))
}

/// A committed session, before it connects to the server.
enum Commit {
    Mpc(Prover<CommitAccepted<tlsn::Mpc>>),
    Proxy(Prover<CommitAccepted<tlsn::Proxy>>),
}

async fn obtain(args: &ProverArgs, st: &mut State, loaded: &mut Loaded) -> Result<()> {
    let spec = args
        .ca_cert
        .as_ref()
        .map_or("webpki".into(), |p| p.display().to_string());
    let (roots, _) = loaded.roots(&spec).await?;
    st.mark("management_ready");
    st.detail.insert("credential_sequence".into(), json!({
            "credential_status": "not_obtained", "obtain_status": null, "revoke_status": null,
            "connection_closed_at": null, "revoke_response_received_at": null, "reveal_started_at": null,
            "obtain_ms": null, "revoke_ms": null, "dead_checks": [],
            "obtained_at": null, "provider_hash": null, "propagation_delay_ms": null,
            "dead_check_timeout_seconds": args.dead_check_timeout,
        }));
    let template = crate::management::load(
        args.obtain_request
            .as_ref()
            .expect("clap requires template"),
    )?;
    let t = Instant::now();
    let (status, fields) = crate::management::request(
        &template,
        &roots,
        &Value::Null,
        template.credential_field.is_some() || template.requires_byok_confirmation(),
        &st.session_name,
        Duration::from_secs(args.management_timeout),
    )
    .await
    .context("obtain failed; no witnessed call started")?;
    st.detail["credential_sequence"]["obtain_ms"] = json!(ms(t));
    st.detail["credential_sequence"]["obtain_status"] = json!(status);
    if !(200..300).contains(&status) {
        bail!("obtain returned non-2xx status {status}; no witnessed call started");
    }
    // Retain identifiers before extracting the credential: even a malformed
    // successful obtain must attempt cleanup when its hash is available.
    st.obtained = fields;
    st.cleanup_pending = true;
    st.detail["credential_sequence"]["obtained_at"] = json!(stamp());
    st.detail["credential_sequence"]["provider_hash"] = st
        .obtained
        .pointer("/data/hash")
        .and_then(Value::as_str)
        .map_or(Value::Null, |hash| json!(hash));
    if let Some(call) = &st.router {
        let hash = st
            .obtained
            .pointer("/data/hash")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("router obtain requires a provider hash for crash cleanup"))?;
        call.obtained(hash).await?;
    }
    if template.requires_byok_confirmation() {
        let mut confirmed = st
            .obtained
            .pointer("/data/include_byok_in_limit")
            .and_then(Value::as_bool)
            == Some(true);
        let mut limit_confirmed = template.confirms_limit(&st.obtained);
        st.detail["credential_sequence"]["include_byok_in_limit_create_confirmed"] =
            json!(confirmed);
        let missing_byok = st.obtained.pointer("/data/include_byok_in_limit").is_none();
        let missing_limit = st.obtained.pointer("/data/limit").is_none();
        if (missing_byok || missing_limit)
            && (missing_byok || confirmed)
            && (missing_limit || limit_confirmed)
        {
            let result = async {
                let readback = template.key_readback(&st.obtained)?;
                crate::management::request(
                    &readback,
                    &roots,
                    &st.obtained,
                    true,
                    &st.session_name,
                    Duration::from_secs(args.management_timeout),
                )
                .await
            }
            .await;
            // One GET only. Errors and non-2xx fail closed and trigger cleanup.
            (confirmed, limit_confirmed) = match result {
                Ok((status, fields)) if (200..300).contains(&status) => (
                    fields
                        .pointer("/data/include_byok_in_limit")
                        .and_then(Value::as_bool)
                        == Some(true),
                    template.confirms_limit(&fields),
                ),
                _ => (false, false),
            };
            st.detail["credential_sequence"]["include_byok_in_limit_readback_confirmed"] =
                json!(confirmed);
        }
        st.detail["credential_sequence"]["include_byok_in_limit_confirmed"] = json!(confirmed);
        st.detail["credential_sequence"]["limit_confirmed"] = json!(limit_confirmed);
        if !confirmed || !limit_confirmed {
            cleanup(args, st, loaded).await;
            bail!(
                "obtain did not confirm a bounded key limit including BYOK; session refused before use"
            );
        }
    }
    st.temporary_credential = Some(match &template.credential_field {
        Some(field) => st
            .obtained
            .pointer(field)
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("obtain credential field missing"))?
            .to_owned(),
        None => hex::encode(random_bytes::<36>()?),
    });
    st.detail["credential_sequence"]["credential_source"] =
        json!(if template.credential_field.is_some() {
            "obtain_response"
        } else {
            "locally_generated"
        });
    st.detail["credential_sequence"]["credential_status"] = json!("obtained");
    st.mark("obtained");
    Ok(())
}

async fn witness(
    args: &ProverArgs,
    run_id: &str,
    st: &mut State,
    loaded: &mut Loaded,
) -> Result<()> {
    if args.decrypt_online && !matches!(args.mode, Mode::Mpc) {
        bail!("--decrypt-online applies to MPC mode only; nothing was sent");
    }
    if args.batch_max == 0 {
        bail!("--batch-max must be at least 1; nothing was sent");
    }
    if args.batch_max > 1 {
        let numbered = |p: &std::path::Path| p.to_string_lossy().contains("{n}");
        if args.prewarm.is_none() || !matches!(args.mode, Mode::Proxy) || args.stream {
            bail!(
                "--batch-max above 1 needs --prewarm and proxy mode, without --stream; nothing was sent"
            );
        }
        if !numbered(&args.request) || !numbered(&args.seal) {
            bail!("--batch-max above 1 needs {{n}} in --request and --seal; nothing was sent");
        }
    }
    // Router requests already have a public statement; do not mint a credential
    // until a witness has accepted the commit. Proxy upstream dialing is lazy.
    let deferred_credential = st.router.is_some() && args.is_sequence();
    if deferred_credential {
        st.host = st.router.as_ref().map(|call| call.request.host.clone());
        st.detail.insert(
            "credential_sequence".into(),
            json!({"credential_status":"not_obtained", "dead_checks":[]}),
        );
    }
    if args.is_sequence() && !deferred_credential {
        obtain(args, st, loaded).await?;
    }
    // Cold, the first request is prepared first; pre-warmed, only once its
    // file arrives after the commit.
    if args.prewarm.is_none() && !deferred_credential {
        prepare(args, run_id, st, 1)?;
    }
    let host = match (&st.host, &args.prewarm) {
        (_, Some(host)) => host.clone(),
        (Some(host), None) => host.clone(),
        (None, None) => unreachable!("prepared when not pre-warming"),
    };
    st.host = Some(host.clone());
    st.mark("setup_started");

    // The no-CR/LF circuit is sized for every request the session may carry,
    // using the selected header value length.
    let server_name = DnsName::try_from(host.as_str())
        .map_err(|e| anyhow!("host {host:?} is not a DNS name: {e}"))?;
    let circuit = if args.profile == Profile::CredentialHidden {
        let key_len = args.profile.credential()?.len();
        let def = zk::select_circuit(args.batch_max * (args.credential_header.prefix().len() + key_len)).await
            .map_err(|e| e.context(format!("--batch-max {}; nothing was sent", args.batch_max)))?;
        Some(loaded.circuit(&args.srs, def).await?)
    } else {
        None
    };
    st.detail.insert("cgroup_caps".into(), crate::record::cgroup_caps());
    st.detail.insert(
        "profile".into(),
        json!(args.profile),
    );
    let roots = args
        .ca_cert
        .as_ref()
        .map_or("webpki".into(), |p| p.display().to_string());
    let (roots, roots_about) = loaded.roots(&roots).await?;
    st.detail.insert("roots".into(), roots_about);
    // Hand freed heap back to the system before waiting for a request: the
    // setup's working memory on a first session, the previous session's
    // proofs on a later one. malloc_trim is glibc's.
    #[cfg(all(target_os = "linux", target_env = "gnu"))]
    unsafe {
        libc::malloc_trim(0)
    };
    st.mark("ready");
    let tls_config = TlsClientConfig::builder()
        .server_name(ServerName::Dns(server_name.clone()))
        .root_store(roots)
        .build()?;

    let t = Instant::now();
    let tcp = match TcpStream::connect(&args.verifier).await {
        Ok(tcp) => tcp,
        Err(e) => {
            st.safe_retry = true;
            return Err(e).context("witness TCP connect failed");
        }
    };
    st.rtt_ms = Some(ms(t));
    tcp.set_nodelay(true)?;
    let (mut socket, counters) = Counting::new(tcp);
    st.counters = counters;
    write_frame(&mut socket, args.profile.as_str().as_bytes()).await?;
    let accepted = read_frame(&mut socket, 256).await?;
    if let Some(reason) = accepted.strip_prefix(b"refused: ") {
        st.safe_retry = true;
        bail!("witness refused before commit: {}", String::from_utf8_lossy(reason));
    }
    if accepted != args.profile.as_str().as_bytes() {
        bail!("profile mismatch: verifier refused requested profile");
    }
    st.witness_session_id = String::from_utf8(read_frame(&mut socket, 256).await?)?;
    let statement = match &st.router {
        Some(call) => call.statement(&st.witness_session_id)?,
        None => Value::Null,
    };
    if !statement.is_null() {
        st.detail
            .insert("operator_statement".into(), statement.clone());
    }
    write_frame(&mut socket, &serde_json::to_vec(&statement)?).await?;
    write_frame(&mut socket, host.as_bytes()).await?;
    let accepted = read_frame(&mut socket, 16384).await?;
    if let Some(reason) = accepted.strip_prefix(b"refused: ") {
        st.safe_retry = true;
        bail!("witness refused before commit: {}", String::from_utf8_lossy(reason));
    }
    if accepted != b"accepted" {
        bail!("unexpected witness admission reply");
    }
    let session = crate::io::with_cpus(args.tlsn_threads, || Session::new(socket.compat()))?;
    let (driver, mut handle) = session.split();
    let mut driver = AbortOnDrop(tokio::spawn(driver));
    let prover = handle.new_prover(ProverConfig::builder().build()?)?;

    let t = Instant::now();
    let commit = match args.mode {
        Mode::Mpc => {
            let mut caps = MpcTlsConfig::builder()
                .max_sent_data(args.max_sent)
                .max_recv_data(args.max_recv);
            if args.decrypt_online {
                caps = caps
                    .defer_decryption_from_start(false)
                    .max_recv_data_online(args.max_recv);
                if let Some(n) = args.recv_records_online {
                    caps = caps.max_recv_records_online(n);
                }
            }
            let caps = caps.build()?;
            st.detail.insert(
                "mpc_config".into(),
                json!({
                    "max_recv_data_online": caps.max_recv_data_online(),
                    "max_recv_records_online": caps.max_recv_records_online(),
                    "defer_decryption_from_start": caps.defer_decryption_from_start(),
                }),
            );
            Commit::Mpc(
                step(
                    "commit (MPC preprocessing)",
                    prover.commit(caps),
                    &mut driver,
                )
                .await?,
            )
        }
        Mode::Proxy => {
            let config = ProxyTlsConfig::builder().server_name(server_name).build()?;
            let accepted = step("commit (proxy setup)", prover.commit(config), &mut driver).await;
            if let Err(e) = &accepted {
                st.safe_retry = e
                    .chain()
                    .filter_map(|c| c.downcast_ref::<tlsn::Error>())
                    .any(|e| {
                        e.is_user() && e.msg() == Some("commitment protocol rejected by verifier")
                    });
            }
            Commit::Proxy(accepted?)
        }
    };
    st.timings.prewarm = Some(ms(t));
    let committed_at = Instant::now();
    st.mark("committed");

    if deferred_credential {
        obtain(args, st, loaded).await?;
        prepare(args, run_id, st, 1)?;
    }

    let user_start = match &args.prewarm {
        None => Instant::now(),
        Some(_) => {
            let first = nth(&args.request, 1);
            println!("prewarmed: waiting for {}", first.display());
            let ready = Instant::now();
            st.waiting = true;
            let arrived =
                step("waiting for the request file", arrival(&first), &mut driver).await?;
            st.waiting = false;
            st.mark("request_arrived");
            let waited = arrived.duration_since(ready).as_secs_f64() * 1000.0;
            st.detail.insert(
                "prewarm_wait_ms".into(),
                json!((waited * 10.0).round() / 10.0),
            );
            prepare(args, run_id, st, 1)?;
            arrived
        }
    };
    st.exchanges[0].arrived = Some(user_start);
    if args.live_check {
        let (roots, _) = loaded.roots(
            &args
                .ca_cert
                .as_ref()
                .map_or("webpki".into(), |p| p.display().to_string()),
        ).await?;
        st.detail["credential_sequence"]["live_check"] = json!({"started_at":stamp()});
        let t = Instant::now();
        let (status, cost, code, completion, generation_id) = crate::management::dead_check(
            st.dead_template.as_ref().expect("prepared"),
            &roots,
            st.temporary_credential.as_deref().expect("obtained"),
            Duration::from_secs(args.management_timeout),
        )
        .await?;
        st.detail["credential_sequence"]["live_check"] = json!({
            "started_at":st.detail["credential_sequence"]["live_check"]["started_at"],
            "response_received_at":stamp(),"ms":ms(t),"status":status,
            "provider_cost_usd":cost,"provider_error_code":code,"completion":completion,
            "generation_id":generation_id});
        if !(200..300).contains(&status) || !completion {
            bail!("live dead-check control did not return a 2xx completion");
        }
    }

    // The prover future is polled here rather than spawned, and is declared
    // after `handle`, so on any early return it is dropped before the handle
    // shuts down mpz's executor. A spawned future is only asked to stop, and
    // can still be running when the executor goes; it then polls a cancelled
    // mpz task, which panics inside mpz.
    let (mut tls, mut prover_fut): (_, ProverFut) = match commit {
        Commit::Mpc(prover) => {
            // No server connection is opened for a witness already gone.
            if driver.0.is_finished() {
                return Err(
                    session_ended((&mut driver).await).context("before connecting to the server")
                );
            }
            let (server, mut upstream) = connect_upstream(&host, &args.resolve, "prover").await?;
            upstream["opened_after_commit_ms"] = json!(ms(committed_at));
            st.detail.insert("upstream".into(), upstream);
            st.dialed = true;
            let (server, records) = RecordTap::new(server);
            st.app_data = Some(records);
            let (server, tap) = HelloTap::new(server);
            st.hello = Some(tap);
            let (tls, prover) = prover.connect(tls_config, server.compat())?;
            (tls, Box::pin(prover.into_future()))
        }
        Commit::Proxy(prover) => {
            let (tls, prover) = prover.connect(tls_config)?;
            (tls, Box::pin(prover.into_future()))
        }
    };
    st.tls_started = true;
    if args.stream {
        let path = args.out_dir.join(format!("{}.response.bin", st.stem));
        st.live = Some(Live::new(&path, user_start)?);
    }

    let mut received = Vec::new();
    let mut committed = None;
    // The TLS stream does not end when tlsn fails (for example on its own
    // max_recv cap), so the conversation races the prover future and the
    // session. At tlsn alpha.15 the prover future is not woken again after
    // the TLS client refuses plaintext because its send buffer is full, so a
    // request of more than about 24 KB stalls until a network event arrives;
    // the server, waiting for the rest of the body, sends none. The tick
    // polls it again.
    let mut tick = tokio::time::interval(Duration::from_millis(1));
    tick.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
    // If the session or tlsn fails, plaintext already decrypted is still read
    // for a short while, so a response that arrived is not lost with it.
    let mut prover_err = None;
    let mut driver_end = None;
    let drain = tokio::time::sleep(Duration::from_secs(86400));
    let mut drain = std::pin::pin!(drain);
    let conversed = {
        let mut converse = std::pin::pin!(converse(args, run_id, st, &mut tls, &mut received));
        loop {
            let failed = prover_err.is_some() || driver_end.is_some();
            tokio::select! {
                biased;
                done = &mut prover_fut, if committed.is_none() && prover_err.is_none() => match done {
                    Ok(prover) => committed = Some(prover),
                    Err(e) => {
                        prover_err = Some(e);
                        if !failed {
                            drain.as_mut().reset(tokio::time::Instant::now() + DRAIN);
                        }
                    }
                },
                result = &mut converse => break Some(result),
                end = &mut driver, if driver_end.is_none() => {
                    driver_end = Some(end);
                    if !failed {
                        drain.as_mut().reset(tokio::time::Instant::now() + DRAIN);
                    }
                }
                _ = &mut drain, if failed => break None,
                _ = tick.tick() => {}
            }
        }
    };
    let closed_at = Instant::now();
    let closed_stamp = chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Micros, true);
    if let (Some((when, cpu)), Some(marks)) = (proxy_handshake(), st.marks.as_mut()) {
        marks.mark_at("handshake", when, cpu);
    }
    st.mark("connection_closed");
    drop(tls);
    st.received = received.len();
    if let Some(live) = st.live.as_mut() {
        live.closed = Some(ms(live.start));
    }
    let ended = match (prover_err, driver_end) {
        (Some(e), _) => Some(anyhow::Error::new(e).context("witnessed TLS session failed")),
        (None, Some(end)) => Some(session_ended(end)),
        (None, None) => None,
    };
    let delivered = st
        .exchanges
        .iter()
        .filter(|ex| ex.response.is_some())
        .count();
    match (conversed, ended) {
        (Some(Ok(())), None) => {}
        (Some(Ok(())), Some(cause)) => {
            return Err(cause.context(format!(
                "{delivered} response(s) delivered, but the witness session ended"
            )));
        }
        (None, Some(cause)) => {
            return Err(cause.context(format!(
                "{delivered} response(s) delivered; the connection had not finished after {} bytes received",
                received.len()
            )));
        }
        (Some(Err(e)), Some(cause)) => return Err(cause.context(describe(&e))),
        (Some(Err(e)), None) if committed.is_none() => {
            // The connection ended early; tlsn's own error says why.
            let what = format!("witnessed connection ended early ({})", describe(&e));
            return Err(
                match tokio::time::timeout(
                    Duration::from_secs(10),
                    step(&what, prover_fut, &mut driver),
                )
                .await
                {
                    Ok(Err(cause)) => cause,
                    _ => e,
                },
            );
        }
        (Some(Err(e)), None) => return Err(e),
        (None, None) => unreachable!("the drain runs only after a failure"),
    }

    // converse returned successfully only after observing EOF on the
    // witnessed TLS stream. No prove future has been created or polled.
    if args.is_sequence() {
        st.detail["credential_sequence"]["connection_closed_at"] = json!(closed_stamp);
        st.detail["credential_sequence"]["credential_status"] = json!("revocation_pending");
        let t = Instant::now();
        let revoke = async {
            let template = crate::management::load(
                args.revoke_request
                    .as_ref()
                    .expect("clap requires template"),
            )?;
            let spec = args
                .ca_cert
                .as_ref()
                .map_or("webpki".into(), |p| p.display().to_string());
            let (roots, _) = loaded.roots(&spec).await?;
            crate::management::request(
                &template,
                &roots,
                &st.obtained,
                false,
                &st.session_name,
                Duration::from_secs(args.management_timeout),
            )
            .await
        }
        .await;
        st.detail["credential_sequence"]["revoke_ms"] = json!(ms(t));
        st.mark("revoke_finished");
        let cause = match revoke {
            Ok((status, _)) => {
                st.detail["credential_sequence"]["revoke_status"] = json!(status);
                st.detail["credential_sequence"]["revoke_response_received_at"] =
                    json!(chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Micros, true));
                if (200..300).contains(&status) {
                    None
                } else {
                    Some(format!("revoke returned non-2xx status {status}"))
                }
            }
            Err(e) => Some(format!("revoke failed: {}", describe(&e))),
        };
        if let Some(cause) = cause {
            st.detail["credential_sequence"]["credential_status"] = json!("revocation_failed");
            st.detail["credential_sequence"]["failure"] = json!(cause);
            st.detail["credential_sequence"]["witness_session_end"] =
                json!("prover drops the unproved session and closes its witness transport");
            // Drop the prover/handle and AbortOnDrop driver. The witness sees
            // transport termination; it cannot know whether revocation occurred.
            bail!("{cause}; reveal suppressed; ending witness session");
        }
        st.cleanup_pending = false;
        st.detail["credential_sequence"]["credential_status"] = json!("revoke_accepted");
        let revoked_at = Instant::now();
        if let Err(e) = check_dead(args, st, loaded, revoked_at).await {
            // Retry retirement on any ambiguous probe failure, after the
            // unproved witness session has been dropped by the caller.
            st.cleanup_pending = true;
            st.detail["credential_sequence"]["credential_status"] = json!("death_unconfirmed");
            st.detail["credential_sequence"]["failure"] = json!(describe(&e));
            st.detail["credential_sequence"]["witness_session_end"] =
                json!("prover drops the unproved session and closes its witness transport");
            return Err(e.context("dead-check failed; reveal suppressed; ending witness session"));
        }
        st.detail["credential_sequence"]["credential_status"] = json!("dead_confirmed");
    }

    // Every sent request, in order; the rest were not sent.
    let sent: Vec<&Exchange> = st
        .exchanges
        .iter()
        .filter(|ex| ex.sent_at.is_some())
        .collect();
    if sent.iter().any(|ex| ex.response.is_none()) {
        bail!("a request sent on the connection was not answered before it closed");
    }
    let withheld: Vec<std::ops::Range<usize>> =
        sent.iter().filter_map(|ex| ex.withheld()).collect();
    let sent_bytes: Vec<u8> = sent
        .iter()
        .flat_map(|ex| ex.request.as_ref().map_or(&[][..], |r| &r.bytes))
        .copied()
        .collect();

    let mut prover = match committed {
        Some(prover) => prover,
        None => step("witnessed TLS session", prover_fut, &mut driver).await?,
    };
    if prover.transcript().sent() != sent_bytes.as_slice()
        || prover.transcript().received() != received.as_slice()
    {
        bail!("tlsn transcript differs from the bytes this prover exchanged");
    }
    if let Some(marks) = st.marks.as_mut() {
        marks.mark("plaintext_auth_started");
    }
    let config = {
        let hidden = RangeSet::from(withheld.clone());
        let mut shown = RangeSet::from(0..sent_bytes.len());
        if args.profile == Profile::CredentialHidden {
            shown.difference_mut(&hidden);
        }
        let mut builder = ProveConfig::builder(prover.transcript());
        builder.server_identity();
        builder.reveal_sent(&shown)?;
        builder.reveal_recv_all()?;
        st.detail.insert("disclosure".into(), json!({
            "sent_transcript_bytes": sent_bytes.len(),
            "received_transcript_bytes": received.len(),
            "sent_fully_revealed": args.profile != Profile::CredentialHidden,
            "received_fully_revealed": true,
            "withheld_hash_commitment": args.profile == Profile::CredentialHidden,
        }));
        // tlsn commits to the withheld values together as
        // SHA-256(value 1 || value 2 || ... || blinder).
        if args.profile == Profile::CredentialHidden {
            let mut commits = TranscriptCommitConfig::builder(prover.transcript());
            commits.default_kind(TranscriptCommitmentKind::Hash {
                alg: HashAlgId::SHA256,
            });
            commits.commit_sent(&hidden)?;
            builder.transcript_commit(commits.build()?);
        }
        builder.build()?
    };
    if args.is_sequence() {
        st.detail["credential_sequence"]["reveal_started_at"] =
            json!(chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Micros, true));
        st.detail["credential_sequence"]["close_to_reveal_ms"] = json!(ms(closed_at));
        if let Some(marks) = st.marks.as_mut() {
            marks.mark("reveal_started");
        }
    }
    let output = step(
        "proving to the verifier",
        prover.prove(&config),
        &mut driver,
    )
    .await?;
    step("closing prover", prover.close(), &mut driver).await?;
    // The verifier closes the session once it has checked the commitments.
    // Closing it from this side could end the verifier's session before then.
    let mut socket = tokio::time::timeout(Duration::from_secs(60), driver)
        .await
        .map_err(|_| anyhow!("the verifier did not close the session within 60 s"))?
        .context("session task")?
        .context("closing session")?
        .into_inner();
    // A field, not `st.mark`: `sent` borrows the exchanges.
    if let Some(marks) = st.marks.as_mut() {
        marks.mark("tlsn_proved");
    }
    // The no-CR/LF proof follows the session on the same connection.
    let circuit_sha = if let Some((circuit, circuit_about)) = circuit {
        let value_len: usize = withheld.iter().map(|r| r.len()).sum();
        let need = zk::select_circuit(value_len).await?;
        let (circuit, about) = if need.sha256 == circuit.def().sha256 {
            (circuit, circuit_about)
        } else {
            let (circuit, again) = loaded.circuit(&args.srs, need).await?;
            (circuit, json!({ "load": circuit_about, "reload": again }))
        };
        st.detail.insert("zk".into(), json!({ "load": about }));
        let proof =
            no_line_break_proof(circuit, output, &sent_bytes, &withheld, &mut st.detail).await?;
        write_frame(&mut socket, &proof)
            .await
            .context("sending the proof")?;
        Some(need.sha256.clone())
    } else {
        None
    };
    if let Some(marks) = st.marks.as_mut() {
        marks.mark("zk_proved");
    }
    let reply = read_frame(&mut socket, 1 << 20)
        .await
        .context("reading verdict")?;
    st.timings.prove = Some(ms(closed_at));
    if let Some(marks) = st.marks.as_mut() {
        marks.mark("verdict");
    }

    let reply_bytes = reply.len();
    let reply: Reply = serde_json::from_slice(&reply).context("parsing verifier reply")?;
    let verdict = match (reply.verdict, reply.error) {
        (Some(verdict), _) => verdict,
        (None, Some(e)) => bail!("verifier refused to issue a verdict: {e}"),
        (None, None) => bail!("verifier reply has neither a verdict nor an error"),
    };
    let verdict_path = args.out_dir.join(format!("{}.verdict.json", st.stem));
    write_json(&verdict_path, &verdict)?;
    st.detail.insert("verdict_file".into(), json!(verdict_path));

    verify_signature(&verdict, "verifier_pub").map_err(|e| anyhow!("verdict {e}"))?;
    let verdict_value = verdict.clone();
    let verdict: Verdict = serde_json::from_value(verdict).context("reading the verdict")?;
    let mut mismatched = Vec::new();
    if verdict.profile != args.profile {
        mismatched.push("profile".to_string());
    }
    if verdict.session_id != st.witness_session_id {
        mismatched.push("session_id".into());
    }
    if verdict.mode != args.mode.as_str() {
        mismatched.push("mode".to_string());
    }
    if verdict.server_name != host {
        mismatched.push("server_name".to_string());
    }
    let records = reply.records;
    if verdict.exchanges != sent.len() || records.len() != sent.len() {
        mismatched.push(format!(
            "{} exchanges and {} records for {} requests",
            verdict.exchanges,
            records.len(),
            sent.len()
        ));
    }
    let t = Instant::now();
    let leaves = records
        .iter()
        .map(ExchangeRecord::leaf)
        .collect::<Result<Vec<_>>>()?;
    if hex::encode(merkle::root(&leaves)) != verdict.root {
        mismatched.push("the records do not hash to the verdict's root".to_string());
    }
    let root_us = t.elapsed().as_secs_f64() * 1e6;
    for (i, (ex, got)) in sent.iter().zip(&records).enumerate() {
        let (response_sha, images) = ex.response.as_ref().expect("checked above");
        let withheld = circuit_sha.as_ref().and_then(|sha| {
            ex.withheld().map(|r| Withheld {
                header: args.credential_header.as_str().to_string(),
                start: r.start,
                end: r.end,
                no_cr_lf: sha.clone(),
            })
        });
        let checks = [
            ("n", got.n == i + 1),
            ("outcome", got.outcome == "verified"),
            ("job_id", Some(&got.job_id) == ex.job_id.as_ref()),
            (
                "request.body_sha256",
                Some(&got.request.body_sha256) == ex.body_sha256.as_ref(),
            ),
            ("request.withheld", got.request.withheld == withheld),
            (
                "response.body_sha256",
                got.response.body_sha256 == *response_sha,
            ),
            ("response.images", got.response.images == *images),
        ];
        mismatched.extend(
            checks
                .iter()
                .filter(|(_, ok)| !ok)
                .map(|(what, _)| format!("exchange {}: {what}", i + 1)),
        );
    }
    if !mismatched.is_empty() {
        bail!(
            "verdict does not match this session: {}",
            mismatched.join(", ")
        );
    }
    let places: Vec<usize> = sent.iter().map(|ex| ex.n - 1).collect();
    receipts(
        args,
        run_id,
        st,
        verdict_value,
        &places,
        records,
        &leaves,
        reply_bytes,
        root_us,
    )
}

/// One receipt per job: its own record and salt, its path to the session
/// root, and the signed verdict. Its siblings are hashes of salted records,
/// so they say nothing about the other jobs.
#[allow(clippy::too_many_arguments)]
fn receipts(
    args: &ProverArgs,
    run_id: &str,
    st: &mut State,
    verdict: Value,
    places: &[usize],
    records: Vec<ExchangeRecord>,
    leaves: &[merkle::Hash],
    reply_bytes: usize,
    root_us: f64,
) -> Result<()> {
    let mut sizes = Vec::new();
    let t = Instant::now();
    let paths = merkle::paths(leaves);
    let mut build_us = t.elapsed().as_secs_f64() * 1e6;
    for ((i, record), place) in records.into_iter().enumerate().zip(places) {
        let t = Instant::now();
        let path = paths[i].iter().map(hex::encode).collect();
        let receipt = Receipt {
            v: 1,
            path,
            record,
            verdict: verdict.clone(),
        };
        if let Some(call) = &st.router {
            call.verified(serde_json::to_value(&receipt)?);
        }
        let mut text = serde_json::to_string_pretty(&receipt)?;
        text.push('\n');
        build_us += t.elapsed().as_secs_f64() * 1e6;
        let file = args
            .out_dir
            .join(format!("{}.{run_id}.receipt.json", receipt.record.job_id));
        fs::write(&file, &text).with_context(|| format!("writing {}", file.display()))?;
        sizes.push(text.len());
        let ex = &mut st.exchanges[*place];
        ex.detail.insert("receipt_file".into(), json!(file));
        ex.detail.insert("receipt_bytes".into(), json!(text.len()));
    }
    let us = |x: f64| (x * 10.0).round() / 10.0;
    st.detail.insert(
        "receipts".into(),
        json!({
            "count": sizes.len(),
            "bytes": sizes,
            "reply_bytes": reply_bytes,
            "root_check_us": us(root_us),
            "build_us": us(build_us),
        }),
    );
    Ok(())
}

type ProverFut = Pin<Box<dyn Future<Output = tlsn::Result<Prover<Committed>>> + Send>>;

/// Proves that the values tlsn committed to, together, hold no CR or LF.
async fn no_line_break_proof(
    circuit: zk::Circuit,
    output: ProverOutput,
    sent: &[u8],
    withheld: &[std::ops::Range<usize>],
    detail: &mut Map<String, Value>,
) -> Result<Vec<u8>> {
    let commitment = output
        .transcript_commitments
        .iter()
        .find_map(|c| match c {
            TranscriptCommitment::Hash(h) if h.direction == Direction::Sent => Some(h),
            _ => None,
        })
        .ok_or_else(|| anyhow!("tlsn returned no commitment to the withheld values"))?;
    let secret = output
        .transcript_secrets
        .iter()
        .find_map(|s| match s {
            TranscriptSecret::Hash(h) if h.direction == Direction::Sent => Some(h),
            _ => None,
        })
        .ok_or_else(|| anyhow!("tlsn returned no blinder for the withheld values"))?;
    let range: Vec<std::ops::Range<usize>> = commitment.idx.iter().collect();
    if range != withheld {
        bail!("tlsn committed to {range:?}, not the withheld {withheld:?}");
    }
    let value: Vec<u8> = range
        .iter()
        .flat_map(|r| sent[r.clone()].to_vec())
        .collect();
    let blinder = secret.blinder.as_bytes().to_vec();
    let hash = commitment.hash.value.as_bytes().to_vec();
    if sha256_hex(&[value.as_slice(), &blinder].concat()) != hex::encode(&hash) {
        bail!("tlsn's commitment is not SHA-256(values || blinder)");
    }

    let t = Instant::now();
    let cpu = cpu_seconds();
    let proof = tokio::task::spawn_blocking(move || zk::prove(&circuit, &value, &blinder, &hash))
        .await
        .context("proving")??;
    if let Some(zk) = detail.get_mut("zk") {
        zk["commitment_ranges"] = json!(range);
        zk["prove_ms"] = json!(ms(t));
        zk["prove_cpu_s"] = json!(cpu_seconds() - cpu);
        zk["proof_bytes"] = json!(proof.len());
    }
    Ok(proof)
}

/// Why the session sends no more requests.
enum Last {
    /// The last request sent asked the server to close.
    Asked,
    /// The server closed the connection.
    ServerClosed,
    /// The window passed, or the next request was refused: the prover closes.
    Closing,
}

/// The conversation: sends each request as its file arrives, the next once
/// the previous response is complete, delivers each response as it
/// completes, then has the connection closed. tlsn's proxy client finishes
/// only once the server has closed.
async fn converse<S: AsyncRead + AsyncWrite + Unpin>(
    args: &ProverArgs,
    run_id: &str,
    st: &mut State,
    tls: &mut S,
    received: &mut Vec<u8>,
) -> Result<()> {
    let first = st.exchanges[0].arrived.expect("set before connecting");
    let deadline = args
        .batch_window_ms
        .map(|w| tokio::time::Instant::from_std(first) + Duration::from_millis(w));
    let mut buf = vec![0u8; 16384];
    let mut n = 1;
    let last = loop {
        if n > 1 {
            // Wait for the next file, the window's end, or the server closing.
            let path = nth(&args.request, n);
            let window = async {
                match deadline {
                    Some(at) => tokio::time::sleep_until(at).await,
                    None => std::future::pending().await,
                }
            };
            let read = tls.read(&mut buf);
            let seen = tokio::select! {
                seen = arrival(&path) => seen?,
                _ = window => break Last::Closing,
                got = read => {
                    let got = got?;
                    if got == 0 {
                        break Last::ServerClosed;
                    }
                    received.extend_from_slice(&buf[..got]);
                    bail!("the server sent {got} bytes without a request");
                }
            };
            let arrived = placed_at(&path).unwrap_or(seen).min(seen);
            if prepare(args, run_id, st, n).is_err() {
                break Last::Closing;
            }
            let ex = &mut st.exchanges[n - 1];
            ex.arrived = Some(arrived);
            ex.detail.insert(
                "arrived_ms".into(),
                json!(round(arrived.saturating_duration_since(first))),
            );
            ex.detail.insert(
                "seen_ms".into(),
                json!(round(seen.saturating_duration_since(first))),
            );
        }

        let ex = &mut st.exchanges[n - 1];
        let request = &ex.request.as_ref().expect("prepared").bytes;
        ex.sent_at = Some(st.sent);
        ex.detail
            .insert("inference_started_at".into(), json!(stamp()));
        tls.write_all(request).await?;
        tls.flush().await?;
        st.sent += request.len();
        ex.detail
            .insert("sent_range".into(), json!(ex.sent_at.unwrap()..st.sent));

        // Read until the response is complete by its framing, or the server
        // closes.
        let start = received.len();
        let (response, closed) = loop {
            match http::parse_response_at(&received[start..], false) {
                Ok((response, used)) if start + used == received.len() => break (response, false),
                Ok((_, used)) => bail!(
                    "{} unexpected bytes after response {n}",
                    received.len() - start - used
                ),
                Err(_) => {}
            }
            let got = tls.read(&mut buf).await?;
            if got == 0 {
                let response = http::parse_response_at(&received[start..], true)
                    .and_then(|(response, used)| match start + used == received.len() {
                        true => Ok(response),
                        false => bail!(
                            "{} unexpected bytes after the response",
                            received.len() - start - used
                        ),
                    })
                    .with_context(|| {
                        format!("the server closed before response {n} was complete")
                    })?;
                break (response, true);
            }
            received.extend_from_slice(&buf[..got]);
            st.received = received.len();
            if received.len() > args.max_recv {
                bail!("responses exceed --max-recv");
            }
            if let Some(call) = &st.router {
                call.stream_update(received).await?;
            }
            if let Some(live) = st.live.as_mut() {
                live.update(received)?;
            }
            if received.len() > args.max_recv {
                bail!(
                    "responses exceed --max-recv {}: aborted after {} bytes",
                    args.max_recv,
                    received.len()
                );
            }
        };
        deliver(args, run_id, st, n, response, start..received.len()).await?;
        if closed {
            break Last::ServerClosed;
        }
        if n == args.batch_max {
            break Last::Asked;
        }
        n += 1;
    };
    st.detail.insert(
        "connection_end".into(),
        json!(match last {
            Last::Asked => "the last request asked the server to close",
            Last::ServerClosed => "the server closed",
            Last::Closing => "this prover closed: no further request was sent",
        }),
    );
    if matches!(last, Last::Closing) {
        tls.close().await?;
    }
    // tlsn's proxy client finishes once the server has closed.
    if !matches!(last, Last::ServerClosed) {
        let got = tls.read(&mut buf).await?;
        if got > 0 {
            received.extend_from_slice(&buf[..got]);
            bail!("the server sent {got} bytes after the last response");
        }
    }
    Ok(())
}

fn round(d: Duration) -> f64 {
    (d.as_secs_f64() * 1e4).round() / 10.0
}

/// Writes the n-th response body, and any inline images, to disk.
async fn deliver(
    args: &ProverArgs,
    run_id: &str,
    st: &mut State,
    n: usize,
    response: http::ParsedResponse,
    recv_range: std::ops::Range<usize>,
) -> Result<()> {
    if let Some(call) = &st.router {
        call.deliver(response.clone()).await;
    }
    let ex = &mut st.exchanges[n - 1];
    let stem = format!("{}.{run_id}", ex.job_id.as_deref().expect("prepared"));
    let response_path = args.out_dir.join(format!("{stem}.response.bin"));
    let streamed = st
        .live
        .as_ref()
        .map(|live| live.written == response.body.len());
    // A streamed file holds the body already, unless its framing was read
    // differently as it arrived; the parsed body is then written over it.
    let kept = streamed == Some(true)
        && sha256_hex(&fs::read(&response_path)?) == sha256_hex(&response.body);
    if !kept {
        fs::write(&response_path, &response.body)
            .with_context(|| format!("writing {}", response_path.display()))?;
        if streamed.is_some() {
            ex.detail
                .insert("stream_file_rewritten".into(), json!(true));
        }
    }
    let images = http::inline_images(&response.body).context("decoding inline images")?;
    let mut image_files = Vec::new();
    for (i, image) in images.iter().enumerate() {
        let ext = image
            .media_type
            .strip_prefix("image/")
            .filter(|e| e.bytes().all(|b| b.is_ascii_alphanumeric()));
        let path = args
            .out_dir
            .join(format!("{stem}.image-{i}.{}", ext.unwrap_or("bin")));
        fs::write(&path, &image.bytes).with_context(|| format!("writing {}", path.display()))?;
        image_files.push(
            json!({ "file": path, "media_type": image.media_type, "bytes": image.bytes.len() }),
        );
    }
    let arrived = ex.arrived.expect("set before sending");
    // A streamed body was fully on disk at its last write.
    let user = match st.live.as_ref().and_then(|live| live.last_write) {
        Some(at) if kept => at,
        _ => ms(arrived),
    };
    if n == 1 {
        st.timings.user = Some(user);
    }
    if !image_files.is_empty() {
        ex.detail.insert("images".into(), json!(image_files));
    }
    let response_sha256 = sha256_hex(&response.body);
    ex.detail.insert("recv_range".into(), json!(recv_range));
    ex.detail.insert("user_ms".into(), json!(user));
    ex.detail
        .insert("response_file".into(), json!(response_path));
    ex.detail
        .insert("response_body_sha256".into(), json!(response_sha256));
    ex.detail
        .insert("response_body_bytes".into(), json!(response.body.len()));
    ex.detail
        .insert("response_status".into(), json!(response.status));
    ex.detail
        .insert("response_received_at".into(), json!(stamp()));
    // Provider usage is inference data, never a management response. Preserve
    // its reported cost so the call/spend account can be reconciled offline.
    if let Ok(body) = serde_json::from_slice::<Value>(&response.body) {
        ex.detail.insert(
            "provider_cost_usd".into(),
            body.pointer("/usage/cost").cloned().unwrap_or(Value::Null),
        );
        ex.detail.insert(
            "completion_present".into(),
            json!(
                body.get("choices")
                    .and_then(Value::as_array)
                    .is_some_and(|c| !c.is_empty())
            ),
        );
    }
    ex.response = Some((
        response_sha256,
        images.iter().map(VerdictImage::of).collect(),
    ));
    Ok(())
}

/// Router sessions use the same commit, TLS, revoke-before-reveal and receipt path.
pub async fn router_session(
    args: &ProverArgs,
    call: std::sync::Arc<crate::router::Call>,
) -> Result<bool> {
    static SETUP: std::sync::OnceLock<Loaded> = std::sync::OnceLock::new();
    let mut loaded = SETUP.get_or_init(Loaded::default).clone();
    let (_, _, safe_retry) =
        session(args, 1, Instant::now(), &mut loaded, Some(call)).await?;
    Ok(safe_retry)
}

/// Recovery can disable and read back a journaled hash without persisting a key.
/// Authentication refusal cannot be reprobed after a crash because the secret
/// lived only in memory; report that distinction explicitly.
pub async fn router_recover(args: &ProverArgs, credential: &Value) -> Result<Value> {
    let hash = credential["provider_hash"]
        .as_str()
        .ok_or_else(|| anyhow!("missing recovery hash"))?;
    let mut st = State {
        obtained: json!({"data":{"hash":hash}}),
        cleanup_pending: true,
        ..State::default()
    };
    st.detail.insert("credential_sequence".into(), json!({}));
    let mut loaded = Loaded::default();
    cleanup(args, &mut st, &mut loaded).await;
    let template = crate::management::load(args.obtain_request.as_ref().unwrap())?
        .key_readback(&st.obtained)?;
    let spec = args
        .ca_cert
        .as_ref()
        .map_or("webpki".into(), |p| p.display().to_string());
    let (roots, _) = loaded.roots(&spec).await?;
    let confirmed = match crate::management::request(
        &template,
        &roots,
        &st.obtained,
        true,
        "",
        Duration::from_secs(10),
    )
    .await
    {
        Ok((200, value)) => value.pointer("/data/disabled").and_then(Value::as_bool) == Some(true),
        _ => false,
    };
    Ok(
        json!({"state":if confirmed {"disabled_confirmed"} else {"cleanup_failed"},
        "disabled_confirmed":confirmed,"death_confirmation":"unavailable after restart; credential was memory only",
        "disable_accepted":st.detail["credential_sequence"]["cleanup"]["succeeded"] == true
                || st.detail["credential_sequence"]["credential_status"] == "dead_confirmed"}),
    )
}

/// Exactly one ordinary HTTPS attempt after all witnesses positively declined.
pub async fn router_direct(
    args: &ProverArgs,
    call: std::sync::Arc<crate::router::Call>,
) -> Result<()> {
    let start = Instant::now();
    let cpu = cpu_seconds();
    let mut loaded = Loaded::default();
    let mut st = State {
        router: Some(call.clone()),
        session_name: format!("tlsw-temp-{}", hex::encode(random_bytes::<16>()?)),
        ..State::default()
    };
    let work = async {
        if args.is_sequence() { obtain(args, &mut st, &mut loaded).await?; }
        prepare(args, "direct", &mut st, 1)?;
        let spec = args
            .ca_cert
            .as_ref()
            .map_or("webpki".into(), |p| p.display().to_string());
        let (roots, _) = loaded.roots(&spec).await?;
        let mut client = reqwest::Client::builder()
            .https_only(true)
            .http1_only()
            .no_proxy()
            .redirect(reqwest::redirect::Policy::none())
            .tls_built_in_root_certs(false)
            .min_tls_version(reqwest::tls::Version::TLS_1_2)
            .max_tls_version(reqwest::tls::Version::TLS_1_2)
            .timeout(Duration::from_secs(args.timeout));
        for cert in roots.roots {
            client = client.add_root_certificate(reqwest::Certificate::from_der(&cert.0)?);
        }
        for mapping in &args.resolve {
            let (name, addr) = mapping
                .split_once('=')
                .ok_or_else(|| anyhow!("invalid resolve"))?;
            client = client.resolve(name, addr.parse()?);
        }
        let request = &call.request;
        let mut send = client.build()?.request(
            reqwest::Method::from_bytes(request.method.as_bytes())?,
            format!("https://{}{}", request.host, request.path),
        );
        for (n, v) in &request.ordered_headers {
            send = send.header(n, v);
        }
        st.detail.insert("direct_attempts".into(), json!(1));
        let response = send
            .bearer_auth(if args.is_sequence() { st.temporary_credential.clone().unwrap() } else { args.profile.credential()? })
            .header("X-Job-Id", &call.id)
            .header("Accept-Encoding", "identity")
            .header("Connection", "close")
            .body(request.body_bytes().to_vec())
            .send()
            .await?;
        let status = response.status().as_u16();
        let content_type = response
            .headers()
            .get("content-type")
            .map(|v| v.to_str().map(str::to_owned))
            .transpose()?;
        let reserved_receipt = response.headers().contains_key("x-witness-receipt");
        let mut response = response;
        let mut stream_raw = format!("HTTP/1.1 {status} Response\r\n");
        if let Some(ct) = &content_type {
            stream_raw.push_str(&format!("Content-Type: {ct}\r\n"));
        }
        stream_raw.push_str("\r\n");
        let mut stream_raw = stream_raw.into_bytes();
        let mut body = Vec::new();
        while let Some(chunk) = response.chunk().await? {
            if body.len() + chunk.len() > args.max_recv {
                bail!("direct response exceeds cap");
            }
            body.extend_from_slice(&chunk);
            if call.stream {
                stream_raw.extend_from_slice(&chunk);
                call.stream_update(&stream_raw).await?;
            }
        }
        call.deliver(http::ParsedResponse {
            status,
            content_type,
            reserved_receipt,
            chunked: false,
            body,
        })
        .await;
        Ok(())
    };
    let result: Result<()> = match tokio::time::timeout_at(call.deadline.into(), work).await {
        Ok(result) => result,
        Err(_) => {
            call.cancel_delivery().await;
            Err(anyhow!(
                "evidence deadline exceeded; direct routing cancelled"
            ))
        }
    };
    if st.cleanup_pending {
        cleanup(args, &mut st, &mut loaded).await;
    }
    if args.is_sequence() && !st.cleanup_pending && st.temporary_credential.is_some() {
        let dead = check_dead(args, &mut st, &mut loaded, Instant::now()).await;
        st.detail.insert(
            "dead_check_error".into(),
            json!(dead.err().map(|e| describe(&e))),
        );
    }
    call.cleanup_record(json!({"state":st.detail["credential_sequence"]["credential_status"],"dead_check_error":st.detail["dead_check_error"]})).await?;
    write_json(
        &args.out_dir.join("direct.record.json"),
        &json!({"role":"router_direct", "receipt_id":call.id,
        "outcome":"unverified", "error": result.as_ref().err().map(describe), "detail":st.detail,
        "timings_ms":{"total":ms(start)}, "resources":{"cpu_seconds":cpu_seconds()-cpu,"peak_rss_mb":peak_rss_mb()}}),
    )?;
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use clap::Parser;
    use std::io::{BufRead, BufReader};
    use std::process::{Child, Command, Stdio};

    // Like the other unit tests, keep this loopback fixture beside its callers.
    const MANAGEMENT_FIXTURE: &str = r#""""Loopback HTTPS fixture for obtain/revoke and stale-accept probe tests."""
import http.server
import json
from pathlib import Path
import ssl
import subprocess
import sys

root = Path(sys.argv[1])
confirmation = sys.argv[2]
limit = sys.argv[3]
subprocess.run([
    "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
    "-keyout", str(root / "fixture.key"), "-out", str(root / "ca.pem"),
    "-days", "1", "-subj", "/CN=localhost",
    "-addext", "subjectAltName=DNS:localhost",
    "-addext", "basicConstraints=critical,CA:FALSE",
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, status, body):
        encoded = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/keys":
            assert body["include_byok_in_limit"] is True
            data = {"hash": "fixture-hash"}
            if confirmation not in ("missing", "readback"):
                data["include_byok_in_limit"] = json.loads(confirmation)
            if limit not in ("missing", "readback"):
                data["limit"] = json.loads(limit)
            self.reply(201, {"key": "fixture-only-credential", "data": data})
        elif self.path in ("/probe", "/probe-stale", "/probe-forbidden", "/probe-error"):
            marker = root / "probe-count"
            count = int(marker.read_text()) if marker.exists() else 0
            marker.write_text(str(count + 1))
            status = ([200, 401, 200, 401, 401] if self.path == "/probe" else [200, 401, 200, 200, 200])[min(count, 4)]
            if self.path in ("/probe-forbidden", "/probe-error"):
                status = 401 if count == 0 else (403 if self.path == "/probe-forbidden" else 500)
            if status == 200:
                self.reply(200, {"id": "gen-fixture-probe-" + str(count), "choices": [{}],
                                 "usage": {"cost": 0.001}})
            else:
                self.reply(status, {"error": {"code": status}})
        elif self.path == "/api/v1/chat/completions":
            self.reply(200, {"id":"gen-fixture-main", "choices":[{"message":{"content":"pong"}}]})
        else:
            self.reply(404, {})

    def do_GET(self):
        assert self.path == "/keys/fixture-hash"
        marker = root / "readback-count"
        count = int(marker.read_text()) if marker.exists() else 0
        marker.write_text(str(count + 1))
        data = {}
        if confirmation == "readback" or limit == "readback":
            data["include_byok_in_limit"] = True
        if limit == "readback":
            data["limit"] = 0.05
        elif limit != "missing":
            data["limit"] = json.loads(limit)
        self.reply(200, {"data": data})

    def do_PATCH(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        assert self.path == "/keys/fixture-hash"
        (root / "revoked").touch()
        self.reply(200, {})


server = http.server.HTTPServer(("127.0.0.1", int(sys.argv[4])), Handler)
server.timeout = 10
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(root / "ca.pem", root / "fixture.key")
server.socket = context.wrap_socket(server.socket, server_side=True)
print(server.server_port, flush=True)
server.serve_forever()
"#;

    struct Fixture(Child);
    impl Drop for Fixture {
        fn drop(&mut self) {
            let _ = self.0.kill();
            let _ = self.0.wait();
        }
    }

    async fn obtain_fixture(confirmation: &str, limit: &str, port: u16) {
        let dir = std::env::temp_dir().join(format!(
            "tlsw-ch-witness-management-{}",
            hex::encode(random_bytes::<8>().unwrap())
        ));
        fs::create_dir(&dir).unwrap();
        let mut fixture = Fixture(
            Command::new("python3")
                .args(["-u", "-c", MANAGEMENT_FIXTURE])
                .arg(&dir)
                .arg(confirmation)
                .arg(limit)
                .arg(port.to_string())
                .stdout(Stdio::piped())
                .stderr(Stdio::null())
                .spawn()
                .unwrap(),
        );
        let mut port = String::new();
        BufReader::new(fixture.0.stdout.take().unwrap())
            .read_line(&mut port)
            .unwrap();
        let address = format!("127.0.0.1:{}", port.trim().parse::<u16>().unwrap());
        let obtain_path = dir.join("obtain.json");
        let revoke_path = dir.join("revoke.json");
        write_json(
            &obtain_path,
            &json!({"method":"POST", "host":"localhost",
            "path":"/keys", "address":address, "credential_field":"/key",
            "body":{"include_byok_in_limit":true,"limit":0.05}}),
        )
        .unwrap();
        write_json(
            &revoke_path,
            &json!({"method":"PATCH", "host":"localhost",
            "path":"/keys/{obtain:/data/hash}", "address":address,
            "body":{"disabled":true}}),
        )
        .unwrap();
        let mut args = ProverArgs::parse_from([
            "prover",
            "--profile", "credential-hidden",
            "--verifier",
            "127.0.0.1:1",
            "--mode",
            "proxy",
            "--request",
            "unused",
            "--seal",
            "unused",
            "--out-dir",
            "unused",
        ]);
        args.profile = Profile::CredentialSequence;
        args.obtain_request = Some(obtain_path);
        args.revoke_request = Some(revoke_path);
        args.ca_cert = Some(dir.join("ca.pem"));
        let mut st = State::default();
        let mut loaded = Loaded::default();
        let result = obtain(&args, &mut st, &mut loaded).await;
        let byok_confirmed =
            (confirmation == "true" || confirmation == "readback") && limit != "missing";
        let limit_confirmed = matches!(limit, "0.05" | "0.01" | "readback");
        let confirmed = byok_confirmed && limit_confirmed;
        if confirmed {
            assert!(result.is_ok(), "{}", describe(result.as_ref().unwrap_err()));
        }
        assert_eq!(result.is_ok(), confirmed);
        assert_eq!(
            st.detail["credential_sequence"]["include_byok_in_limit_confirmed"],
            byok_confirmed,
            "{}",
            result.as_ref().err().map(describe).unwrap_or_default()
        );
        assert_eq!(
            st.detail["credential_sequence"]["limit_confirmed"],
            limit_confirmed
        );
        let readback_count = fs::read_to_string(dir.join("readback-count")).unwrap_or("0".into());
        assert_eq!(
            readback_count,
            if confirmation == "missing"
                || confirmation == "readback"
                || limit == "missing"
                || limit == "readback"
            {
                "1"
            } else {
                "0"
            }
        );
        assert!(!st.tls_started);
        assert!(!st.dialed);
        assert_eq!(st.temporary_credential.is_some(), confirmed);
        assert_eq!(dir.join("revoked").exists(), !confirmed);
        if !confirmed {
            assert!(!st.cleanup_pending);
            assert_eq!(
                st.detail["credential_sequence"]["cleanup"]["succeeded"],
                true
            );
            assert_eq!(
                st.detail["credential_sequence"]["cleanup"]["attempts"][0]["status"],
                200
            );
        } else {
            assert!(st.cleanup_pending);
            cleanup(&args, &mut st, &mut loaded).await;
            assert!(dir.join("revoked").exists());
            st.dead_template = Some(
                serde_json::from_value(json!({
                "method":"POST", "host":"localhost", "path":"/probe",
                "address":address, "body":{}}))
                .unwrap(),
            );
            check_dead(&args, &mut st, &mut loaded, Instant::now())
                .await
                .unwrap();
            let checks = st.detail["credential_sequence"]["dead_checks"]
                .as_array()
                .unwrap();
            assert_eq!(
                checks
                    .iter()
                    .map(|c| c["status"].as_u64().unwrap())
                    .collect::<Vec<_>>(),
                [200, 401, 200, 401, 401]
            );
            assert_eq!(
                checks
                    .iter()
                    .map(|c| c["consecutive_refusals"].as_u64().unwrap())
                    .collect::<Vec<_>>(),
                [0, 1, 0, 1, 2]
            );
            assert_eq!(checks[0]["generation_id"], "gen-fixture-probe-0");
            assert_eq!(checks[2]["generation_id"], "gen-fixture-probe-2");
            assert_eq!(st.detail["credential_sequence"]["accepted_probe_count"], 2);
            assert!(
                st.detail["credential_sequence"]["second_consecutive_refusal_ms"]
                    .as_f64()
                    .unwrap()
                    >= 2000.0
            );
            // A paid runner can reserve a finite request budget even if the
            // provider never reaches two consecutive refusals. Exhaustion is
            // shared by later cleanup gates rather than resetting per call.
            st.detail["credential_sequence"]["dead_checks"] = json!([]);
            args.max_dead_check_attempts = 1;
            let error = check_dead(&args, &mut st, &mut loaded, Instant::now()).await.unwrap_err();
            assert!(describe(&error).contains("budget exhausted"));
            assert_eq!(st.detail["credential_sequence"]["dead_checks"].as_array().unwrap().len(), 1);
            assert!(st.detail["credential_sequence"]["second_consecutive_refusal_ms"].is_null());
            assert!(check_dead(&args, &mut st, &mut loaded, Instant::now()).await.is_err());
            assert_eq!(st.detail["credential_sequence"]["dead_checks"].as_array().unwrap().len(), 1);
            args.max_dead_check_attempts = 20;
            for (route, status) in [("/probe-forbidden", 403), ("/probe-error", 500)] {
                fs::write(dir.join("probe-count"), "0").unwrap();
                st.detail["credential_sequence"]["dead_checks"] = json!([]);
                st.dead_template = Some(
                    serde_json::from_value(json!({
                    "method":"POST", "host":"localhost", "path":route,
                    "address":address, "body":{}}))
                    .unwrap(),
                );
                let error = check_dead(&args, &mut st, &mut loaded, Instant::now())
                    .await
                    .unwrap_err();
                assert!(describe(&error).contains(&format!("status {status}")));
                assert!(st.detail["credential_sequence"]["reveal_started_at"].is_null());
                assert!(
                    st.detail["credential_sequence"]["second_consecutive_refusal_ms"].is_null()
                );
                st.cleanup_pending = true;
                cleanup(&args, &mut st, &mut loaded).await;
                assert!(!st.cleanup_pending);
                assert_eq!(
                    st.detail["credential_sequence"]["cleanup"]["succeeded"],
                    true
                );
            }
            st.dead_template = Some(
                serde_json::from_value(json!({
                "method":"POST", "host":"localhost", "path":"/probe-stale",
                "address":address, "body":{}}))
                .unwrap(),
            );
            // A 1 s deadline sees the lone refusal, then must fail without
            // a second consecutive refusal. The real router fixture also
            // checks that the reveal timestamp remains absent on failure.
            fs::write(dir.join("probe-count"), "0").unwrap();
            st.detail.get_mut("credential_sequence").unwrap()["dead_checks"] = json!([]);
            args.dead_check_timeout = 1;
            let error = check_dead(&args, &mut st, &mut loaded, Instant::now())
                .await
                .unwrap_err();
            assert!(describe(&error).contains("deadline"));
            assert!(st.detail["credential_sequence"]["reveal_started_at"].is_null());
        }
    }

    #[tokio::test]
    async fn unconfirmed_byok_limit_revokes_and_refuses_before_use() {
        for confirmation in ["missing", "false", "\"true\""] {
            obtain_fixture(confirmation, "0.05", 18990).await;
        }
    }

    #[tokio::test]
    async fn invalid_numeric_limit_revokes_and_refuses_before_use() {
        for limit in ["missing", "null", "0.06", "0", "-1", "\"0.05\""] {
            obtain_fixture("true", limit, 18991).await;
        }
    }

    #[tokio::test]
    async fn confirmed_byok_limit_proceeds_and_records_stale_probe_generation() {
        obtain_fixture("true", "0.05", 18992).await;
        obtain_fixture("readback", "0.05", 18992).await;
        obtain_fixture("true", "readback", 18992).await;
    }
}
