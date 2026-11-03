//! `witness`: HTTPS calls on one connection witnessed by a TLSNotary
//! verifier, which signs a verdict binding the destination and each
//! exchange's request and response bytes;
//! a customer's seal over the call it wants; and the check that ties seal,
//! verdict and delivered file together.

mod check;
mod epoch;
mod http;
mod io;
mod management;
mod merkle;
mod prover;
mod record;
mod router;
mod seal;
mod stop;
mod verifier;
mod zk;

use std::{path::PathBuf, process::ExitCode, time::Duration, time::Instant};

use clap::{Parser, Subcommand, ValueEnum};

#[derive(Parser)]
#[command(
    name = "witness",
    version,
    about = "Witnessed HTTPS calls over TLSNotary"
)]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    /// Serve witnessed sessions, up to --max-sessions at once, and sign verdicts.
    Verifier(VerifierArgs),
    /// Route ordinary HTTP calls and serve their witness evidence.
    Router(router::Args),
    /// Reconcile every admitted receipt id against its durable evidence outcome.
    Reconcile(router::ReconcileArgs),
    /// Make witnessed calls on one connection and write each response, the
    /// verdict and the run record.
    Prover(ProverArgs),
    /// Sign a seal over the request a customer wants made.
    Seal(SealArgs),
    /// Check a verdict, seal and delivered file; PASS or the failing link.
    Check(CheckArgs),
}

#[derive(Parser)]
pub struct VerifierArgs {
    /// Exact DNS names permitted at admission and before proxy dialing.
    /// Repeating this flag replaces the default list.
    #[arg(long, default_values = ["openrouter.ai"])]
    pub allow_server: Vec<String>,
    /// Public keys permitted to sign router requests (hex .pub files).
    #[arg(long)]
    pub operator_pub: Vec<PathBuf>,
    /// Exactly one witnessing profile served by this process.
    #[arg(long, value_enum)]
    pub profile: Profile,
    #[arg(long, default_value = "0.0.0.0:7047")]
    pub listen: String,
    /// Ed25519 signing key (hex seed). Created with mode 600 if missing; the
    /// public key is written next to it with a `.pub` extension.
    #[arg(long)]
    pub key: PathBuf,
    /// Roots the verifier trusts for server identity: `webpki` for the
    /// Mozilla roots built into this binary, or a PEM file.
    #[arg(long)]
    pub roots: String,
    #[arg(long, default_value_t = 16384)]
    pub max_sent: usize,
    #[arg(long, default_value_t = 262144)]
    pub max_recv: usize,
    #[arg(long, default_value = "runs/verifier")]
    pub record_dir: PathBuf,
    /// Persist revealed sent/received plaintext, including disclosed credentials.
    #[arg(long)]
    pub write_plaintext: bool,
    /// Proxy mode: connect to NAME at HOST:PORT instead of NAME:443.
    #[arg(long, value_name = "NAME=HOST:PORT")]
    pub resolve: Vec<String>,
    /// SRS file for the no-CR/LF proof, checked against its pinned SHA-256.
    /// Fetched from crs.aztec.network if missing.
    #[arg(long, default_value = "target/srs/g1.dat")]
    pub srs: PathBuf,
    /// Exit the process at this point of the first session that reaches it,
    /// after writing `<session>.stopped.json`, to show what the prover and
    /// the provider see when the witness disappears there.
    #[arg(long, value_enum)]
    pub stop_at: Option<stop::StopAt>,
    /// Sessions served at once. A connection past this is refused at its
    /// commit, with a readable error, before any upstream connection; one
    /// that sends no commit within 10 s is closed. Past 16 pending refusals a
    /// connection is closed unread.
    #[arg(long, default_value_t = 1)]
    pub max_sessions: usize,
    /// Epoch length. When each epoch ends, the verifier writes a signed
    /// report over the sessions recorded in it to `--record-dir`. Epochs are
    /// counted from the Unix epoch, so they start on multiples of this.
    #[arg(long, default_value_t = 3600)]
    pub epoch_secs: u64,
    /// Bound each of the witness's pools to N threads and pin the process
    /// to N cores. Each session's tlsn executor gets N worker threads, and
    /// the proof-verification pools (rayon's, through RAYON_NUM_THREADS, and
    /// barretenberg's, through HARDWARE_CONCURRENCY) and the async runtime N
    /// each; the bound is per pool, so the process has more than N threads,
    /// all on the N cores. The cores are chosen from those the process may
    /// use, on one NUMA node where it can, unless --cpus names them. Without
    /// it each pool starts one thread per CPU and the process is not pinned.
    #[arg(long, value_name = "N", value_parser = clap::value_parser!(u16).range(1..))]
    pub threads: Option<u16>,
    /// The cores --threads N pins the witness to, instead of the ones it
    /// chooses: exactly N, as a list such as `16-19` or `2,4,6,8`.
    #[arg(long, value_name = "LIST", requires = "threads")]
    pub cpus: Option<String>,
}

