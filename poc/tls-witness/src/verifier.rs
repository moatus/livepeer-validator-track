//! Verifier: serves witnessed sessions, each as its own task, up to
//! `--max-sessions` at once; past that a connection is refused at its commit,
//! with a readable error and no upstream connection, and closed if it sends
//! no commit within 10 s. At most 16 refusals are pending at once; a
//! connection past that is closed unread. Enforces its cap policy,
//! validates the server identity against its own roots, parses the revealed
//! HTTP as one or more requests and their responses, requires every request's
//! credential header value, and nothing else, withheld, and one proof that the
//! withheld values hold no CR or LF, signs one verdict for the session over
//! the Merkle root of its exchange records, and sends both back over the same
//! connection. Every session's record is on disk from its start, so one the
//! process did not live to finish is found at the next start; and every
//! `--epoch-secs` the verifier signs a report over the sessions that ended in
//! that period, from those records.

use std::{
    fs,
    net::SocketAddr,
    ops::Range,
    path::PathBuf,
    sync::{
        Arc, Mutex,
        atomic::{AtomicU64, AtomicUsize, Ordering},
    },
    time::Duration,
    time::Instant,
};

use anyhow::{Context, Result, anyhow, bail};
use ed25519_dalek::SigningKey;
use serde_json::{Map, Value, json};
use tlsn::{
    Session, SessionHandle,
    config::verifier::VerifierConfig,
    connection::ServerName,
    hash::HashAlgId,
    transcript::{Direction, TranscriptCommitment},
    verifier::{VerifierCommitStart, VerifierOutput},
    webpki::RootCertStore,
};
use tokio::{
    io::AsyncRead,
    net::{TcpListener, TcpStream},
};
use tokio_util::compat::TokioAsyncReadCompatExt;

use crate::{
    Profile, VerifierArgs, epoch, http,
    io::{
        AbortOnDrop, Counters, Counting, HelloTap, LazyUpstream, RecordCap, RecordTap,
        connect_upstream, process_facts, read_frame, server_hello, step, write_frame,
    },
    merkle,
    record::{
        Bytes, ExchangeRecord, Limits, Marks, Resources, RunRecord, Timings, Verdict, VerdictImage,
        VerdictRequest, VerdictResponse, Withheld, cpu_seconds, describe, ensure_dir,
        load_or_create_key, ms, now_ms_rfc3339, now_rfc3339, peak_rss_mb, phase_of, random_bytes,
        reset_peak_rss, sha256_hex, sign, write_json, write_json_atomic,
    },
    stop::{self, StopAt},
    zk,
};

/// A session that has not finished by then is abandoned.
const SESSION_LIMIT: Duration = Duration::from_secs(600);
/// A refused connection gets this long to send its commit and take the
/// refusal; one that stays silent is closed, so it cannot hold its place.
/// Cooperative refusals take well under 1 s.
const REFUSAL_LIMIT: Duration = Duration::from_secs(10);
/// Refusals pending at once. Each holds a tlsn session, which starts one
/// executor thread per core, so a connection past this is closed unread.
const REFUSALS_PENDING: usize = 16;

struct Ctx {
    args: VerifierArgs,
    key: SigningKey,
    roots: RootCertStore,
    roots_about: Value,
    /// Bounded lazy cache of the selected built-in verification keys.
    circuits: Option<Arc<zk::Keys>>,
    zk_about: Value,
    /// --threads and what it set.
    threads: Value,
    /// Admitted sessions not yet finished.
    in_flight: AtomicUsize,
    /// Sessions admitted since startup.
    admitted: AtomicU64,
    /// Refused connections not yet closed.
    refusing: AtomicUsize,
}

/// A new session's id: when it started, and three random bytes.
fn session_id() -> String {
    format!(
        "{}-{}",
        chrono::Utc::now().format("%Y%m%dT%H%M%SZ"),
        hex::encode(random_bytes::<3>().unwrap_or_default())
    )
}

/// A connection's place, as an admitted session under `--max-sessions` or a
/// pending refusal under `REFUSALS_PENDING`, given back when its task ends,
/// however it ends.
struct Slot {
    ctx: Arc<Ctx>,
    admitted: bool,
}

impl Drop for Slot {
    fn drop(&mut self) {
        let count = if self.admitted {
            &self.ctx.in_flight
        } else {
            &self.ctx.refusing
        };
        count.fetch_sub(1, Ordering::Relaxed);
    }
}

#[derive(Default)]
struct State {
    mode: Option<&'static str>,
    /// Refused at the commit: at capacity, or asking for caps past policy.
    refused: bool,
    /// The connection to the server ran to its end, so the prover had every
    /// response.
    connection_done: bool,
    limits: Option<Limits>,
    proxy_name: Option<String>,
    host: Option<String>,
    job_id: Option<String>,
    counters: Counters,
    // Socket counts survive upstream/protocol failure for sizing records.
    upstream_counters: Counters,
    timings: Timings,
    request_body: Option<usize>,
    response_body: Option<usize>,
    upstream_called: bool,
    exchanges: Vec<Value>,
    marks: Option<Marks>,
    detail: Map<String, Value>,
    operator_statement: Option<Value>,
    admitted_name: Option<String>,
}

