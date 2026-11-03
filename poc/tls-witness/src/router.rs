//! Ordinary HTTP ingress, asynchronous receipt evidence, and offline client checks.
use crate::{
    Profile, Mode, ProverArgs, http,
    record::{self, Receipt, Verdict},
};
use anyhow::{Result, anyhow, bail};
use clap::Parser;
use ed25519_dalek::SigningKey;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    io::Write as _,
    path::PathBuf,
    sync::{Arc, Mutex},
    time::{Duration, Instant},
};
use tokio::{
    io::{AsyncReadExt, AsyncWriteExt},
    net::{TcpListener, TcpStream},
};

const RECEIPT: &str = "X-Witness-Receipt";
const DEADLINE: u64 = 240;

#[derive(Parser)]
pub struct Args {
    #[arg(long, value_enum, default_value = "authorization")]
    credential_header: crate::CredentialHeader,
    #[arg(long, value_enum)]
    pub profile: Profile,
    #[arg(long, default_value = "127.0.0.1:8080")]
    listen: String,
    /// Execute the fixture submit/poll/fetch protocol as one receipt.
    #[arg(long)]
    job: bool,
    /// Ordered witness endpoints, repeated in preference order.
    #[arg(long, required = true)]
    witness: Vec<String>,
    #[arg(long)]
    operator_key: PathBuf,
    #[arg(long)]
    host: String,
    #[arg(long, default_value = "/api/v1/chat/completions")]
    path: String,
    #[arg(long)]
    obtain_request: Option<PathBuf>,
    #[arg(long)]
    revoke_request: Option<PathBuf>,
    #[arg(long)]
    dead_check_request: Option<PathBuf>,
    /// Test the dead-check request while the session credential is still live.
    #[arg(long)]
    live_check: bool,
    #[arg(long)]
    ca_cert: Option<PathBuf>,
    #[arg(long)]
    resolve: Vec<String>,
    #[arg(long, default_value_t = 16384)]
    max_sent: usize,
    #[arg(long, default_value_t = 262144)]
    max_recv: usize,
    /// Maximum active witnessed sessions; admission above this returns 503.
    #[arg(long, default_value_t = 4, value_parser = clap::value_parser!(u16).range(1..=16))]
    max_sessions: u16,
    /// Maximum seconds for each witnessed session (including credential cleanup).
    #[arg(long, default_value_t = 30)]
    session_timeout: u64,
    #[arg(long, default_value = "runs/router")]
    record_dir: PathBuf,
    /// Append-only receipt admission log; default: RECORD_DIR/admissions.jsonl.
    #[arg(long)]
    admission_log: Option<PathBuf>,
    /// Cancel routing at this deadline; credential cleanup runs after cancellation.
    #[arg(long, default_value_t = DEADLINE, value_parser = clap::value_parser!(u64).range(1..))]
    evidence_deadline: u64,
    /// Bound provider-visible refusal probes per admitted session.
    #[arg(long, default_value_t = 20, value_parser = clap::value_parser!(u64).range(1..))]
    max_dead_check_attempts: u64,
}

impl Args {
    pub fn validate(&self) -> Result<()> {
        let roots = self.ca_cert.as_ref().map_or("webpki".into(), |p| p.display().to_string());
        self.profile.check_environment(&roots)?;
        self.credential_header.validate(self.profile)?;
        self.profile.lifecycle(self.obtain_request.is_some(), self.revoke_request.is_some(), self.dead_check_request.is_some() || self.live_check)?;
        if self.profile != Profile::CredentialSequence { self.profile.credential()?; }
        Ok(())
    }
}

#[derive(Parser)]
pub struct ReconcileArgs {
    #[arg(long)]
    admission_log: PathBuf,
    #[arg(long)]
    record_dir: PathBuf,
}

fn durable_json(path: &std::path::Path, value: &Value) -> Result<()> {
    record::write_json_atomic(path, value)?;
    fs::File::open(path)?.sync_all()?;
    fs::File::open(path.parent().unwrap())?.sync_all()?;
    Ok(())
}

async fn persist(path: PathBuf, value: Value) -> Result<()> {
    tokio::task::spawn_blocking(move || durable_json(&path, &value)).await?
}

fn admit(path: &std::path::Path, id: &str) -> Result<()> {
    let mut file = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)?;
    file.write_all(
        format!(
            "{}\n",
            json!({"receipt_id":id,"admitted_at":record::now_ms_rfc3339()})
        )
        .as_bytes(),
    )?;
    file.sync_all()?;
    fs::File::open(
        path.parent()
            .filter(|p| !p.as_os_str().is_empty())
            .unwrap_or(std::path::Path::new(".")),
    )?
    .sync_all()?;
    Ok(())
}

fn admitted(path: &std::path::Path) -> Result<Vec<String>> {
    let mut ids = Vec::new();
    let bytes = fs::read(path)?;
    let end = bytes.iter().rposition(|&b| b == b'\n').map_or(0, |i| i + 1);
    if end != bytes.len() {
        eprintln!("torn final admission line ignored in {}", path.display());
    }
    for line in std::str::from_utf8(&bytes[..end])?.lines() {
        let row: Value = serde_json::from_str(line)?;
        let id = row["receipt_id"]
            .as_str()
            .ok_or_else(|| anyhow!("admission has no receipt id"))?;
        crate::seal::check_job_id(id)?;
        ids.push(id.to_owned());
    }
    Ok(ids)
}

fn recovery_ids(log: &std::path::Path, records: &std::path::Path) -> Result<BTreeSet<String>> {
    let mut ids: BTreeSet<_> = admitted(log)?.into_iter().collect();
    for entry in fs::read_dir(records)? {
        let entry = entry?;
        if entry.file_type()?.is_dir() && entry.path().join("evidence.json").exists() {
            let id = entry.file_name().to_string_lossy().into_owned();
            crate::seal::check_job_id(&id)?;
            ids.insert(id);
        }
    }
    Ok(ids)
}

pub fn reconcile(args: ReconcileArgs) -> Result<bool> {
    let mut rows = Vec::new();
    let mut missing = 0;
    for id in admitted(&args.admission_log)? {
        let evidence = fs::read(args.record_dir.join(&id).join("evidence.json"))
            .ok()
            .and_then(|b| serde_json::from_slice::<Value>(&b).ok());
        let outcome = evidence
            .as_ref()
            .filter(|e| e["receipt_id"] == id)
            .and_then(|e| e["state"].as_str())
            .unwrap_or("missing");
        if !matches!(outcome, "verified" | "unverified") {
            missing += 1;
        }
        rows.push(json!({"receipt_id":id,"outcome":outcome,"reason":evidence.as_ref().and_then(|e|e.get("reason")),
            "delivery":evidence.as_ref().and_then(|e|e.get("delivery")),
            "credential_cleanup":evidence.as_ref().and_then(|e|e.get("credential_cleanup"))}));
    }
    println!(
        "{}",
        serde_json::to_string_pretty(
            &json!({"admitted":rows.len(),"without_terminal_outcome":missing,"receipts":rows})
        )?
    );
    Ok(missing == 0)
}

struct Delivery {
    tcp: TcpStream,
    head_sent: bool,
    body_seen: usize,
    accepted: usize,
    accepted_hash: Sha256,
    wire_at: usize,
    chunked: bool,
    chunk_left: usize,
    chunk_crlf: bool,
    stream_done: bool,
    complete: bool,
    disconnected: bool,
    cancelled: bool,
    first_ms: Option<u64>,
    total_ms: Option<u64>,
}
impl Delivery {
    async fn write(&mut self, mut bytes: &[u8], body: bool, start: Instant) {
        if self.disconnected || self.cancelled {
            return;
        }
        while !bytes.is_empty() {
            match tokio::time::timeout(Duration::from_secs(2), self.tcp.write(bytes)).await {
                Ok(Ok(n)) if n > 0 => {
                    if body {
                        self.first_ms
                            .get_or_insert(start.elapsed().as_millis() as u64);
                        self.accepted += n;
                        self.accepted_hash.update(&bytes[..n]);
                    }
                    bytes = &bytes[n..];
                }
                _ => {
                    self.disconnected = true;
                    break;
                }
            }
        }
    }
    fn facts(&self) -> Value {
        json!({"rule":"body", "complete":self.complete, "client_disconnected":self.disconnected,
            "cancelled":self.cancelled,"socket_accepted_body_bytes":self.accepted,
            "socket_accepted_body_sha256":hex::encode(self.accepted_hash.clone().finalize()),
            "first_chunk_ms":self.first_ms,"total_ms":self.total_ms})
    }
}