#[derive(Parser, Clone)]
pub struct ProverArgs {
    /// Header whose value is injected from operator memory. x-api-key requires credential-hidden.
    #[arg(long, value_enum, default_value = "authorization")]
    pub credential_header: CredentialHeader,
    /// Management request JSON. No credential_field means generate locally;
    /// otherwise it is a JSON pointer into the obtain response (never saved).
    #[arg(long)]
    pub obtain_request: Option<PathBuf>,
    /// Management request JSON; {s} selects a template for each session.
    #[arg(long)]
    pub revoke_request: Option<PathBuf>,
    /// Optional dead-check route template (same host); default is the inference
    /// route. Authorization and a one-token body are always set by the prover.
    #[arg(long)]
    pub dead_check_request: Option<PathBuf>,
    /// Send the exact dead-check request once before use, requiring a live completion.
    #[arg(long)]
    pub live_check: bool,
    /// Maximum seconds after revoke 2xx for two consecutive 401/403 refusals.
    #[arg(long, default_value_t = 10, value_parser = clap::value_parser!(u64).range(1..=10))]
    pub dead_check_timeout: u64,
    /// Maximum total refusal-probe attempts per session, including failed gates.
    #[arg(long, default_value_t = 20, value_parser = clap::value_parser!(u64).range(1..))]
    pub max_dead_check_attempts: u64,
    /// Deadline for each management HTTPS exchange, including its response body.
    #[arg(long, default_value_t = 10)]
    pub management_timeout: u64,
    /// Explicit witnessing and credential profile; no default.
    #[arg(long, value_enum)]
    pub profile: Profile,
    /// Verifier address, HOST:PORT.
    #[arg(long)]
    pub verifier: String,
    #[arg(long, value_enum)]
    pub mode: Mode,
    /// Request file (method, host, path, headers, body). With --batch-max
    /// above 1, a path in which `n` in curly braces stands for the request's
    /// place in the session, from 1.
    // clap prints the braced token itself as a line break, so it is spelled out.
    #[arg(long)]
    pub request: PathBuf,
    /// The customer's seal; the request file must match it. `n` in curly
    /// braces as in --request.
    #[arg(long)]
    pub seal: PathBuf,
    /// Send up to N requests on the one connection, each as its file
    /// appears, the next once the previous response is complete. Needs
    /// --prewarm. Every request but the N-th asks the server to keep the
    /// connection open.
    #[arg(long, value_name = "N", default_value_t = 1)]
    pub batch_max: usize,
    /// Send no request that has not arrived this long after the first did;
    /// the connection is then closed once the last response is complete.
    #[arg(long, value_name = "MS")]
    pub batch_window_ms: Option<u64>,
    #[arg(long)]
    pub out_dir: PathBuf,
    /// PEM file of root certificates the prover trusts for the server;
    /// without it, the Mozilla roots built into this binary.
    #[arg(long)]
    pub ca_cert: Option<PathBuf>,
    /// Bytes the session may send. The MPC opens tlsn-mux streams roughly
    /// in proportion to the bytes sent, and a verifier that takes them up
    /// more slowly than the prover opens them reaches its 512-stream limit
    /// ("context mux error"); see --tlsn-threads.
    #[arg(long, default_value_t = 4096)]
    pub max_sent: usize,
    /// Worker threads for tlsn's executor, which otherwise starts
    /// one per available CPU. The executor opens a mux stream for each piece
    /// of work it starts; a prover that starts them faster than the verifier
    /// takes them up fills the verifier's 512-stream limit and the session
    /// fails. One thread holds the prover near the verifier's pace, at some
    /// cost in proving time when the verifier is as fast as the prover.
    #[arg(long, value_name = "N", default_value_t = 1, value_parser = clap::value_parser!(u16).range(1..))]
    pub tlsn_threads: u16,
    #[arg(long, default_value_t = 262144)]
    pub max_recv: usize,
    #[arg(long)]
    pub label: Option<String>,
    /// Pre-warm a session for HOST: commit first, then wait until the
    /// request file appears at --request (the seal must exist by then), then
    /// connect. `user` is measured from the file's arrival. Write the file
    /// atomically, for example by renaming it into place.
    #[arg(long, value_name = "HOST")]
    pub prewarm: Option<String>,
    /// MPC mode: connect to NAME at HOST:PORT instead of NAME:443.
    #[arg(long, value_name = "NAME=HOST:PORT")]
    pub resolve: Vec<String>,
    /// SRS file for the no-CR/LF proof, checked against its pinned SHA-256.
    /// Fetched from crs.aztec.network if missing.
    #[arg(long, default_value = "target/srs/g1.dat")]
    pub srs: PathBuf,
    /// Write the response body to disk as it arrives, and time the first
    /// body byte and the final `data: [DONE]` line. The request body must ask
    /// for `"stream": true`.
    #[arg(long)]
    pub stream: bool,
    /// MPC mode: decrypt received records during the connection
    /// (`defer_decryption_from_start=false`, `max_recv_data_online` equal to
    /// --max-recv) instead of after it closes.
    #[arg(long)]
    pub decrypt_online: bool,
    /// MPC mode with --decrypt-online: received records to allow for, in
    /// place of tlsn's default for the data volume.
    #[arg(long, requires = "decrypt_online")]
    pub recv_records_online: Option<usize>,
    /// Each session, from its start to its verdict, is abandoned after this
    /// many seconds, with a record of how far it got.
    #[arg(long, default_value_t = 300)]
    pub timeout: u64,
    /// Serve N sessions from this process, one after another, each on its
    /// own connection to the verifier with its own verdict, receipts and
    /// record; the SRS, verification key and roots are set up once. `s` in
    /// curly braces in --request, --seal and --out-dir stands for the
    /// session's place, from 1. Needs --prewarm. The process stops early
    /// once a session's first request does not arrive within --timeout.
    #[arg(long, value_name = "N", default_value_t = 1, value_parser = clap::value_parser!(u32).range(1..))]
    pub sessions: u32,
}