impl State {
    fn mark(&mut self, at: &str) {
        if let Some(marks) = self.marks.as_mut() {
            marks.mark(at);
        }
    }
}

pub async fn run(args: VerifierArgs, pinned: Option<crate::io::Pinned>) -> Result<()> {
    if args.max_sessions == 0 {
        bail!("--max-sessions must be at least 1");
    }
    // The stop note and the MPC event watch track one session at a time.
    if args.stop_at.is_some() && args.max_sessions != 1 {
        bail!("--stop-at needs --max-sessions 1");
    }
    if args.epoch_secs == 0 {
        bail!("--epoch-secs must be at least 1");
    }
    ensure_dir(&args.record_dir)?;
    let key = load_or_create_key(&args.key)?;
    // Sessions a stopped process left open are closed before any new one
    // starts, so an epoch counts each of them once.
    for id in epoch::close_interrupted(&args.record_dir)? {
        println!("session {id}: interrupted: found open at startup");
    }
    let (roots, roots_about) = crate::roots(&args.roots)?;
    let listener = TcpListener::bind(&args.listen)
        .await
        .with_context(|| format!("listening on {}", args.listen))?;
    println!(
        "verifier listening on {} pub {}",
        listener.local_addr()?,
        hex::encode(key.verifying_key().as_bytes())
    );
    let (circuits, zk_about) = if args.profile == Profile::CredentialHidden {
        let keys = Arc::new(zk::Keys::new(&args.srs)?);
        let about = keys.about();
        (Some(keys), about)
    } else {
        (None, json!({ "skipped": "revealed credential" }))
    };
    println!("profile: {}", args.profile.as_str());
    println!("no-CR/LF circuits loaded: {zk_about}");
    if let Some(at) = stop::configured() {
        println!("stop at: {}", at.as_str());
    }
    let threads = threads(&args, pinned.as_ref());
    match (args.threads, &pinned) {
        (Some(n), Some(p)) => println!(
            "threads: {n} per pool (tlsn executor per session {n}, runtime workers {n}, RAYON_NUM_THREADS={}, HARDWARE_CONCURRENCY={}); pinned to CPUs {} ({}; {} CPUs allowed)",
            threads["rayon_num_threads"].as_str().unwrap_or("-"),
            threads["hardware_concurrency"].as_str().unwrap_or("-"),
            if p.cpus.is_empty() {
                "none".to_string()
            } else {
                crate::io::cpu_list(&p.cpus)
            },
            p.how,
            p.allowed.map_or("unknown".to_string(), |a| a.to_string()),
        ),
        _ => println!(
            "threads: not bounded, not pinned; {} CPUs available",
            threads["available_cpus"]
        ),
    }
    println!("max sessions: {}", args.max_sessions);
    println!("epoch: {} s", args.epoch_secs);
    write_json(&args.record_dir.join("startup.json"), &json!({
        "cpu_seconds": cpu_seconds(), "peak_rss_mb": peak_rss_mb(),
        "cgroup_caps": crate::record::cgroup_caps(), "threads": threads,
        "zk": zk_about, "profile": args.profile,
    }))?;
    let ctx = Arc::new(Ctx {
        args,
        key,
        roots,
        roots_about,
        circuits,
        zk_about,
        threads,
        in_flight: AtomicUsize::new(0),
        admitted: AtomicU64::new(0),
        refusing: AtomicUsize::new(0),
    });
    let next = epoch::catch_up(&ctx.args.record_dir, ctx.args.epoch_secs, &ctx.key)?;
    tokio::spawn(epoch::every(
        ctx.args.record_dir.clone(),
        ctx.args.epoch_secs,
        ctx.key.clone(),
        next,
    ));
    loop {
        match listener.accept().await {
            Ok((tcp, peer)) => {
                // Only this loop admits, so the count can only fall between
                // the check and the increment.
                let in_flight = ctx.in_flight.load(Ordering::Relaxed);
                let max = ctx.args.max_sessions;
                let admitted = in_flight < max;
                if admitted {
                    ctx.in_flight.fetch_add(1, Ordering::Relaxed);
                    ctx.admitted.fetch_add(1, Ordering::Relaxed);
                } else if ctx.refusing.load(Ordering::Relaxed) < REFUSALS_PENDING {
                    ctx.refusing.fetch_add(1, Ordering::Relaxed);
                } else {
                    let error =
                        format!("closed unread: {REFUSALS_PENDING} refusals already pending");
                    let id = session_id();
                    if let Err(e) = closed_unread(&ctx, &id, peer, &error) {
                        eprintln!("session {id}: {e:#}");
                    }
                    println!("session {id} from {peer}: refused: {error}");
                    continue;
                }
                let slot = Slot {
                    ctx: ctx.clone(),
                    admitted,
                };
                let refusal = (!admitted).then(|| {
                    format!("the witness is at capacity: {in_flight} sessions in flight, --max-sessions {max}")
                });
                let ctx = ctx.clone();
                tokio::spawn(async move {
                    session(&ctx, tcp, peer, refusal).await;
                    drop(slot);
                });
            }
            Err(e) => eprintln!("accept failed: {e}"),
        }
    }
}