pub struct Call {
    pub id: String,
    pub request: http::RequestFile,
    key: SigningKey,
    delivery: Arc<tokio::sync::Mutex<Delivery>>,
    capture: Option<Mutex<Option<http::ParsedResponse>>>,
    pub stream: bool,
    pub deadline: Instant,
    start: Instant,
    evidence: Mutex<Value>,
    dir: PathBuf,
}

impl Call {
    pub fn statement(&self, session: &str) -> Result<Value> {
        let mut statement = json!({"v":1,"session_id":session,"receipt_id":self.id,
            "method":self.request.method,"host":self.request.host,"path":self.request.path,
            "forwarded_headers_sha256":http::forwarded_hash(&self.request.ordered_headers),
            "body_sha256":record::sha256_hex(self.request.body_bytes()),"body_bytes":self.request.body_bytes().len()});
        record::sign(&mut statement, "operator_pub", &self.key);
        // Public signed statement only; neither credential nor request body.
        record::write_json(
            &self.dir.join(format!("{session}.statement.json")),
            &statement,
        )?;
        self.evidence.lock().unwrap()["operator_statement"] = statement.clone();
        Ok(statement)
    }
    /// Write each newly decrypted body byte, including all SSE comments. HTTP
    /// transfer coding is regenerated and is not part of the signed body.
    pub async fn stream_update(&self, received: &[u8]) -> Result<()> {
        if !self.stream {
            return Ok(());
        }
        let mut d = self.delivery.lock().await;
        let before = (d.first_ms, d.disconnected);
        if !d.head_sent {
            let mut headers = [httparse::EMPTY_HEADER; 64];
            let mut response = httparse::Response::new(&mut headers);
            let httparse::Status::Complete(at) = response.parse(received)? else { return Ok(()); };
            d.wire_at = at;
            d.chunked = response.headers.iter().any(|h| h.name.eq_ignore_ascii_case("transfer-encoding") && h.value.eq_ignore_ascii_case(b"chunked"));
            let mut head = format!(
                "HTTP/1.1 {} Response\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n{RECEIPT}: {}\r\n",
                response.code.unwrap_or_default(),
                self.id
            );
            if let Some(ct) = response
                .headers
                .iter()
                .find(|h| h.name.eq_ignore_ascii_case("content-type"))
            {
                head.push_str(&format!(
                    "Content-Type: {}\r\n",
                    std::str::from_utf8(ct.value)?
                ));
            }
            head.push_str("\r\n");
            d.head_sent = true;
            d.write(head.as_bytes(), false, self.start).await;
        }
        let mut chunk = Vec::new();
        while d.wire_at < received.len() && !d.stream_done {
            if !d.chunked {
                chunk.extend_from_slice(&received[d.wire_at..]);
                d.wire_at = received.len();
            } else if d.chunk_left > 0 {
                let n = d.chunk_left.min(received.len() - d.wire_at);
                chunk.extend_from_slice(&received[d.wire_at..d.wire_at + n]);
                d.wire_at += n;
                d.chunk_left -= n;
                d.chunk_crlf = d.chunk_left == 0;
            } else if d.chunk_crlf {
                if received.len() - d.wire_at < 2 { break; }
                if &received[d.wire_at..d.wire_at + 2] != b"\r\n" { bail!("chunk lacks CRLF"); }
                d.wire_at += 2;
                d.chunk_crlf = false;
            } else {
                let Some(end) = received[d.wire_at..].windows(2).position(|w| w == b"\r\n") else { break; };
                let line = std::str::from_utf8(&received[d.wire_at..d.wire_at + end])?;
                d.chunk_left = usize::from_str_radix(line.split(';').next().unwrap().trim(), 16)?;
                d.wire_at += end + 2;
                d.stream_done = d.chunk_left == 0;
            }
        }
        if !chunk.is_empty() {
            d.write(format!("{:x}\r\n", chunk.len()).as_bytes(), false, self.start).await;
            d.write(&chunk, true, self.start).await;
            d.write(b"\r\n", false, self.start).await;
            d.body_seen += chunk.len();
        }
        if before != (d.first_ms, d.disconnected) {
            persist(self.dir.join("delivery.json"), d.facts()).await?;
        }
        Ok(())
    }
    pub async fn deliver(&self, response: http::ParsedResponse) {
        if let Some(capture) = &self.capture {
            *capture.lock().unwrap() = Some(response);
            return;
        }
        if response.reserved_receipt {
            let _ = persist(self.dir.join("reserved-header.json"), json!({"dropped":RECEIPT})).await;
        }
        let mut d = self.delivery.lock().await;
        if d.complete {
            return;
        }
        if self.stream && d.head_sent {
            // Parsing the entire response must agree with the streamed prefix.
            if response.body.len() != d.body_seen || record::sha256_hex(&response.body[..d.accepted]) != hex::encode(d.accepted_hash.clone().finalize()) {
                d.cancelled = true;
            }
            d.write(b"0\r\n\r\n", false, self.start).await;
        } else {
            let mut head = format!(
                "HTTP/1.1 {} Response\r\nContent-Length: {}\r\nConnection: close\r\n{RECEIPT}: {}\r\n",
                response.status,
                response.body.len(),
                self.id
            );
            if let Some(ct) = response.content_type {
                head.push_str(&format!("Content-Type: {ct}\r\n"));
            }
            head.push_str("\r\n");
            d.head_sent = true;
            d.write(head.as_bytes(), false, self.start).await;
            d.write(&response.body, true, self.start).await;
        }
        d.complete = !d.disconnected && !d.cancelled;
        d.total_ms = Some(self.start.elapsed().as_millis() as u64);
        let _ = d.tcp.shutdown().await;
        let _ = persist(self.dir.join("delivery.json"), d.facts()).await;
    }
    pub async fn cancel_delivery(&self) {
        let mut d = self.delivery.lock().await;
        d.cancelled = true;
        let _ = d.tcp.shutdown().await;
        let _ = persist(self.dir.join("delivery.json"), d.facts()).await;
    }
    /// Only the provider hash is durable; never the credential or create body.
    pub async fn obtained(&self, hash: &str) -> Result<()> {
        persist(self.dir.join("credential.json"), json!({"provider_hash":hash,"state":"cleanup_required"})).await
    }
    pub async fn cleanup_record(&self, outcome: Value) -> Result<()> {
        let step = self.evidence.lock().unwrap().get("step").cloned();
        let cleanup = if let Some(step) = step {
            let mut outcomes: Vec<Value> = match tokio::fs::read(self.dir.join("credential-cleanup.json")).await {
                Ok(bytes) => serde_json::from_slice(&bytes)?,
                Err(e) if e.kind() == std::io::ErrorKind::NotFound => Vec::new(),
                Err(e) => return Err(e.into()),
            };
            outcomes.retain(|v| v["step"] != step);
            outcomes.push(json!({"step":step,"outcome":outcome}));
            json!(outcomes)
        } else { outcome.clone() };
        persist(self.dir.join("credential-cleanup.json"), cleanup.clone()).await?;
        self.evidence.lock().unwrap()["credential_cleanup"] = cleanup;
        if outcome["state"] == "dead_confirmed" {
            let path = self.dir.join("credential.json");
            if let Ok(bytes) = tokio::fs::read(&path).await {
                let mut credential: Value = serde_json::from_slice(&bytes)?;
                credential["state"] = json!("dead_confirmed");
                persist(path, credential).await?;
            }
        }
        Ok(())
    }
    pub fn verified(&self, receipt: Value) {
        let mut evidence = self.evidence.lock().unwrap();
        evidence["witness_key_id"] = receipt["verdict"]["verifier_pub"].clone();
        evidence["receipt"] = receipt;
    }
    pub fn failure(&self, reason: &str) {
        let mut evidence = self.evidence.lock().unwrap();
        if evidence["state"] == "pending" {
            evidence["reason"] = json!(reason);
        }
    }
    async fn finish(&self, reason: &str) {
        let mut d = self.delivery.lock().await;
        if !d.head_sent {
            let head = format!(
                "HTTP/1.1 502 Response\r\nContent-Length: 0\r\nConnection: close\r\n{RECEIPT}: {}\r\n\r\n",
                self.id
            );
            d.write(head.as_bytes(), false, self.start).await;
        }
        let _ = d.tcp.shutdown().await;
        let delivery = d.facts();
        drop(d);
        let terminal = {
        let mut evidence = self.evidence.lock().unwrap();
        if evidence["state"] != "pending" {
            return;
        }
        evidence["delivery"] = delivery.clone();
        if !delivery["complete"].as_bool().unwrap_or(false) {
            if let Some(receipt) = evidence.as_object_mut().unwrap().remove("receipt") {
                evidence["witnessed_receipt"] = receipt;
            }
            evidence.as_object_mut().unwrap().remove("chain");
            if delivery["client_disconnected"] == true {
                evidence["reason"] = json!("client_disconnected; upstream read to completion unless witness/deadline interrupted it");
            }
        }
        if evidence.get("receipt").is_some() || evidence.get("chain").is_some() {
            evidence["state"] = json!("verified");
            evidence.as_object_mut().unwrap().remove("reason");
        } else {
            evidence["state"] = json!("unverified");
            if evidence.get("reason").is_none() {
                evidence["reason"] = json!(reason);
            }
        }
        evidence["terminal_at"] = json!(record::now_ms_rfc3339());
                evidence.clone()
        };
        let _ = persist(self.dir.join("evidence.json"), terminal).await;
    }
}