#[derive(Parser)]
pub struct SealArgs {
    /// The customer's Ed25519 key (hex seed). Created with mode 600 if
    /// missing; the public key is written next to it with a `.pub` extension.
    #[arg(long)]
    pub key: PathBuf,
    #[arg(long)]
    pub request: PathBuf,
    #[arg(long)]
    pub job_id: String,
    #[arg(long)]
    pub out: PathBuf,
}

#[derive(Parser)]
pub struct CheckArgs {
    /// Accept a signed verdict that reveals its credential to the witness.
    #[arg(long)]
    pub accept_revealed: bool,
    /// The customer's receipt: its exchange record, the path to the session
    /// root, and the signed session verdict.
    #[arg(long)]
    pub receipt: Option<PathBuf>,
    #[arg(long)]
    pub seal: Option<PathBuf>,
    /// Router evidence JSON, instead of a sealed receipt.
    #[arg(long, conflicts_with_all = ["receipt", "seal", "ledger", "epoch", "epoch_paths", "delivered", "verifier_pub", "accept_revealed", "expect_host"])]
    pub evidence: Option<PathBuf>,
    /// Self-contained policy: inline witness/operator keys and expected destination.
    #[arg(long)]
    pub trust_list: Option<PathBuf>,
    /// Retained raw HTTP request, including headers and body.
    #[arg(long)]
    pub client_request: Option<PathBuf>,
    /// Retained raw HTTP response, including status and receipt header.
    #[arg(long)]
    pub client_response: Option<PathBuf>,
    /// The file the service delivered as the response body.
    #[arg(long)]
    pub delivered: Option<PathBuf>,
    /// The expected verifier's public key, hex, as in its `.pub` file.
    #[arg(long)]
    pub verifier_pub: Option<PathBuf>,
    #[arg(long, default_value = "openrouter.ai")]
    pub expect_host: String,
    /// JSON lines of jobs already checked; a PASS appends to it.
    #[arg(long)]
    pub ledger: Option<PathBuf>,
    /// A signed epoch report: also show that the receipt's session is in it.
    #[arg(long, requires = "epoch_paths")]
    pub epoch: Option<PathBuf>,
    /// The paths file written beside that report.
    #[arg(long, requires = "epoch")]
    pub epoch_paths: Option<PathBuf>,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug, ValueEnum)]