/// --threads, the environment it set for the proof pools, the cores it
/// pinned the process to and how they were chosen, and the CPUs the process
/// may use.
fn threads(args: &VerifierArgs, pinned: Option<&crate::io::Pinned>) -> Value {
    json!({
        "setting": args.threads,
        "tlsn_executor_per_session": args.threads,
        "runtime_workers": args.threads,
        "rayon_num_threads": std::env::var("RAYON_NUM_THREADS").ok(),
        "hardware_concurrency": std::env::var("HARDWARE_CONCURRENCY").ok(),
        "pinned_cpus": pinned.map(|p| crate::io::cpu_list(&p.cpus)),
        "pinning": pinned.map(|p| p.how.clone()),
        "allowed_cpus_before_pinning": pinned.and_then(|p| p.allowed),
        "available_cpus": std::thread::available_parallelism().map(|n| n.get()).ok(),
    })
}

/// Process-wide figures when a session starts or ends. CPU time and peak RSS
/// come from getrusage and VmHWM for the whole process, so a session's own
/// share is known only when it ran alone.
fn process_now(ctx: &Ctx) -> Value {
    json!({
        "in_flight": ctx.in_flight.load(Ordering::Relaxed),
        "admitted": ctx.admitted.load(Ordering::Relaxed),
        "refusals_pending": ctx.refusing.load(Ordering::Relaxed),
        "cpu_seconds": (cpu_seconds() * 1000.0).round() / 1000.0,
        "peak_rss_mb": peak_rss_mb(),
    })
}

/// The record of a connection closed without being read, so it is counted.
fn closed_unread(ctx: &Ctx, id: &str, peer: SocketAddr, error: &str) -> Result<()> {
    let record = json!({
        "role": "verifier",
        "outcome": "refused",
        "error": error,
        "upstream_called": false,
        "started_at": now_rfc3339(),
        "recorded_at": now_ms_rfc3339(),
        "exchanges": [],
        "detail": { "session_id": id, "peer": peer.to_string(), "process": process_facts() },
    });
    write_json_atomic(
        &ctx.args.record_dir.join(format!("{id}.record.json")),
        &record,
    )?;
    Ok(())
}

/// Serves one connection; with `refusal` set, refuses it at the commit.
async fn session(ctx: &Ctx, tcp: TcpStream, peer: SocketAddr, refusal: Option<String>) {
    let started = Instant::now();
    let started_at = now_rfc3339();
    let session_id = session_id();
    let dir = &ctx.args.record_dir;
    let record_path = dir.join(format!("{session_id}.record.json"));
    // On disk until the session's own record replaces it; one still open
    // when the next process starts was cut off by the process stopping.
    let open = json!({
        "role": "verifier",
        "outcome": epoch::OPEN,
        "started_at": started_at,
        "exchanges": [],
        "detail": { "session_id": session_id, "peer": peer.to_string(), "process": process_facts() },
    });
    if let Err(e) = write_json_atomic(&record_path, &open) {
        eprintln!("session {session_id}: {e:#}");
    }
    let admitted = refusal.is_none();
    // Peak RSS is per process: it restarts only when no other session is in
    // flight, so it covers every session overlapping this one.
    if admitted && ctx.in_flight.load(Ordering::Relaxed) == 1 {
        reset_peak_rss();
    }
    let at_start = process_now(ctx);
    let cpu_start = cpu_seconds();
    let mut st = State {
        refused: !admitted,
        marks: Some(Marks::new(started)),
        ..State::default()
    };
    st.mark("session_start");
    if admitted {
        stop::begin(&session_id, &ctx.args.record_dir);
        stop::note("peer", json!(peer.to_string()));
    }

    let serving = serve(ctx, tcp, &session_id, &mut st, refusal.as_deref());
    let limit = if admitted {
        SESSION_LIMIT
    } else {
        REFUSAL_LIMIT
    };
    let result = match tokio::time::timeout(limit, serving).await {
        Ok(result) => result,
        Err(_) => Err(match &refusal {
            Some(msg) => anyhow!(
                "refused: {msg}; closed after {} s without completing the commit",
                limit.as_secs()
            ),
            None => anyhow!("session exceeded {} s and was abandoned", limit.as_secs()),
        }),
    };
    st.timings.total = Some(ms(started));

    let outcome = match &result {
        Ok(()) => "verified",
        Err(_) if st.refused => "refused",
        Err(_) if !st.upstream_called => "not_sent",
        Err(_) if st.connection_done => "unwitnessed",
        Err(_) => "aborted",
    };
    let error = result.as_ref().err().map(describe);
    // An exchange is verified only in a session whose verdict reached the
    // prover; one whose verdict was refused, or not delivered, is not.
    for ex in &mut st.exchanges {
        ex["outcome"] = json!(if outcome == "verified" {
            "verified"
        } else {
            "unwitnessed"
        });
    }
    if outcome != "verified" {
        st.detail.remove("session_root");
    }
    st.detail.insert("session_id".into(), json!(session_id));
    st.detail.insert("peer".into(), json!(peer.to_string()));
    st.detail
        .insert("proxy_server_name".into(), json!(st.proxy_name));
    st.detail.insert("roots".into(), ctx.roots_about.clone());
    st.detail.insert("process".into(), process_facts());
    st.detail.insert("socket_bytes".into(), json!({
        "upstream_sent": st.upstream_counters.written(),
        "upstream_received": st.upstream_counters.read(),
        "operator_to_witness": st.counters.read(),
        "witness_to_operator": st.counters.written(),
        "operator_to_witness_non_relay": st.counters.read().saturating_sub(st.upstream_counters.written()),
        "witness_to_operator_non_relay": st.counters.written().saturating_sub(st.upstream_counters.read()),
    }));
    st.detail.insert(
        "policy".into(),
        json!({ "max_sent": ctx.args.max_sent, "max_recv": ctx.args.max_recv }),
    );
    st.detail.insert(
        "verifier_pub".into(),
        json!(hex::encode(ctx.key.verifying_key().as_bytes())),
    );
    st.detail.insert("zk_startup".into(), ctx.zk_about.clone());
    st.detail.insert("threads".into(), ctx.threads.clone());
    st.mark("recorded");
    if let Some(marks) = st.marks.take() {
        st.detail.insert("cpu_marks".into(), marks.value());
    }
    let at_end = process_now(ctx);
    let ran_alone =
        admitted && at_start["in_flight"] == json!(1) && at_end["admitted"] == at_start["admitted"];
    st.detail.insert(
        "sessions".into(),
        json!({
            "max": ctx.args.max_sessions,
            "admitted": admitted,
            "ran_alone": ran_alone,
            "at_start": at_start,
            "at_end": at_end,
        }),
    );
    let record = RunRecord {
        role: "verifier",
        job_id: st.job_id,
        phase: phase_of(dir),
        label: None,
        mode: st.mode,
        prewarm: false,
        stream: false,
        host: st.host.or(st.proxy_name),
        limits: st.limits,
        timings_ms: st.timings,
        bytes: Bytes {
            to_verifier: st.counters.read(),
            from_verifier: st.counters.written(),
            request_body: st.request_body,
            response_body: st.response_body,
        },
        // Process-wide while this session was open: its own cost only when
        // `detail.sessions.ran_alone`.
        resources: Resources {
            peak_rss_mb: peak_rss_mb(),
            cpu_seconds: ((cpu_seconds() - cpu_start) * 1000.0).round() / 1000.0,
        },
        outcome,
        error: error.clone(),
        upstream_called: Some(st.upstream_called),
        rtt_to_verifier_ms: None,
        started_at,
        recorded_at: now_ms_rfc3339(),
        exchanges: st.exchanges,
        detail: Value::Object(st.detail),
    };
    if let Err(e) = write_json_atomic(&record_path, &record) {
        eprintln!("session {session_id}: {e:#}");
    }
    match error {
        None => println!("session {session_id} from {peer}: {outcome}"),
        Some(e) => println!("session {session_id} from {peer}: {outcome}: {e}"),
    }
}

