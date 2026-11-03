//! The verifier's `--stop-at`: the process exits at one named point of a
//! session, after writing a note of where it stopped. It answers what the
//! prover, and the provider, see when the witness disappears at that point.
//!
//! | Point | Proxy mode | MPC mode |
//! |---|---|---|
//! | `before_connect` | the prover's first TLS bytes arrived; the upstream was not dialed | preprocessing is done; the prover has not started its TLS connection |
//! | `during_handshake` | the server's first bytes arrived; not relayed to the prover | the client Finished is being encrypted; the handshake is incomplete |
//! | `after_request` | the server's first application-data record arrived; not relayed | the server's first application-data record reached the prover; not decrypted |
//! | `after_response` | the proxied TLS connection ended | the TLS connection ended and its records were committed |
//! | `during_prove` | the prover's proof request arrived; not answered | the same |
//!
//! In MPC mode the verifier sees no TLS records, so the two points inside the
//! connection are read from tlsn's own debug events (see [`MpcEvents`]).

use std::{
    path::PathBuf,
    sync::{Mutex, OnceLock},
    time::Instant,
};

use clap::ValueEnum;
use serde_json::{Map, Value, json};

use crate::record::{ms, now_rfc3339};

#[derive(Clone, Copy, PartialEq, Eq, ValueEnum)]
#[value(rename_all = "snake_case")]
pub enum StopAt {
    BeforeConnect,
    DuringHandshake,
    AfterRequest,
    AfterResponse,
    DuringProve,
}

impl StopAt {
    pub fn as_str(self) -> &'static str {
        match self {
            StopAt::BeforeConnect => "before_connect",
            StopAt::DuringHandshake => "during_handshake",
            StopAt::AfterRequest => "after_request",
            StopAt::AfterResponse => "after_response",
            StopAt::DuringProve => "during_prove",
        }
    }
}

struct Session {
    id: String,
    dir: PathBuf,
    started: Instant,
    facts: Map<String, Value>,
    /// MPC: the follower has started on application data.
    traffic: bool,
    /// MPC: the follower has encrypted the first application-data record.
    request: bool,
    /// MPC: record-layer flushes seen in this session.
    flushes: u32,
}

static AT: OnceLock<StopAt> = OnceLock::new();
static SESSION: Mutex<Option<Session>> = Mutex::new(None);

pub fn configure(at: Option<StopAt>) {
    if let Some(at) = at {
        let _ = AT.set(at);
    }
}

pub fn configured() -> Option<StopAt> {
    AT.get().copied()
}

/// Starts tracking a new session; its note is `<id>.stopped.json` in `dir`.
pub fn begin(id: &str, dir: &std::path::Path) {
    *SESSION.lock().unwrap() = Some(Session {
        id: id.to_string(),
        dir: dir.to_path_buf(),
        started: Instant::now(),
        facts: Map::new(),
        traffic: false,
        request: false,
        flushes: 0,
    });
}

/// Adds a fact to the note written if the session stops.
pub fn note(key: &str, value: Value) {
    if AT.get().is_none() {
        return;
    }
    if let Some(s) = SESSION.lock().unwrap().as_mut() {
        s.facts.insert(key.to_string(), value);
    }
}

/// Exits the process if `point` is the configured stop point.
pub fn at(point: StopAt, what: &str) {
    if AT.get() != Some(&point) {
        return;
    }
    let session = SESSION.lock().unwrap().take();
    if let Some(s) = session {
        let note = json!({
            "stop_at": point.as_str(),
            "what": what,
            "session_id": s.id,
            "stopped_at": now_rfc3339(),
            "after_session_start_ms": ms(s.started),
            "pid": std::process::id(),
            "facts": s.facts,
        });
        let path = s.dir.join(format!("{}.stopped.json", s.id));
        let text = serde_json::to_string_pretty(&note).unwrap_or_default() + "\n";
        if let Err(e) = std::fs::write(&path, text) {
            eprintln!("writing {}: {e}", path.display());
        }
        println!("session {}: stopped at {}: {what}", s.id, point.as_str());
    }
    use std::io::Write as _;
    let _ = std::io::stdout().flush();
    std::process::exit(3);
}

/// Watches tlsn's MPC record layer in the verifier, which runs only the
/// follower. At tlsn alpha.15 every record-layer flush logs either
/// "processing N encrypt ops and M decrypt ops" or "no operations to process,
/// skipping", and the switch to application data logs "started processing
/// application data". A flush happens only when a record is to be encrypted or
/// one has arrived, so in order: the first flush encrypts the client Finished;
/// after the switch, the first flush with an encrypt op is the request; the
/// next flush means the server's first response record has reached the prover.
pub struct MpcEvents;

struct Message(String);

impl tracing::field::Visit for Message {
    fn record_debug(&mut self, field: &tracing::field::Field, value: &dyn std::fmt::Debug) {
        if field.name() == "message" {
            self.0 = format!("{value:?}");
        }
    }
}

/// The text of a tracing event.
pub fn message(event: &tracing::Event<'_>) -> String {
    let mut message = Message(String::new());
    event.record(&mut message);
    message.0
}

impl<S: tracing::Subscriber> tracing_subscriber::Layer<S> for MpcEvents {
    fn on_event(&self, event: &tracing::Event<'_>, _: tracing_subscriber::layer::Context<'_, S>) {
        if event.metadata().target() != "mpc_tls::record_layer" {
            return;
        }
        let text = message(event);
        let flush = text.starts_with("processing ") || text.starts_with("no operations to process");
        let hit = {
            let mut guard = SESSION.lock().unwrap();
            let Some(s) = guard.as_mut() else { return };
            if text.starts_with("started processing application data") {
                s.traffic = true;
                return;
            }
            if !flush {
                return;
            }
            s.flushes += 1;
            s.facts.insert("mpc_flushes".into(), json!(s.flushes));
            if !s.traffic {
                (s.flushes == 1).then_some((
                    StopAt::DuringHandshake,
                    "MPC: the follower began encrypting the client Finished; the handshake is incomplete",
                ))
            } else if !s.request {
                s.request = !text.starts_with("processing 0 encrypt") && text.starts_with("processing ");
                None
            } else {
                Some((
                    StopAt::AfterRequest,
                    "MPC: the request was encrypted and sent, and the server's first response record reached the prover; it was not decrypted",
                ))
            }
        };
        if let Some((point, what)) = hit {
            at(point, what);
        }
    }
}