pub enum CredentialHeader {
    Authorization,
    XApiKey,
}

impl CredentialHeader {
    pub fn as_str(self) -> &'static str {
        match self { Self::Authorization => "authorization", Self::XApiKey => "x-api-key" }
    }
    pub fn prefix(self) -> &'static str {
        match self { Self::Authorization => "Bearer ", Self::XApiKey => "" }
    }
    pub fn validate(self, profile: Profile) -> anyhow::Result<()> {
        if self == Self::XApiKey && profile != Profile::CredentialHidden {
            anyhow::bail!("x-api-key requires credential-hidden");
        }
        Ok(())
    }
}

#[derive(Clone, Copy, PartialEq, Eq, Debug, ValueEnum, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum Profile {
    FullDisclosureFixture,
    CredentialHidden,
    CredentialSequence,
}

impl Profile {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::FullDisclosureFixture => "full-disclosure-fixture",
            Self::CredentialHidden => "credential-hidden",
            Self::CredentialSequence => "credential-sequence",
        }
    }

    fn check_environment(self, roots: &str) -> anyhow::Result<()> {
        if self == Self::CredentialSequence && std::env::var_os("OPENROUTER_API_KEY").is_some() {
            anyhow::bail!("credential-sequence refuses to start while OPENROUTER_API_KEY is set");
        }
        if self == Self::FullDisclosureFixture {
            for name in ["OPENROUTER_API_KEY", "WITNESS_UPSTREAM_CREDENTIAL"] {
                if std::env::var_os(name).is_some() {
                    anyhow::bail!("full-disclosure-fixture refuses to start while {name} is set");
                }
            }
            let credential = std::env::var("WITNESS_FIXTURE_CREDENTIAL")
                .map_err(|_| anyhow::anyhow!("WITNESS_FIXTURE_CREDENTIAL is required"))?;
            if !credential.starts_with("tlsw-fixture-") {
                anyhow::bail!("WITNESS_FIXTURE_CREDENTIAL must begin with tlsw-fixture-");
            }
            if roots == "webpki" || !std::path::Path::new(roots).is_file() {
                anyhow::bail!("full-disclosure-fixture requires a local PEM root file");
            }
            load_roots(std::path::Path::new(roots))?;
        }
        Ok(())
    }

    pub fn credential(self) -> anyhow::Result<String> {
        let name = match self {
            Self::FullDisclosureFixture => "WITNESS_FIXTURE_CREDENTIAL",
            Self::CredentialHidden => "WITNESS_UPSTREAM_CREDENTIAL",
            Self::CredentialSequence => anyhow::bail!("sequence credential is session-only"),
        };
        std::env::var(name).map_err(|_| anyhow::anyhow!("{name} is required"))
    }

    fn lifecycle(self, obtain: bool, revoke: bool, probe: bool) -> anyhow::Result<()> {
        if self == Self::CredentialSequence {
            if !obtain || !revoke { anyhow::bail!("credential-sequence requires --obtain-request and --revoke-request"); }
        } else if obtain || revoke || probe {
            anyhow::bail!("lifecycle flags require credential-sequence");
        }
        Ok(())
    }
}