/// Closes the session after a refusal, so the refusal reaches the prover.
async fn close_session<T>(handle: SessionHandle, driver: AbortOnDrop<T>) {
    handle.close();
    let _ = tokio::time::timeout(Duration::from_secs(5), driver).await;
}

async fn serve(
    ctx: &Ctx,
    tcp: TcpStream,
    session_id: &str,
    st: &mut State,
    refusal: Option<&str>,
) -> Result<()> {
    tcp.set_nodelay(true)?;
    let (mut socket, counters) = Counting::new(tcp);
    st.counters = counters;
    st.detail.insert("cgroup_caps".into(), crate::record::cgroup_caps());
    st.detail.insert(
        "profile".into(),
        json!(ctx.args.profile),
    );
    let requested =
        tokio::time::timeout(Duration::from_secs(10), read_frame(&mut socket, 256)).await??;
    let kind = ctx.args.profile.as_str().as_bytes();
    if requested != kind {
        st.refused = true;
        write_frame(&mut socket, b"refused: profile mismatch").await?;
        bail!(
            "profile mismatch: verifier requires {}",
            ctx.args.profile.as_str()
        );
    }
    write_frame(&mut socket, kind).await?;
    write_frame(&mut socket, session_id.as_bytes()).await?;
    let statement: Value = serde_json::from_slice(&read_frame(&mut socket, 16384).await?)?;
    if !statement.is_null() {
        let accepted = crate::router::verify_operator(&statement, session_id, &ctx.args.operator_pub);
        if let Err(error) = accepted {
            st.refused = true;
            write_frame(&mut socket, format!("refused: {error}").as_bytes()).await?;
            return Err(error);
        }
        st.operator_statement = Some(statement);
    }
    let name = String::from_utf8(read_frame(&mut socket, 256).await?)?;
    if !ctx.args.allow_server.contains(&name) {
        st.refused = true;
        write_frame(&mut socket, b"refused: server name is not on the upstream allowlist").await?;
        bail!("refused: server name is not on the upstream allowlist");
    }
    st.admitted_name = Some(name);
    write_frame(&mut socket, b"accepted").await?;
    let session = match ctx.args.threads {
        Some(n) => crate::io::with_cpus(n, || Session::new(socket.compat()))?,
        None => Session::new(socket.compat()),
    };
    let (driver, mut handle) = session.split();
    let mut driver = AbortOnDrop(tokio::spawn(driver));
    let config = VerifierConfig::builder()
        .root_store(ctx.roots.clone())
        .build()?;
    let verifier = handle.new_verifier(config)?;
    let policy = Limits {
        max_sent: ctx.args.max_sent,
        max_recv: ctx.args.max_recv,
    };

    if let Some(msg) = refusal {
        st.detail.insert("refused".into(), json!(msg));
    }
    let t = Instant::now();
    let start = step("receiving commit", verifier.commit(), &mut driver).await?;
    if let Some(msg) = refusal {
        match start {
            VerifierCommitStart::Mpc(verifier) => {
                st.mode = Some("mpc");
                step(
                    "refusing the session",
                    verifier.reject(Some(msg)),
                    &mut driver,
                )
                .await?;
            }
            VerifierCommitStart::Proxy(verifier) => {
                st.mode = Some("proxy");
                step(
                    "refusing the session",
                    verifier.reject(Some(msg)),
                    &mut driver,
                )
                .await?;
            }
        }
        close_session(handle, driver).await;
        bail!("refused: {msg}");
    }
    let verifier = match start {
        VerifierCommitStart::Mpc(verifier) => {
            st.mode = Some("mpc");
            if ctx.args.profile == Profile::FullDisclosureFixture {
                st.refused = true;
                step("rejecting commit", verifier.reject(Some("full-disclosure-fixture requires proxy mode")), &mut driver).await?;
                close_session(handle, driver).await;
                bail!("full-disclosure-fixture requires proxy mode");
            }
            let asked = Limits {
                max_sent: verifier.config().max_sent_data(),
                max_recv: verifier.config().max_recv_data(),
            };
            st.limits = Some(asked);
            let mpc = json!({
                "max_recv_data_online": verifier.config().max_recv_data_online(),
                "max_recv_records_online": verifier.config().max_recv_records_online(),
                "defer_decryption_from_start": verifier.config().defer_decryption_from_start(),
            });
            stop::note("mode", json!("mpc"));
            stop::note("mpc_config", mpc.clone());
            st.detail.insert("mpc_config".into(), mpc);
            if asked.max_sent > policy.max_sent || asked.max_recv > policy.max_recv {
                let msg = format!(
                    "requested caps sent {} / recv {} exceed policy {} / {}",
                    asked.max_sent, asked.max_recv, policy.max_sent, policy.max_recv
                );
                st.refused = true;
                step("rejecting commit", verifier.reject(Some(&msg)), &mut driver).await?;
                close_session(handle, driver).await;
                bail!(msg);
            }
            let verifier = step("MPC preprocessing", verifier.accept(), &mut driver).await?;
            st.timings.prewarm = Some(ms(t));
            stop::at(
                StopAt::BeforeConnect,
                "MPC: preprocessing finished; the verifier took no part in the TLS connection",
            );
            let t = Instant::now();
            st.upstream_called = true;
            let verifier = step("MPC-TLS connection", verifier.run(), &mut driver).await?;
            st.connection_done = true;
            st.timings.user = Some(ms(t));
            stop::at(
                StopAt::AfterResponse,
                "MPC: the TLS connection closed and its records were committed",
            );
            verifier
        }
        VerifierCommitStart::Proxy(verifier) => {
            st.mode = Some("proxy");
            st.limits = Some(policy);
            let name = verifier.config().server_name().as_str().to_string();
            if !ctx.args.allow_server.contains(&name) || st.admitted_name.as_ref() != Some(&name) {
                st.refused = true;
                let msg = "refused: proxy server name differs from admitted upstream allowlist name";
                step("rejecting commit", verifier.reject(Some(msg)), &mut driver).await?;
                close_session(handle, driver).await;
                bail!(msg);
            }
            st.proxy_name = Some(name.clone());
            stop::note("mode", json!("proxy"));
            let verifier = step("proxy setup", verifier.accept(), &mut driver).await?;
            st.timings.prewarm = Some(ms(t));
            st.mark("committed");
            // The upstream connection opens when the prover's first TLS bytes
            // arrive, not here: a pre-warmed prover may wait a long time for
            // its request, and an idle connection would be reset.
            let accepted = Instant::now();
            let opened: Arc<Mutex<Option<(Instant, Value)>>> = Arc::default();
            let connect = {
                let (name, resolve, opened) =
                    (name.clone(), ctx.args.resolve.clone(), opened.clone());
                async move {
                    stop::at(
                        StopAt::BeforeConnect,
                        "proxy: the prover's first TLS bytes arrived; the upstream was not dialed",
                    );
                    let t = Instant::now();
                    let (server, mut upstream) =
                        connect_upstream(&name, &resolve, "verifier").await?;
                    upstream["opened_after_accept_ms"] = json!(ms(accepted));
                    stop::note("upstream", upstream.clone());
                    *opened.lock().unwrap() = Some((t, upstream));
                    Ok(server)
                }
            };
            let (server, counters) = Counting::new(LazyUpstream::new(Box::pin(connect)));
            st.upstream_counters = counters;
            let server = RecordTap::with_stops(server);
            let (server, hello) = HelloTap::new(server);
            let server = RecordCap::new(server, policy.max_sent, policy.max_recv);
            let run = step(
                "proxied TLS connection",
                verifier.run(server.compat()),
                &mut driver,
            )
            .await;
            st.detail.insert("upstream_tls_bytes".into(), json!({
                "to_server": st.upstream_counters.written(),
                "from_server": st.upstream_counters.read(),
                "basis": "successful socket reads/writes; includes TLS handshake, records and alerts; excludes TCP/IP headers",
            }));
            let opened = opened.lock().unwrap().take();
            if let Some((t, upstream)) = opened {
                st.detail.insert("upstream".into(), upstream);
                st.upstream_called = true;
                st.timings.user = Some(ms(t));
            }
            st.detail.insert("tls".into(), server_hello(&hello));
            let verifier = run?;
            st.connection_done = true;
            st.mark("connection_closed");
            st.detail.insert("transport_at_connection_close".into(), json!({
                "operator_to_witness": st.counters.read(),
                "witness_to_operator": st.counters.written(),
            }));
            stop::at(
                StopAt::AfterResponse,
                "proxy: the proxied TLS connection ended",
            );
            verifier
        }
    };

    let t = Instant::now();
    let verifier = step("receiving proof request", verifier.verify(), &mut driver).await?;
    stop::at(
        StopAt::DuringProve,
        "the prover's proof request arrived and was not answered",
    );
    let request = verifier.request();
    if !request.server_identity() || request.reveal().is_none() {
        let refusal = verifier.reject(Some(
            "the server identity and the transcript must be revealed",
        ));
        let verifier = step("refusing the proof request", refusal, &mut driver).await?;
        step("closing verifier", verifier.close(), &mut driver).await?;
        close_session(handle, driver).await;
        bail!("prover did not reveal the server identity and the transcript");
    }
    st.mark("plaintext_auth_started");
    let (output, verifier) = step("verifying proof", verifier.accept(), &mut driver).await?;
    step("closing verifier", verifier.close(), &mut driver).await?;
    // The no-CR/LF proof follows the session on the same connection.
    handle.close();
    let mut socket = driver
        .await
        .context("session task")?
        .context("closing session")?
        .into_inner();
    st.mark("tlsn_verified");

    let verdict = build_verdict(ctx, st, session_id, output, &mut socket).await;
    st.mark("verdict_built");
    match &verdict {
        Ok((verdict, records)) => {
            let path = ctx
                .args
                .record_dir
                .join(format!("{session_id}.verdict.json"));
            write_json(&path, verdict)?;
            st.detail.insert("verdict_file".into(), json!(path));
            let path = ctx
                .args
                .record_dir
                .join(format!("{session_id}.exchanges.json"));
            write_json(&path, records)?;
            st.detail.insert("exchanges_file".into(), json!(path));
        }
        Err(e) => {
            st.detail.insert("refusal".into(), json!(describe(e)));
        }
    }
    // The prover gets every exchange record with its salt, to hand each
    // customer a receipt for its own.
    let reply = match &verdict {
        Ok((verdict, records)) => json!({ "verdict": verdict, "records": records }),
        Err(e) => json!({ "error": describe(e) }),
    };
    let sent = write_frame(&mut socket, &serde_json::to_vec(&reply)?).await;
    st.timings.prove = Some(ms(t));
    st.mark("verdict_sent");
    match (verdict, sent) {
        (Ok(_), sent) => sent.context("sending verdict"),
        // A refusal stays the session's error even if the prover is gone.
        (Err(e), sent) => {
            if let Err(send) = sent {
                st.detail
                    .insert("reply_error".into(), json!(send.to_string()));
            }
            Err(e)
        }
    }
}