pub fn verify_operator(statement: &Value, session: &str, permitted: &[PathBuf]) -> Result<()> {
    record::verify_signature(statement, "operator_pub")?;
    if statement["session_id"] != session {
        bail!("operator statement session mismatch");
    }
    let mut allowed = false;
    for key in permitted {
        if statement["operator_pub"].as_str() == Some(fs::read_to_string(key)?.trim()) {
            allowed = true;
        }
    }
    if !allowed {
        bail!("operator key is not configured at this witness");
    }
    Ok(())
}

pub fn match_statement(
    statement: &Value,
    session: &str,
    req: &http::ParsedRequest,
    body: &[u8],
) -> Result<()> {
    let expected = json!({"session_id":session,"receipt_id":req.job_id,
        "method":req.method,"host":req.host,"path":req.path,
        "forwarded_headers_sha256":req.forwarded_headers_sha256,
        "body_sha256":record::sha256_hex(body),"body_bytes":body.len()});
    for (name, value) in expected.as_object().unwrap() {
        if statement[name] != *value {
            bail!("operator statement differs from witnessed {name}");
        }
    }
    Ok(())
}

struct ClientRequest {
    method: String,
    target: String,
    headers: Vec<(String, String)>,
    body: Vec<u8>,
    expect: bool,
    require: bool,
}

/// One framed HTTP request. Headers are retained in wire order, duplicates intact.
fn client_request(raw: &[u8], head_only: bool) -> Result<Option<(ClientRequest, usize)>> {
    let mut headers = [httparse::EMPTY_HEADER; 64];
    let mut req = httparse::Request::new(&mut headers);
    let head = match req.parse(raw)? {
        httparse::Status::Partial => return Ok(None),
        httparse::Status::Complete(n) => n,
    };
    let mut length = None;
    let mut transfer = None;
    let mut expect = false;
    let mut require = false;
    let mut kept = Vec::new();
    for h in req.headers.iter() {
        let name = h.name.to_ascii_lowercase();
        let value = std::str::from_utf8(h.value)?.to_string();
        match name.as_str() {
            "content-length" => {
                if length.is_some() {
                    bail!("duplicate Content-Length");
                }
                length = Some(http::content_length(value.as_bytes())?);
            }
            "transfer-encoding" => {
                if transfer.is_some() {
                    bail!("duplicate Transfer-Encoding");
                }
                transfer = Some(value.clone());
            }
            "expect" => {
                if !value.eq_ignore_ascii_case("100-continue") {
                    bail!("unsupported Expect");
                }
                expect = true;
            }
            "x-client-require-witness" => {
                require |= value.eq_ignore_ascii_case("true");
            }
            _ => {}
        }
        if http::forwarded(&name) {
            kept.push((name, value));
        }
    }
    if length.is_some() && transfer.is_some() {
        bail!("ambiguous request framing");
    }
    let (body, used) = if head_only {
        (Vec::new(), head)
    } else if let Some(encoding) = transfer {
        if !encoding.eq_ignore_ascii_case("chunked") {
            bail!("unsupported request encoding");
        }
        match http::dechunk(&raw[head..]) {
            Ok((b, n)) => (b, head + n),
            Err(_) => return Ok(None),
        }
    } else {
        let end = head
            .checked_add(length.unwrap_or(0))
            .ok_or_else(|| anyhow!("request length overflow"))?;
        if raw.len() < end {
            return Ok(None);
        }
        (raw[head..end].to_vec(), end)
    };
    Ok(Some((
        ClientRequest {
            method: req.method.unwrap_or_default().into(),
            target: req.path.unwrap_or_default().into(),
            headers: kept,
            body,
            expect,
            require,
        },
        used,
    )))
}

async fn recover_pending(args: &Args, log: &std::path::Path) -> Result<()> {
    // Recover the union before accepting new admissions. Only an uncommitted,
    // torn suffix may be discarded; malformed complete lines already fail above.
    let ids = recovery_ids(log, &args.record_dir)?;
    let log = log.to_owned();
    tokio::task::spawn_blocking(move || -> Result<()> {
        let bytes = fs::read(&log)?;
        if !bytes.is_empty() && !bytes.ends_with(b"\n") {
            let end = bytes.iter().rposition(|&b| b == b'\n').map_or(0, |i| i + 1);
            let file = fs::OpenOptions::new().write(true).open(log)?;
            file.set_len(end as u64)?;
            file.sync_all()?;
        }
        Ok(())
    }).await??;
    for id in ids {
        let dir = args.record_dir.join(&id);
        record::ensure_dir(&dir)?;
        let path = dir.join("evidence.json");
        let mut evidence: Value = fs::read(&path)
            .ok()
            .and_then(|b| serde_json::from_slice(&b).ok())
            .unwrap_or_else(|| json!({"v":1,"receipt_id":id,"state":"pending"}));
        if evidence["state"] == "pending" {
            if args.profile != Profile::CredentialSequence {
                evidence["credential_cleanup"] = json!({"state":"not_applicable","profile":args.profile});
            } else if let Ok(bytes) = fs::read(dir.join("credential.json")) {
                let credential: Value = serde_json::from_slice(&bytes)?;
                let result = crate::prover::router_recover(
                    &prover_args(args, dir.clone(), String::new()),
                    &credential,
                )
                .await;
                let cleanup = match result {
                    Ok(value) => value,
                    Err(e) => json!({"state":"cleanup_failed","reason":record::describe(&e)}),
                };
                persist(dir.join("credential-cleanup.json"), cleanup.clone()).await?;
                evidence["credential_cleanup"] = cleanup;
            } else {
                evidence["credential_cleanup"] = json!({"state":"unknown","reason":"no durable provider hash; credential creation may have been interrupted"});
            }
            if let Ok(bytes) = fs::read(dir.join("delivery.json")) {
                evidence["delivery"] = serde_json::from_slice(&bytes)?;
            }
            evidence["state"] = json!("unverified");
            evidence["reason"] =
                json!("router restarted before evidence completed; no upstream retry");
            evidence["terminal_at"] = json!(record::now_ms_rfc3339());
            evidence.as_object_mut().unwrap().remove("receipt");
            persist(path, evidence).await?;
        }
    }
    Ok(())
}