impl ProverArgs {
    fn is_sequence(&self) -> bool { self.profile == Profile::CredentialSequence }
}

#[derive(Clone, Copy, ValueEnum)]
pub enum Mode {
    Mpc,
    Proxy,
}

impl Mode {
    pub fn as_str(self) -> &'static str {
        match self {
            Mode::Mpc => "mpc",
            Mode::Proxy => "proxy",
        }
    }
}

/// The root store for `webpki` or a PEM file, with a description for records:
/// its source and a SHA-256 over the file, or over the concatenated DER roots.
pub fn roots(spec: &str) -> anyhow::Result<(tlsn::webpki::RootCertStore, serde_json::Value)> {
    use sha2::{Digest, Sha256};
    if spec == "webpki" {
        let store = tlsn::webpki::RootCertStore::mozilla();
        let mut hash = Sha256::new();
        for root in &store.roots {
            hash.update(&root.0);
        }
        let about = serde_json::json!({
            "source": "webpki",
            "count": store.roots.len(),
            "sha256": hex::encode(hash.finalize()),
        });
        return Ok((store, about));
    }
    let path = std::path::Path::new(spec);
    let store = load_roots(path)?;
    let about = serde_json::json!({
        "path": path,
        "count": store.roots.len(),
        "sha256": record::sha256_hex(&std::fs::read(path)?),
    });
    Ok((store, about))
}

/// Reads every certificate in a PEM file into a root store.
pub fn load_roots(path: &std::path::Path) -> anyhow::Result<tlsn::webpki::RootCertStore> {
    use anyhow::Context;
    let pem =
        std::fs::read_to_string(path).with_context(|| format!("reading {}", path.display()))?;
    const END: &str = "-----END CERTIFICATE-----";
    let mut roots = Vec::new();
    for block in pem.split_inclusive(END).filter(|b| b.contains(END)) {
        let der = tlsn::webpki::CertificateDer::from_pem_slice(block.as_bytes())
            .map_err(|_| anyhow::anyhow!("{} has an unreadable certificate", path.display()))?;
        roots.push(der);
    }
    if roots.is_empty() {
        anyhow::bail!("{} contains no PEM certificates", path.display());
    }
    Ok(tlsn::webpki::RootCertStore { roots })
}

fn exit(result: anyhow::Result<bool>) -> ExitCode {
    match result {
        Ok(true) => ExitCode::SUCCESS,
        Ok(false) => ExitCode::FAILURE,
        Err(e) => {
            eprintln!("error: {e:#}");
            ExitCode::FAILURE
        }
    }
}

/// barretenberg proves on this many threads at most. More threads add CPU
/// time without making the proof much faster.
const PROVING_THREADS: u32 = 4;