fn ranges(set: &tlsn::rangeset::set::RangeSet<usize>) -> Vec<Range<usize>> {
    set.iter().collect()
}

async fn build_verdict(
    ctx: &Ctx,
    st: &mut State,
    session_id: &str,
    output: VerifierOutput,
    socket: &mut (impl AsyncRead + Unpin),
) -> Result<(Value, Vec<ExchangeRecord>)> {
    let server_name = match output.server_name {
        Some(ServerName::Dns(name)) => name.as_str().to_string(),
        None => bail!("the server identity was not proven"),
    };
    if st.admitted_name.as_ref() != Some(&server_name) || !ctx.args.allow_server.contains(&server_name) {
        bail!("proven server identity differs from admitted upstream allowlist name");
    }
    st.detail.insert("server_name".into(), json!(server_name));
    if let Some(proxied) = &st.proxy_name
        && *proxied != server_name
    {
        bail!(
            "proxied connection was opened to {proxied} but the certificate was validated for {server_name}"
        );
    }

    let mut transcript = output
        .transcript
        .ok_or_else(|| anyhow!("no transcript was revealed"))?;
    let sent_hidden = ranges(&transcript.sent_unauthed());
    let recv_hidden = ranges(&transcript.received_unauthed());
    st.detail
        .insert("sent_bytes".into(), json!(transcript.len_sent()));
    st.detail
        .insert("recv_bytes".into(), json!(transcript.len_received()));
    st.detail.insert("sent_hidden".into(), json!(sent_hidden));
    st.detail.insert("recv_hidden".into(), json!(recv_hidden));

    // Disclosure is checked before anything is written, so a transcript that
    // reveals the credential is never persisted. Unrevealed bytes are unknown
    // to the verifier and stand as '*'.
    if !recv_hidden.is_empty() {
        bail!("the response was not fully revealed: hidden ranges {recv_hidden:?}");
    }
    transcript.set_unauthed(b'*');
    let sent = transcript.sent_unsafe();
    let recv = transcript.received_unsafe();
    // The verifier knows only where the withheld spans are and how long they
    // are, not what they hold. The requests are parsed with the spans masked,
    // so the framing read here is the server's only if the spans hold no line
    // break, which the proof checked below establishes.
    let reqs = if st.operator_statement.is_some() {
        http::parse_router_requests(sent)
    } else {
        http::parse_requests(sent)
    }
    .context("parsing the revealed requests")?;
    let mut auths = Vec::new();
    for (i, req) in reqs.iter().enumerate() {
        if ctx.args.profile != Profile::CredentialHidden && req.credential_header != crate::CredentialHeader::Authorization {
            bail!("revealed profiles require authorization placement");
        }
        match &req.auth_value {
            Some(auth) => auths.push(auth.clone()),
            None => bail!("request {} has no credential header", i + 1),
        }
    }
    // Every request withholds exactly its credential header value; one that falls
    // short refuses the whole session.
    if ctx.args.profile == Profile::CredentialHidden && sent_hidden != auths {
        match auths.iter().position(|a| !sent_hidden.contains(a)) {
            Some(i) => bail!(
                "request {} does not withhold exactly its credential header value {:?}: hidden {sent_hidden:?}",
                i + 1,
                auths[i]
            ),
            None => bail!(
                "bytes other than the credential header values are withheld: hidden {sent_hidden:?}"
            ),
        }
    }
    if ctx.args.profile != Profile::CredentialHidden && !sent_hidden.is_empty() {
        bail!("revealed credential handling requires the entire sent direction");
    }
    if ctx.args.profile == Profile::FullDisclosureFixture {
        for (i, auth) in auths.iter().enumerate() {
            if !sent[auth.clone()].starts_with(b"Bearer tlsw-fixture-") {
                bail!(
                    "full-disclosure-fixture request {} Authorization must begin with Bearer tlsw-fixture-",
                    i + 1
                );
            }
        }
    }
    // Known to the witness from here, whatever becomes of the verdict.
    st.exchanges = reqs
        .iter()
        .enumerate()
        .map(|(i, req)| json!({ "n": i + 1, "job_id": req.job_id, "outcome": "unwitnessed" }))
        .collect();
    st.host = Some(reqs[0].host.clone());
    if let [req] = reqs.as_slice() {
        st.job_id = Some(req.job_id.clone());
    }
    st.request_body = Some(reqs.iter().map(|r| r.body.len()).sum());
    let circuit = if ctx.args.profile == Profile::CredentialHidden {
        Some(
            check_no_line_break(
                ctx,
                st,
                &output.transcript_commitments,
                &sent_hidden,
                socket,
            )
            .await?,
        )
    } else {
        if !output.transcript_commitments.is_empty() {
            bail!("revealed credential handling forbids transcript commitments");
        }
        None
    };
    let resps = http::parse_responses(recv).context("parsing the revealed responses")?;
    if resps.len() != reqs.len() {
        bail!(
            "{} requests were sent but {} responses came back",
            reqs.len(),
            resps.len()
        );
    }
    st.response_body = Some(resps.iter().map(|r| r.body.len()).sum());
    for (name, bytes) in [("sent", sent), ("recv", recv)] {
        st.detail.insert(format!("{name}_sha256"), json!(sha256_hex(bytes)));
        if ctx.args.write_plaintext {
            let path: PathBuf = ctx.args.record_dir.join(format!("{session_id}.{name}.txt"));
            fs::write(&path, bytes).with_context(|| format!("writing {}", path.display()))?;
            st.detail.insert(format!("{name}_file"), json!(path));
        }
    }

    let mut records = Vec::new();
    let reqs_count = reqs.len();
    for (i, (req, resp)) in reqs.into_iter().zip(resps).enumerate() {
        let images: Vec<VerdictImage> = http::inline_images(&resp.body)?
            .iter()
            .map(VerdictImage::of)
            .collect();
        let body = &sent[req.body.clone()];
        let auth = req.auth_value.clone().expect("checked above");
        let ex = &mut st.exchanges[i];
        ex["request_body"] = json!(body.len());
        ex["response_body"] = json!(resp.body.len());
        ex["response_status"] = json!(resp.status);
        if let Some(statement) = &st.operator_statement {
            if reqs_count != 1 {
                bail!("operator statement requires one exchange");
            }
            crate::router::match_statement(statement, session_id, &req, body)?;
        }
        records.push(ExchangeRecord {
            session_id: session_id.to_string(),
            operator_pub: st
                .operator_statement
                .as_ref()
                .and_then(|v| v["operator_pub"].as_str().map(str::to_owned)),
            operator_statement_sha256: st
                .operator_statement
                .as_ref()
                .map(|v| sha256_hex(&crate::record::canonical_bytes(v))),
            n: i + 1,
            job_id: req.job_id,
            outcome: "verified".into(),
            request: VerdictRequest {
                forwarded_headers_sha256: req.forwarded_headers_sha256,
                method: req.method,
                host: req.host,
                path: req.path,
                body_sha256: sha256_hex(body),
                body_bytes: body.len(),
                withheld: circuit.as_ref().map(|sha| Withheld {
                    header: req.credential_header.as_str().to_string(),
                    start: auth.start,
                    end: auth.end,
                    no_cr_lf: sha.clone(),
                }),
            },
            response: VerdictResponse {
                content_type: resp.content_type,
                status: resp.status,
                body_sha256: sha256_hex(&resp.body),
                body_bytes: resp.body.len(),
                transfer: if resp.chunked { "chunked" } else { "identity" }.to_string(),
                images,
            },
            salt: hex::encode(random_bytes::<32>()?),
        });
    }
    // What the Merkle layer costs: hashing the records into leaves and the
    // tree, beside the signing a verdict needed before it.
    let t = Instant::now();
    let leaves = records
        .iter()
        .map(ExchangeRecord::leaf)
        .collect::<Result<Vec<_>>>()?;
    let leaf_us = t.elapsed().as_secs_f64() * 1e6;
    let t = Instant::now();
    let root = merkle::root(&leaves);
    let tree_us = t.elapsed().as_secs_f64() * 1e6;
    for (ex, leaf) in st.exchanges.iter_mut().zip(&leaves) {
        ex["leaf"] = json!(hex::encode(leaf));
    }
    let verdict = Verdict {
        profile: ctx.args.profile,
        v: 5,
        session_id: session_id.to_string(),
        mode: st.mode.unwrap_or_default().to_string(),
        server_name,
        exchanges: records.len(),
        root: hex::encode(root),
        limits: st
            .limits
            .ok_or_else(|| anyhow!("limits were not recorded"))?,
        verified_at: now_rfc3339(),
        verifier_pub: String::new(),
        sig: String::new(),
    };
    let mut verdict = serde_json::to_value(&verdict)?;
    let t = Instant::now();
    sign(&mut verdict, "verifier_pub", &ctx.key);
    let sign_us = t.elapsed().as_secs_f64() * 1e6;
    let us = |x: f64| (x * 10.0).round() / 10.0;
    st.detail
        .insert("session_root".into(), json!(hex::encode(root)));
    st.detail.insert(
        "merkle".into(),
        json!({
            "leaves": leaves.len(),
            "leaf_hash_us": us(leaf_us),
            "tree_us": us(tree_us),
            "sign_us": us(sign_us),
            "verdict_bytes": serde_json::to_vec(&verdict)?.len(),
            "records_bytes": serde_json::to_vec(&records)?.len(),
        }),
    );
    Ok((verdict, records))
}