pub async fn run(args: Args) -> Result<()> {
    record::ensure_dir(&args.record_dir)?;
    let key = record::load_or_create_key(&args.operator_key)?;
    let log = args
        .admission_log
        .clone()
        .unwrap_or_else(|| args.record_dir.join("admissions.jsonl"));
    if let Some(parent) = log.parent().filter(|p| !p.as_os_str().is_empty()) {
        record::ensure_dir(parent)?;
    }
    if args.job && args.path != "/jobs" { bail!("--job requires --path /jobs"); }
    if !log.exists() {
        fs::File::create(&log)?.sync_all()?;
    }
    recover_pending(&args, &log).await?;
    let listener = TcpListener::bind(&args.listen).await?;
    println!(
        "router listening on {}; evidence cancellation deadline {}s",
        listener.local_addr()?,
        args.evidence_deadline
    );
    let args = Arc::new(args);
    // Bound active prover work; four sessions fit the run's workstation budget.
    let slots = Arc::new(tokio::sync::Semaphore::new(args.max_sessions as usize));
    loop {
        let (tcp, _) = listener.accept().await?;
        let (args, key, slots) = (args.clone(), key.clone(), slots.clone());
        tokio::spawn(async move {
            if let Err(e) = serve(tcp, args, key, slots).await {
                eprintln!("router client: {e:#}");
            }
        });
    }
}

async fn respond(
    tcp: &mut TcpStream,
    status: u16,
    ct: Option<&str>,
    body: &[u8],
    receipt: Option<&str>,
) -> Result<()> {
    let mut head = format!(
        "HTTP/1.1 {status} Response\r\nContent-Length: {}\r\nConnection: close\r\n",
        body.len()
    );
    if let Some(ct) = ct {
        head.push_str(&format!("Content-Type: {ct}\r\n"));
    }
    if let Some(id) = receipt {
        head.push_str(&format!("{RECEIPT}: {id}\r\n"));
    }
    head.push_str("\r\n");
    tcp.write_all(head.as_bytes()).await?;
    tcp.write_all(body).await?;
    Ok(())
}

async fn serve(
    mut tcp: TcpStream,
    args: Arc<Args>,
    key: SigningKey,
    slots: Arc<tokio::sync::Semaphore>,
) -> Result<()> {
    let start = Instant::now();
    let mut raw = Vec::new();
    let mut sent_continue = false;
    let req = tokio::time::timeout(Duration::from_secs(30), async {
        loop {
            let mut buf = [0u8; 8192];
            let n = tcp.read(&mut buf).await?;
            if n == 0 {
                bail!("client closed incomplete request");
            }
            raw.extend_from_slice(&buf[..n]);
            if raw.len() > args.max_sent {
                bail!("client request exceeds cap");
            }
            if let Some((head, _)) = client_request(&raw, true)? {
                if head.expect && !sent_continue {
                    tcp.write_all(b"HTTP/1.1 100 Continue\r\n\r\n").await?;
                    sent_continue = true;
                }
            }
            if let Some((req, used)) = client_request(&raw, false)? {
                if used != raw.len() {
                    bail!("pipelining is not supported");
                }
                return Ok::<_, anyhow::Error>(req);
            }
        }
    })
    .await;
    let req = match req {
        Ok(Ok(req)) => req,
        _ => {
            respond(&mut tcp, 400, None, b"invalid or incomplete request", None).await?;
            return Ok(());
        }
    };
    if req.method == "GET" {
        let id = req.target.strip_prefix("/evidence/").unwrap_or_default();
        if crate::seal::check_job_id(id).is_err() {
            respond(&mut tcp, 404, None, b"unknown receipt", None).await?;
            return Ok(());
        }
        let evidence = match fs::read(args.record_dir.join(id).join("evidence.json")) {
            Ok(e) => e,
            Err(_) => {
                respond(&mut tcp, 404, None, b"unknown receipt", None).await?;
                return Ok(());
            }
        };
        return respond(&mut tcp, 200, Some("application/json"), &evidence, None).await;
    }
    if req.method != "POST" || req.target.split('?').next() != Some(args.path.as_str()) {
        respond(&mut tcp, 404, None, b"unknown route", None).await?;
        return Ok(());
    }
    let permit = match slots.try_acquire_owned() {
        Ok(p) => p,
        Err(_) => {
            respond(&mut tcp, 503, None, b"router at capacity", None).await?;
            return Ok(());
        }
    };
    let id = hex::encode(record::random_bytes::<16>()?);
    let dir = args.record_dir.join(&id);
    record::ensure_dir(&dir)?;
    // Admission must be durable before a task capable of making an upstream call exists.
    let log = args
        .admission_log
        .clone()
        .unwrap_or_else(|| args.record_dir.join("admissions.jsonl"));
    let admitted_id = id.clone();
    tokio::task::spawn_blocking(move || admit(&log, &admitted_id)).await??;
    let stream = serde_json::from_slice::<Value>(&req.body)
        .ok()
        .is_some_and(|b| b["stream"] == true);
    let call = Arc::new(Call {
        id: id.clone(),
        key,
        delivery: Arc::new(tokio::sync::Mutex::new(Delivery {
            tcp,
            head_sent: false,
            body_seen: 0,
            accepted: 0, accepted_hash: Sha256::new(), wire_at: 0, chunked: false, chunk_left: 0, chunk_crlf: false, stream_done: false,
            complete: false,
            disconnected: false,
            cancelled: false,
            first_ms: None,
            total_ms: None,
        })),
        capture: None,
        stream: stream && !args.job,
        deadline: start + Duration::from_secs(args.evidence_deadline),
        start,
        request: http::RequestFile {
            method: req.method,
            host: args.host.clone(),
            path: req.target,
            headers: BTreeMap::new(),
            ordered_headers: req.headers,
            raw_body: Some(req.body),
            body: None,
        },
        evidence: Mutex::new(
            json!({"v":1,"state":"pending","receipt_id":id,"deadline_seconds":args.evidence_deadline,
            "created_at":record::now_ms_rfc3339()}),
        ),
        dir,
    });
    let initial = call.evidence.lock().unwrap().clone();
    persist(call.dir.join("evidence.json"), initial).await?;
    tokio::spawn(async move {
        let cpu_start = record::cpu_seconds();
        let result = if args.job { route_job(&args, call.clone()).await } else { route(&args, call.clone(), req.require).await };
        // Prover work is done. Release admission before publishing terminal
        // evidence so a client can immediately start its next request.
        drop(permit);
        call.finish(&match result {
            Ok(()) => "no witness evidence".into(),
            Err(e) => record::describe(&e),
        })
        .await;
        let _ = record::write_json(&call.dir.join("operator.resources.json"), &json!({"cpu_seconds":record::cpu_seconds()-cpu_start,"peak_rss_mb":record::peak_rss_mb(),"cgroup_caps":record::cgroup_caps(),"scope":"router whole-process per-request delta; isolated call only","profile":args.profile}));
    });
    Ok(())
}