fn main() -> ExitCode {
    let started = Instant::now();
    let cli = Cli::parse();
    let checked = match &cli.cmd {
        Cmd::Prover(a) => {
            let root = a.ca_cert.as_ref().map_or("webpki".into(), |p| p.display().to_string());
            a.profile.check_environment(&root).and_then(|()| {
                a.credential_header.validate(a.profile)?;
                if a.profile == Profile::FullDisclosureFixture && !matches!(a.mode, Mode::Proxy) {
                    anyhow::bail!("full-disclosure-fixture requires proxy mode");
                }
                a.profile.lifecycle(a.obtain_request.is_some(), a.revoke_request.is_some(), a.dead_check_request.is_some() || a.live_check)
            })
        }
        Cmd::Verifier(a) => a.profile.check_environment(&a.roots),
        Cmd::Router(a) => a.validate(),
        _ => Ok(()),
    };
    if let Err(e) = checked { return exit(Err(e)); }
    tracing(&cli.cmd);
    let cmd = match cli.cmd {
        Cmd::Seal(args) => return exit(seal::run(args).map(|()| true)),
        Cmd::Check(args) => return exit(check::run(args)),
        cmd => cmd,
    };
    let mut workers = None;
    let mut pinned = None;
    if let Cmd::Verifier(VerifierArgs {
        threads: Some(n),
        cpus,
        ..
    }) = &cmd
    {
        // rayon reads RAYON_NUM_THREADS when its pool starts, and
        // barretenberg HARDWARE_CONCURRENCY when it first runs in parallel;
        // neither has yet.
        // SAFETY: no other thread exists yet.
        unsafe {
            std::env::set_var("RAYON_NUM_THREADS", n.to_string());
            std::env::set_var("HARDWARE_CONCURRENCY", n.to_string());
        }
        workers = Some(*n as usize);
        // Every thread started from here on inherits the cores.
        match io::pin(*n, cpus.as_deref()) {
            Ok(p) => pinned = Some(p),
            Err(e) => {
                eprintln!("error: pinning to {n} cores: {e:#}");
                return ExitCode::FAILURE;
            }
        }
    }
    if matches!(cmd, Cmd::Prover(_) | Cmd::Router(_)) {
        workers = Some(4);
        // barretenberg reads HARDWARE_CONCURRENCY when it first proves.
        let set: Option<u32> = std::env::var("HARDWARE_CONCURRENCY")
            .ok()
            .and_then(|v| v.parse().ok());
        if !set.is_some_and(|n| (1..=PROVING_THREADS).contains(&n)) {
            // SAFETY: no other thread exists yet.
            unsafe { std::env::set_var("HARDWARE_CONCURRENCY", PROVING_THREADS.to_string()) };
        }
    }
    let mut runtime = tokio::runtime::Builder::new_multi_thread();
    if let Some(n) = workers {
        runtime.worker_threads(n);
    }
    let runtime = match runtime.enable_all().build() {
        Ok(rt) => rt,
        Err(e) => {
            eprintln!("error: starting runtime: {e}");
            return ExitCode::FAILURE;
        }
    };
    let result = runtime.block_on(async {
        match cmd {
            Cmd::Router(args) => router::run(args).await.map(|()| true),
            Cmd::Reconcile(args) => router::reconcile(args),
            Cmd::Verifier(args) => verifier::run(args, pinned).await.map(|()| true),
            Cmd::Prover(args) => prover::run(args, started).await,
            Cmd::Seal(_) | Cmd::Check(_) => unreachable!("handled above"),
        }
    });
    // A blocking task abandoned by a timeout, such as a proof in progress,
    // must not keep the process alive.
    runtime.shutdown_timeout(Duration::from_secs(5));
    exit(result)
}

/// Log lines go to stderr, filtered by RUST_LOG (default `warn`). Separately,
/// the prover watches tlsn's proxy-mode handshake, and a verifier given
/// --stop-at watches tlsn's MPC record layer; neither changes what is logged.
fn tracing(cmd: &Cmd) {
    use tracing_subscriber::{
        Layer as _, filter::Targets, layer::SubscriberExt as _, util::SubscriberInitExt as _,
    };
    let log = tracing_subscriber::fmt::layer()
        .with_writer(std::io::stderr)
        .with_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("warn")),
        );
    let debug = |target: &str| Targets::new().with_target(target, tracing::Level::DEBUG);
    let prover = matches!(cmd, Cmd::Prover(_))
        .then(|| prover::ProxyHandshake.with_filter(debug("tlsn::prover::client::proxy")));
    let verifier = match cmd {
        Cmd::Verifier(args) if args.stop_at.is_some() => {
            stop::configure(args.stop_at);
            Some(stop::MpcEvents.with_filter(debug("mpc_tls::record_layer")))
        }
        _ => None,
    };
    tracing_subscriber::registry()
        .with(log)
        .with(prover)
        .with(verifier)
        .init();
}