/// Requires one SHA-256 commitment to exactly the withheld spans, then reads
/// the prover's proof that the committed bytes hold no CR or LF and checks it
/// against the key built from the smallest of this binary's circuits that
/// takes them. Returns that circuit's SHA-256.
async fn check_no_line_break(
    ctx: &Ctx,
    st: &mut State,
    commitments: &[TranscriptCommitment],
    withheld: &[Range<usize>],
    socket: &mut (impl AsyncRead + Unpin),
) -> Result<String> {
    let commitment = match commitments {
        [] => bail!("no proof: the prover made no commitment to the withheld values"),
        [TranscriptCommitment::Hash(commitment)] => commitment,
        [_] => bail!("the commitment to the withheld values is not a hash commitment"),
        _ => bail!(
            "expected one commitment to the withheld values, got {}",
            commitments.len()
        ),
    };
    let range: Vec<Range<usize>> = commitment.idx.iter().collect();
    let hash = commitment.hash.value.as_bytes();
    let mut facts = json!({
        "commitment_range": range,
        "commitment_sha256": hex::encode(hash),
    });
    st.detail.insert("zk".into(), facts.clone());
    if commitment.direction != Direction::Sent || commitment.hash.alg != HashAlgId::SHA256 {
        bail!("the commitment is not a SHA-256 commitment to sent bytes");
    }
    if range.as_slice() != withheld {
        bail!("the commitment covers {range:?}, not the withheld spans {withheld:?}");
    }
    let len: usize = withheld.iter().map(|r| r.len()).sum();
    let def = zk::select_circuit(len).await?;
    let keys = ctx.circuits.as_ref().ok_or_else(|| anyhow!("no credential-hidden key cache"))?.clone();
    let setup_start = Instant::now();
    let setup_cpu = cpu_seconds();
    let (circuit, setup) = tokio::task::spawn_blocking(move || keys.circuit(def))
        .await.context("loading the selected verification key")??;
    facts["key_setup"] = setup;
    facts["key_setup_ms"] = json!(ms(setup_start));
    facts["key_setup_cpu_s"] = json!(cpu_seconds() - setup_cpu);
    facts["circuit_sha256"] = json!(def.sha256);
    facts["max_value_len"] = json!(def.max_value_len());
    let proof = read_frame(socket, 1 << 20)
        .await
        .map_err(|e| anyhow!("no proof received: {e}"))?;
    facts["proof_bytes"] = json!(proof.len());
    let t = Instant::now();
    let cpu = cpu_seconds();
    let hash = hash.to_vec();
    let checked = tokio::task::spawn_blocking(move || zk::check(&circuit, &proof, &hash, len))
        .await.context("checking the credential predicate")?;
    facts["verify_ms"] = json!(ms(t));
    facts["verify_cpu_s"] = json!(cpu_seconds() - cpu);
    facts["accepted"] = json!(checked.is_ok());
    st.detail.insert("zk".into(), facts);
    checked.map(|()| def.sha256.clone())
}