fn prover_args(args: &Args, dir: PathBuf, witness: String) -> ProverArgs {
    ProverArgs {
        credential_header: args.credential_header,
        obtain_request: args.obtain_request.clone(),
        revoke_request: args.revoke_request.clone(),
        dead_check_request: args.dead_check_request.clone(),
        live_check: args.live_check,
        dead_check_timeout: 10,
        max_dead_check_attempts: args.max_dead_check_attempts,
        management_timeout: 10,
        profile: args.profile,
        verifier: witness,
        mode: Mode::Proxy,
        request: PathBuf::new(),
        seal: PathBuf::new(),
        batch_max: 1,
        batch_window_ms: None,
        out_dir: dir,
        ca_cert: args.ca_cert.clone(),
        max_sent: args.max_sent,
        max_recv: args.max_recv,
        tlsn_threads: 1,
        prewarm: None,
        stream: false,
        label: Some("router".into()),
        resolve: args.resolve.clone(),
        srs: PathBuf::from("target/srs/g1.dat"),
        decrypt_online: false,
        recv_records_online: None,
        timeout: args.session_timeout,
        sessions: 1,
    }
}

async fn route(args: &Args, call: Arc<Call>, require: bool) -> Result<()> {
    for (i, witness) in args.witness.iter().enumerate() {
        let dir = call.dir.join(format!("attempt-{}", i + 1));
        record::ensure_dir(&dir)?;
        let retry = crate::prover::router_session(
            &{
                let mut p = prover_args(args, dir, witness.clone());
                p.stream = call.stream;
                p
            },
            call.clone(),
        )
        .await?;
        if !retry {
            return Ok(());
        }
    }
    if require {
        call.deliver(http::ParsedResponse {
            status: 503,
            content_type: Some("text/plain".into()),
            body: b"no witness available".to_vec(),
            chunked: false,
            reserved_receipt: false,
        })
        .await;
        bail!("all witnesses declined before upstream; client required witness; no upstream call");
    }
    call.failure("all witnesses declined before upstream; direct response has no witness evidence");
    let dir = call.dir.join("direct");
    record::ensure_dir(&dir)?;
    crate::prover::router_direct(&prover_args(args, dir, String::new()), call).await
}

// Public, credential-free HTTP representations used only inside chain evidence.
fn request_wire(request: &http::RequestFile) -> Vec<u8> {
    let mut raw = format!("{} {} HTTP/1.1\r\nHost: router\r\nContent-Length: {}\r\n", request.method, request.path, request.body_bytes().len());
    for (name, value) in &request.ordered_headers {
        raw.push_str(&format!("{name}: {value}\r\n"));
    }
    raw.push_str("\r\n");
    [raw.as_bytes(), request.body_bytes()].concat()
}

fn response_wire(response: &http::ParsedResponse, id: &str) -> Vec<u8> {
    let mut raw = format!("HTTP/1.1 {} Response\r\nContent-Length: {}\r\nX-Witness-Receipt: {id}\r\n", response.status, response.body.len());
    if let Some(ct) = &response.content_type { raw.push_str(&format!("Content-Type: {ct}\r\n")); }
    raw.push_str("\r\n");
    [raw.as_bytes(), &response.body].concat()
}

fn job_id(body: &[u8]) -> Result<String> {
    let value = evidence_json(body)?;
    let id = value["job_id"].as_str().ok_or_else(|| anyhow!("submit omitted job_id"))?;
    // A segment, not an arbitrary URL or a substring test.
    if id.is_empty() || id.len() > 128 || !id.bytes().all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b)) {
        bail!("invalid submitted job id");
    }
    Ok(id.to_owned())
}

async fn route_job(args: &Args, call: Arc<Call>) -> Result<()> {
    call.evidence.lock().unwrap()["kind"] = json!("job");
    let mut request = call.request.clone();
    let mut steps = Vec::new();
    let mut id = None;
    let mut done_digest = None;
    let mut retained_peak = 0;
    // Submit once. Up to eight polls, each on a new witnessed connection, then fetch.
    for n in 0..10 {
        if Instant::now() >= call.deadline { bail!("job evidence deadline exceeded; no repeat"); }
        let is_fetch = request.path.ends_with("/result");
        let step_call = Arc::new(Call {
            id:call.id.clone(), request:request.clone(), key:call.key.clone(),
            delivery:call.delivery.clone(), capture:Some(Mutex::new(None)), stream:false,
            deadline:call.deadline, start:call.start,
            evidence:Mutex::new(json!({"v":1,"state":"pending","receipt_id":call.id,"step":n+1})),
            // Journal the current credential at the parent: startup recovery can retire it.
            dir:call.dir.clone(),
        });
        let dir = call.dir.join(format!("step-{}", n+1));
        record::ensure_dir(&dir)?;
        let result = crate::prover::router_session(&prover_args(args,dir,args.witness[0].clone()),step_call.clone()).await;
        let evidence = step_call.evidence.lock().unwrap().clone();
        if let Some(cleanup) = evidence.get("credential_cleanup") {
            call.evidence.lock().unwrap()["credential_cleanup"] = cleanup.clone();
        }
        let retry = result?;
        if retry || evidence.get("receipt").is_none() {
            bail!("job step {} unverified: {}; no automatic repeat",n+1,evidence["reason"].as_str().unwrap_or("witness unavailable"));
        }
        let response = step_call.capture.as_ref().unwrap().lock().unwrap().take().ok_or_else(|| anyhow!("job response missing"))?;
        let mut step = json!({"receipt":evidence["receipt"],"operator_statement":evidence["operator_statement"],
            "request_hex":hex::encode(request_wire(&request))});
        if !is_fetch { step["response_hex"] = json!(hex::encode(response_wire(&response,&call.id))); }
        // Keep completed evidence as byte buffers between sessions, so retained
        // buffer capacity is measurable independently of JSON object overhead.
        steps.push(record::canonical_bytes(&step));
        let held = steps.iter().map(Vec::len).sum::<usize>() + steps.len() + 1;
        let allocated = steps.iter().map(Vec::capacity).sum::<usize>()
            + steps.capacity() * std::mem::size_of::<Vec<u8>>();
        retained_peak = retained_peak.max(allocated);
        persist(call.dir.join("retention.json"),json!({"completed_steps":steps.len(),"pending_chain_encoded_bytes":held,
            "retained_evidence_buffer_capacity_bytes":allocated,"peak_retained_evidence_buffer_capacity_bytes":retained_peak,
            "router_peak_rss_mib":record::peak_rss_mb(),
            "scope":"completed evidence byte buffers plus outer vector storage; active session, original client request and transient copies included in process RSS"})).await?;
        if n == 0 {
            if response.status != 201 { bail!("submit failed"); }
            id = Some(job_id(&response.body)?);
        } else if is_fetch {
            if response.status != 200 { bail!("fetch failed"); }
            let digest_matches = done_digest.as_deref() == Some(record::sha256_hex(&response.body).as_str());
            // The upstream bytes are delivered even if the cross-session digest fails.
            call.deliver(response).await;
            let decoded = steps.iter().map(|b| evidence_json(b)).collect::<Result<Vec<_>>>()?;
            if !digest_matches {
                persist(call.dir.join("rejected-chain.json"), json!(decoded)).await?;
                bail!("result digest mismatch: fetched body differs from witnessed done digest");
            }
            call.evidence.lock().unwrap()["chain"] = json!(decoded);
            return Ok(());
        } else {
            let poll = evidence_json(&response.body)?;
            if response.status != 200 { bail!("poll failed"); }
            match poll["state"].as_str() {
                Some("done") => {
                    done_digest = Some(poll["digest"].as_str().ok_or_else(|| anyhow!("done poll omitted digest"))?.to_owned());
                    request.path = format!("/jobs/{}/result",id.as_ref().unwrap());
                    continue;
                }
                Some("pending") if n < 8 => {},
                _ => bail!("poll not done within bounded attempts"),
            }
        }
        request.method = "GET".into();
        request.path = format!("/jobs/{}/poll",id.as_ref().unwrap());
        request.raw_body = Some(Vec::new());
        request.ordered_headers = Vec::new();
        // Avoid busy polling; time spent proving/retiring usually exceeds fixture readiness.
        tokio::time::sleep(Duration::from_millis(100)).await;
    }
    bail!("job step limit exceeded")
}

fn check_chain(evidence: &Value, request: &[u8], response: &[u8], trust: &Value) -> Value {
    let mut link = "evidence".to_owned();
    let mut label = Value::Null;
    let mut time = Value::Null;
    let mut profile = Value::Null;
    let result: Result<()> = (|| {
        if evidence["v"] != 1 { bail!("unsupported job evidence version"); }
        let steps = evidence["chain"].as_array().filter(|s| (3..=10).contains(&s.len())).ok_or_else(|| anyhow!("job needs submit, polls and fetch"))?;
        let mut id = String::new();
        let mut done_digest = None;
        let mut sessions = BTreeSet::new();
        for (i, step) in steps.iter().enumerate() {
            let final_step = i+1 == steps.len();
            link = "evidence".into();
            let req = if i == 0 { request.to_vec() } else {
                hex::decode(step["request_hex"].as_str().ok_or_else(|| anyhow!("missing request_hex"))?)?
            };
            let res = if final_step { response.to_vec() } else {
                hex::decode(step["response_hex"].as_str().ok_or_else(|| anyhow!("missing response_hex"))?)?
            };
            // Authenticate first. The per-step policy pins the common host; the
            // protocol below then pins the exact request targets to submit's body.
            let mut policy = trust.clone();
            if i > 0 { policy["path"] = step["receipt"]["record"]["request"]["path"].clone(); }
            let part = json!({"v":1,"state":"verified","receipt_id":step["receipt"]["record"]["job_id"],
                "witness_key_id":step["receipt"]["verdict"]["verifier_pub"],
                "receipt":step["receipt"],"operator_statement":step["operator_statement"]});
            let checked = check_exchange(&part,&Ok(req.clone()),&Ok(res.clone()),&Ok(policy));
            label = checked["witness_label"].clone();
            profile = checked["profile"].clone();
            if checked["result"] != "PASS" {
                link = checked["link"].as_str().unwrap_or("evidence").to_owned();
                // Map to static names because checked is local to this iteration.
                return Err(anyhow!("step {}: {}: {}",i+1,link,checked["reason"]));
            }
            time = checked["witness_time"].clone();
            link = "job_link".into();
            if part["receipt_id"] != evidence["receipt_id"] { bail!("step {} belongs to another receipt",i+1); }
            let session = step["receipt"]["verdict"]["session_id"].as_str().unwrap_or_default();
            if !sessions.insert(session) { bail!("steps reuse a witnessed TLS session"); }
            let (parsed,_) = client_request(&req,false)?.ok_or_else(|| anyhow!("incomplete step request"))?;
            let (received,_) = http::parse_response_at(strip_continue(&res),true)?;
            if i == 0 {
                if parsed.method != "POST" || parsed.target != "/jobs" || received.status != 201 { bail!("invalid submit"); }
                id = job_id(&received.body)?;
            } else {
                let target = format!("/jobs/{id}/{}",if final_step {"result"} else {"poll"});
                if parsed.method != "GET" || parsed.target != target || !parsed.body.is_empty() || received.status != 200 {
                    bail!("step {} target/status does not carry submitted job id",i+1);
                }
                if final_step {
                    link = "result_digest".into();
                    if done_digest.as_deref() != Some(record::sha256_hex(&received.body).as_str()) { bail!("fetched body differs from witnessed done digest"); }
                } else {
                    let poll = evidence_json(&received.body)?;
                    let last_poll = i+2 == steps.len();
                    if poll["state"] == "done" && last_poll {
                        done_digest = Some(poll["digest"].as_str().ok_or_else(|| anyhow!("done omitted digest"))?.to_owned());
                    } else if poll["state"] != "pending" || last_poll { bail!("invalid poll progression"); }
                }
            }
        }
        Ok(())
    })();
    match result {
        Ok(()) => json!({"result":"PASS","witness_label":label,"witness_time":time,"profile":profile}),
        Err(e) => json!({"result":"FAIL","link":link,"reason":format!("{e:#}"),"witness_label":label,"profile":profile}),
    }
}

#[derive(serde::Deserialize)]
#[serde(deny_unknown_fields)]
struct TrustList {
    v: u32,
    witnesses: Vec<TrustedWitness>,
    operators: Vec<String>,
    server_name: String,
    path: String,
}
#[derive(serde::Deserialize)]
#[serde(deny_unknown_fields)]
struct TrustedWitness {
    label: String,
    public_key: String,
    profiles: Vec<Profile>,
}

/// Router form of the offline checker. Pending/malformed evidence is never UNVERIFIED.
pub fn check(args: &crate::CheckArgs) -> Result<bool> {
    let result: Result<Value> = (|| {
        let evidence = evidence_json(&fs::read(args.evidence.as_ref().unwrap())?)?;
        let read = |path: &Option<PathBuf>, name: &str| -> Result<Vec<u8>> {
            Ok(fs::read(path.as_ref().ok_or_else(|| anyhow!("{name} required"))?)?)
        };
        let request = read(&args.client_request,"client-request");
        let response = read(&args.client_response,"client-response");
        let trust = read(&args.trust_list,"trust-list").and_then(|b| evidence_json(&b));
        Ok(if evidence["kind"] == "job" && evidence["state"] == "verified" {
            check_chain(&evidence, request.as_ref().map_err(|e|anyhow!("{e:#}"))?, response.as_ref().map_err(|e|anyhow!("{e:#}"))?, trust.as_ref().map_err(|e|anyhow!("{e:#}"))?)
        } else { check_exchange(&evidence, &request, &response, &trust) })
    })();
    let report = result.unwrap_or_else(|e| json!({"result":"FAIL","link":"evidence","reason":format!("{e:#}"),"witness_label":null,"profile":null}));
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(report["result"] == "PASS")
}

fn check_exchange(evidence: &Value, request_input: &Result<Vec<u8>>, response_input: &Result<Vec<u8>>, trust_value: &Result<Value>) -> Value {
    let mut label = None;
    let mut witness_time = None;
    let mut profile = None;
    let mut link = "evidence";
    let outcome: Result<&str> = (|| {

        if evidence["v"] != 1 {
            bail!("unsupported evidence version");
        }
        let response_raw = response_input.as_ref().map_err(|e|anyhow!("{e:#}"))?;
        let response_raw = strip_continue(response_raw);
        link = "receipt_match";
        let mut headers = [httparse::EMPTY_HEADER; 64];
        let mut response_head = httparse::Response::new(&mut headers);
        if !response_head.parse(response_raw)?.is_complete() {
            bail!("incomplete retained response head");
        }
        for header in response_head.headers.iter() {
            std::str::from_utf8(header.value)?;
        }
        let ids: Vec<_> = response_head
            .headers
            .iter()
            .filter(|h| h.name.eq_ignore_ascii_case(RECEIPT))
            .collect();
        if ids.len() != 1 {
            bail!("retained response must have one receipt id");
        }
        let id = std::str::from_utf8(ids[0].value)?;
        link = "receipt_match";
        if evidence["receipt_id"] != id {
            bail!("evidence is for another receipt");
        }
        link = "evidence";
        match evidence["state"].as_str() {
            Some("unverified") if evidence.get("receipt").is_none() => return Ok("UNVERIFIED"),
            Some("verified") => {}
            Some("pending") => {
                link = "evidence_pending";
                bail!("evidence is still pending; retrieve it after completion");
            }
            _ => bail!("invalid evidence state"),
        }
        link = "inclusion";
        let receipt: Receipt = serde_json::from_value(evidence["receipt"].clone())?;
        let verdict: Verdict = serde_json::from_value(receipt.verdict.clone())?;
        if receipt.v != 1 || verdict.v != 5 {
            bail!("unsupported receipt or verdict version");
        }
        let ex = &receipt.record;
        let index =
            ex.n.checked_sub(1)
                .ok_or_else(|| anyhow!("invalid exchange index"))?;
        let path = receipt
            .path
            .iter()
            .map(|h| crate::merkle::from_hex(h))
            .collect::<Result<Vec<_>>>()?;
        if hex::encode(crate::merkle::root_from_path(
            crate::merkle::from_hex(&record::sha256_hex(&record::canonical_bytes(
                &evidence["receipt"]["record"],
            )))?,
            index,
            verdict.exchanges,
            &path,
        )?) != verdict.root
            || ex.outcome != "verified"
        {
            bail!("exchange inclusion failed");
        }
        link = "witness_signature";
        record::verify_signature(&receipt.verdict, "verifier_pub")?;
        let trust: TrustList = serde_json::from_value(trust_value.as_ref().map_err(|e|anyhow!("{e:#}"))?.clone())?;
        if trust.v != 1 || evidence["witness_key_id"] != verdict.verifier_pub {
            bail!("invalid trust version or witness identifier");
        }
        let mut accepted_profiles = None;
        for entry in &trust.witnesses {
            if entry.public_key == verdict.verifier_pub {
                label = Some(entry.label.clone());
                accepted_profiles = Some(&entry.profiles);
            }
        }
        if label.is_none() {
            bail!("witness key is not permitted");
        }
        profile = Some(verdict.profile);
        link = "session";
        witness_timestamp(&verdict.verified_at)?;
        if ex.session_id != verdict.session_id
            || !accepted_profiles.unwrap().contains(&verdict.profile)
        {
            bail!("session identity or accepted profile differs");
        }
        match (verdict.profile, &ex.request.withheld) {
            (Profile::CredentialHidden, Some(w)) if w.start < w.end && matches!(w.header.as_str(), "authorization" | "x-api-key") && crate::zk::known(&w.no_cr_lf) => {},
            (Profile::FullDisclosureFixture | Profile::CredentialSequence, None) => {},
            _ => bail!("profile and credential disclosure proof differ"),
        }
        link = "receipt_match";
        if ex.job_id != id {
            bail!("receipt id differs from witnessed job");
        }
        link = "operator_identity";
        let statement = &evidence["operator_statement"];
        record::verify_signature(statement, "operator_pub")?;
        if !trust
            .operators
            .iter()
            .any(|key| ex.operator_pub.as_ref() == Some(key) && statement["operator_pub"] == *key)
            || ex.operator_statement_sha256.as_deref()
                != Some(record::sha256_hex(&record::canonical_bytes(statement)).as_str())
        {
            bail!("operator identity or statement hash differs");
        }
        let expected_fields = json!({"session_id":ex.session_id,"receipt_id":ex.job_id,"method":ex.request.method,"host":ex.request.host,"path":ex.request.path,
            "body_sha256":ex.request.body_sha256,"body_bytes":ex.request.body_bytes,"forwarded_headers_sha256":ex.request.forwarded_headers_sha256});
        for (k, v) in expected_fields.as_object().unwrap() {
            if statement[k] != *v {
                bail!("operator statement {k} differs");
            }
        }
        link = "destination";
        if verdict.server_name != trust.server_name
            || ex.request.host != trust.server_name
            || ex.request.path != trust.path
        {
            bail!("host or request target differs");
        }
        link = "request_match";
        let raw = request_input.as_ref().map_err(|e|anyhow!("{e:#}"))?;
        let (request, used) =
            client_request(&raw, false)?.ok_or_else(|| anyhow!("incomplete retained request"))?;
        if used != raw.len()
            || request.method != ex.request.method
            || request.target != ex.request.path
            || record::sha256_hex(&request.body) != ex.request.body_sha256
            || request.body.len() != ex.request.body_bytes
        {
            bail!("retained request differs");
        }
        link = "forwarded_headers";
        if http::forwarded_hash(&request.headers) != ex.request.forwarded_headers_sha256 {
            bail!("forwarded client header set differs");
        }
        link = "response_delivery";
        let raw = response_raw;
        let raw = strip_continue(&raw);
        let (response, used) = http::parse_response_at(raw, true)?;
        if used != raw.len()
            || response.status != ex.response.status
            || response.content_type != ex.response.content_type
            || response.body.len() != ex.response.body_bytes
            || record::sha256_hex(&response.body) != ex.response.body_sha256
        {
            bail!("delivered response differs");
        }
        link = "receipt_match";
        let mut headers = [httparse::EMPTY_HEADER; 64];
        let mut resp = httparse::Response::new(&mut headers);
        resp.parse(raw)?;
        let ids: Vec<_> = resp
            .headers
            .iter()
            .filter(|h| h.name.eq_ignore_ascii_case(RECEIPT))
            .collect();
        if ids.len() != 1 || ids[0].value != id.as_bytes() {
            bail!("retained response receipt differs");
        }
        witness_time = Some(verdict.verified_at);
        Ok("PASS")
    })();
    let mut report = match &outcome {
        Ok("PASS") => json!({"result":"PASS","witness_label":label,"witness_time":witness_time}),
        Ok(result) => json!({"result":result,"witness_label":label}),
        Err(e) => {
            json!({"result":"FAIL","link":link,"reason":format!("{e:#}"),"witness_label":label})
        }
    };
    report["profile"] = json!(profile);
    report
}

fn strip_continue(mut raw: &[u8]) -> &[u8] {
    while raw.starts_with(b"HTTP/1.1 100 ") {
        match raw.windows(4).position(|w| w == b"\r\n\r\n") {
            Some(n) => raw = &raw[n + 4..],
            None => break,
        }
    }
    raw
}

// The interchange canonical form deliberately supports integers only.
fn evidence_json(raw: &[u8]) -> Result<Value> {
    fn integers(value: &Value) -> bool {
        match value {
            Value::Number(n) => n.is_i64() || n.is_u64(),
            Value::Array(a) => a.iter().all(integers),
            Value::Object(o) => o.values().all(integers),
            _ => true,
        }
    }
    let value = serde_json::from_slice(raw)?;
    if !integers(&value) {
        bail!("evidence JSON numbers must be integers in the supported range");
    }
    Ok(value)
}

fn witness_timestamp(value: &str) -> Result<()> {
    if !value.is_ascii() || value.as_bytes().get(10) != Some(&b'T') {
        bail!("verified_at requires RFC3339 with a literal T separator");
    }
    chrono::DateTime::parse_from_rfc3339(value)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    async fn test_call(port: u16) -> (Call, TcpStream) {
        let listener = TcpListener::bind(("127.0.0.1", port)).await.unwrap();
        let client = TcpStream::connect(listener.local_addr().unwrap()).await.unwrap();
        let (tcp, _) = listener.accept().await.unwrap();
        let dir = std::env::temp_dir().join(format!("tlsw-ch-witness-stream-{}", hex::encode(record::random_bytes::<8>().unwrap())));
        record::ensure_dir(&dir).unwrap();
        let start = Instant::now();
        let call = Call { id:"test-stream".into(), key:SigningKey::from_bytes(&[7;32]),
            request:http::RequestFile {method:"POST".into(),host:"test-server.io".into(),path:"/".into(),headers:BTreeMap::new(),ordered_headers:Vec::new(),raw_body:Some(br#"{"stream":true}"#.to_vec()),body:None},
            delivery:Arc::new(tokio::sync::Mutex::new(Delivery {tcp,head_sent:false,body_seen:0,accepted:0,accepted_hash:Sha256::new(),wire_at:0,chunked:false,chunk_left:0,chunk_crlf:false,stream_done:false,complete:false,disconnected:false,cancelled:false,first_ms:None,total_ms:None})),
            capture:None,stream:true,deadline:start + Duration::from_secs(10),start,evidence:Mutex::new(json!({"state":"pending"})),dir };
        (call, client)
    }

    #[tokio::test]
    async fn terminal_evidence_preserves_session_failure_causes() {
        for reason in ["evidence deadline exceeded; routing future cancelled", "witness dropped mid-stream"] {
            let (call, _client) = test_call(18980).await;
            call.failure(reason);
            call.finish("no witness evidence").await;
            let evidence: Value = serde_json::from_slice(&fs::read(call.dir.join("evidence.json")).unwrap()).unwrap();
            assert_eq!(evidence["reason"], reason);
            assert_eq!(evidence["state"], "unverified");
        }
    }

    #[tokio::test]
    async fn recovery_resolves_pending_outside_current_admission_log() {
        let (call, _client) = test_call(18981).await;
        let log = call.dir.join("admissions.jsonl");
        fs::write(&log, b"{\"receipt_id\":\"logged\"}\n{torn").unwrap();
        let orphan = call.dir.join("orphan");
        record::ensure_dir(&orphan).unwrap();
        durable_json(&orphan.join("evidence.json"), &json!({"v":1,"receipt_id":"orphan","state":"pending"})).unwrap();
        let mut args = Args::try_parse_from(["router", "--profile", "credential-sequence", "--witness", "127.0.0.1:1", "--operator-key", "unused", "--host", "test-server.io", "--obtain-request", "unused", "--revoke-request", "unused"]).unwrap();
        args.record_dir = call.dir.clone();
        recover_pending(&args, &log).await.unwrap();
        admit(&log, "next").unwrap();
        assert_eq!(admitted(&log).unwrap(), vec!["logged", "next"]);
        let evidence: Value = serde_json::from_slice(&fs::read(orphan.join("evidence.json")).unwrap()).unwrap();
        assert_eq!(evidence["state"], "unverified");
        assert!(evidence["reason"].as_str().unwrap().contains("restarted"));
        assert_eq!(evidence["credential_cleanup"]["state"], "unknown");
    }

    #[test]
    fn admission_tolerates_only_unterminated_final_line() {
        let dir = std::env::temp_dir().join(format!("tlsw-ch-witness-torn-{}",hex::encode(record::random_bytes::<8>().unwrap())));
        record::ensure_dir(&dir).unwrap();
        let log = dir.join("admissions.jsonl");
        for tail in [b"{broken".as_slice(), br#"{"receipt_id":"not-admitted"}"#] {
            fs::write(&log, [b"{\"receipt_id\":\"first\"}\n".as_slice(), tail].concat()).unwrap();
            assert_eq!(admitted(&log).unwrap(), vec!["first"]);
        }
        fs::write(&log, b"{broken\n{\"receipt_id\":\"second\"}\n").unwrap();
        assert!(admitted(&log).is_err());
    }

    #[tokio::test]
    async fn streamed_body_reaches_socket_before_complete_and_preserves_comments() {
        let (call, mut client) = test_call(18982).await;
        let prefix = b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nTransfer-Encoding: chunked\r\n\r\n5;ext=yes\r\n: hi\n\r\n";
        call.stream_update(prefix).await.unwrap();
        let mut buf = [0;1024];
        let n = tokio::time::timeout(Duration::from_secs(1),client.read(&mut buf)).await.unwrap().unwrap();
        assert!(buf[..n].windows(5).any(|b| b == b": hi\n"));
        assert!(!call.delivery.lock().await.complete);
        let full = [prefix.as_slice(),b"3\r\nx\n\n\r\n0\r\nTrailer: ignored\r\n\r\n"].concat();
        for n in prefix.len()+1..=full.len() { call.stream_update(&full[..n]).await.unwrap(); }
        call.deliver(http::parse_response_at(&full,true).unwrap().0).await;
        let mut raw = buf[..n].to_vec();
        client.read_to_end(&mut raw).await.unwrap();
        let (parsed,used) = http::parse_response_at(&raw,true).unwrap();
        assert_eq!(parsed.body,b": hi\nx\n\n");
        assert_eq!(used,raw.len());
        assert!(call.delivery.lock().await.complete);
        assert_eq!(call.delivery.lock().await.facts()["socket_accepted_body_sha256"],record::sha256_hex(&parsed.body));
    }

    #[tokio::test]
    async fn many_small_stream_chunks_have_bounded_cost() {
        let (call, mut client) = test_call(18983).await;
        let reader = tokio::spawn(async move { let mut raw=Vec::new(); client.read_to_end(&mut raw).await.unwrap(); raw });
        let mut raw=b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nTransfer-Encoding: chunked\r\n\r\n".to_vec();
        let mut batches=Vec::new();
        for _ in 0..4 {
            let tick=Instant::now();
            for _ in 0..500 { raw.extend_from_slice(b"5;ext=yes\r\n: hi\n\r\n"); call.stream_update(&raw).await.unwrap(); }
            batches.push(tick.elapsed().as_micros() as u64);
        }
        raw.extend_from_slice(b"0\r\n\r\n");
        call.stream_update(&raw).await.unwrap();
        call.deliver(http::parse_response_at(&raw,true).unwrap().0).await;
        let delivered=reader.await.unwrap();
        assert_eq!(http::parse_response_at(&delivered,true).unwrap().0.body, b": hi\n".repeat(2000));
        println!("STREAM_COST {}",json!({"chunks":2000,"chunks_per_batch":500,"batch_us":batches,"total_us":batches.iter().sum::<u64>()}));
    }

    #[test]
    fn admission_log_retains_each_id_and_reconciliation_reports_missing() {
        let dir = std::env::temp_dir().join(format!("tlsw-ch-witness-admission-{}",hex::encode(record::random_bytes::<8>().unwrap())));
        record::ensure_dir(&dir).unwrap();
        let log = dir.join("admissions.jsonl");
        admit(&log,"first").unwrap();
        admit(&log,"second").unwrap();
        assert_eq!(admitted(&log).unwrap(),vec!["first","second"]);
        assert!(!reconcile(ReconcileArgs {admission_log:log.clone(),record_dir:dir.clone()}).unwrap());
        for id in ["first","second"] {
            record::ensure_dir(&dir.join(id)).unwrap();
            durable_json(&dir.join(id).join("evidence.json"),&json!({"receipt_id":id,"state":"unverified"})).unwrap();
        }
        assert!(reconcile(ReconcileArgs {admission_log:log,record_dir:dir}).unwrap());
    }

    #[test]
    fn timestamp_grammar() {
        for good in [
            "2026-11-02T10:17:06Z",
            "2026-11-02T10:17:06.5+02:00",
            "2026-11-02T10:17:60z",
        ] {
            assert!(witness_timestamp(good).is_ok(), "{good}");
        }
        for bad in [
            "2026-11-02 10:17:06Z",
            "2026-11-02t10:17:06Z",
            "2026-02-30T10:17:06Z",
            "2026-11-02T10:17:06",
            "2026-11-02T10:17:06−02:00",
        ] {
            assert!(witness_timestamp(bad).is_err(), "{bad}");
        }
    }
    #[test]
    fn required_nullable_content_type() {
        let mut package: Value =
            serde_json::from_str(include_str!("../samples/evidence/normal-a/package.json"))
                .unwrap();
        package["receipt"]["record"]["response"]["content_type"] = Value::Null;
        assert!(serde_json::from_value::<Receipt>(package["receipt"].clone()).is_ok());
        package["receipt"]["record"]["response"]
            .as_object_mut()
            .unwrap()
            .remove("content_type");
        assert!(serde_json::from_value::<Receipt>(package["receipt"].clone()).is_err());
    }
    #[test]
    fn integer_json_only() {
        assert!(evidence_json(br#"{"x":-1,"x":2}"#).is_ok());
        for bad in [
            br#"{"x":1.0}"#.as_slice(),
            br#"{"x":1e2}"#,
            br#"{"x":18446744073709551616}"#,
            br#"{"x":"\ud800"}"#,
        ] {
            assert!(evidence_json(bad).is_err());
        }
    }
}
