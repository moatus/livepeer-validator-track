//! Socket wrappers and small network helpers shared by both roles.

use std::{
    future::Future,
    io,
    pin::Pin,
    sync::{
        Arc, Mutex,
        atomic::{AtomicU64, Ordering},
    },
    task::{Context, Poll, Waker},
    time::Instant,
};

use anyhow::{Context as _, Result, anyhow, bail};
use serde_json::{Value, json};
use tokio::{
    io::{AsyncRead, AsyncReadExt, AsyncWrite, AsyncWriteExt, ReadBuf},
    net::TcpStream,
    task::{JoinError, JoinHandle},
};

/// Bytes read from and written to one socket.
#[derive(Clone, Default)]
pub struct Counters {
    read: Arc<AtomicU64>,
    written: Arc<AtomicU64>,
}

impl Counters {
    pub fn read(&self) -> u64 {
        self.read.load(Ordering::Relaxed)
    }

    pub fn written(&self) -> u64 {
        self.written.load(Ordering::Relaxed)
    }
}

/// Counts every byte crossing the prover-verifier socket, including the
/// verdict exchange that follows the TLSNotary session.
pub struct Counting<T> {
    inner: T,
    counters: Counters,
}

impl<T> Counting<T> {
    pub fn new(inner: T) -> (Self, Counters) {
        let counters = Counters::default();
        (
            Self {
                inner,
                counters: counters.clone(),
            },
            counters,
        )
    }
}

impl<T: AsyncRead + Unpin> AsyncRead for Counting<T> {
    fn poll_read(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &mut ReadBuf<'_>,
    ) -> Poll<io::Result<()>> {
        let this = self.get_mut();
        let before = buf.filled().len();
        let poll = Pin::new(&mut this.inner).poll_read(cx, buf);
        if let Poll::Ready(Ok(())) = poll {
            let n = (buf.filled().len() - before) as u64;
            this.counters.read.fetch_add(n, Ordering::Relaxed);
        }
        poll
    }
}

impl<T: AsyncWrite + Unpin> AsyncWrite for Counting<T> {
    fn poll_write(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &[u8],
    ) -> Poll<io::Result<usize>> {
        let this = self.get_mut();
        let poll = Pin::new(&mut this.inner).poll_write(cx, buf);
        if let Poll::Ready(Ok(n)) = poll {
            this.counters.written.fetch_add(n as u64, Ordering::Relaxed);
        }
        poll
    }

    fn poll_flush(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<io::Result<()>> {
        Pin::new(&mut self.get_mut().inner).poll_flush(cx)
    }

    fn poll_shutdown(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<io::Result<()>> {
        Pin::new(&mut self.get_mut().inner).poll_shutdown(cx)
    }
}

/// Meters TLS 1.2 application-data plaintext in one direction. tlsn supports
/// only AES-128-GCM suites, whose records carry 24 bytes of overhead
/// (8-byte explicit nonce, 16-byte tag).
#[derive(Clone)]
struct RecordMeter {
    what: &'static str,
    flag: &'static str,
    cap: u64,
    total: u64,
    /// Bytes and application-data records seen, whole or begun.
    bytes: u64,
    records: u64,
    header: [u8; 5],
    header_len: usize,
    body_left: usize,
}

impl RecordMeter {
    fn new(what: &'static str, flag: &'static str, cap: usize) -> Self {
        Self {
            what,
            flag,
            cap: cap as u64,
            total: 0,
            bytes: 0,
            records: 0,
            header: [0; 5],
            header_len: 0,
            body_left: 0,
        }
    }

    fn feed(&mut self, mut data: &[u8]) -> io::Result<()> {
        self.bytes += data.len() as u64;
        while !data.is_empty() {
            if self.body_left > 0 {
                let n = self.body_left.min(data.len());
                self.body_left -= n;
                data = &data[n..];
                continue;
            }
            let n = (5 - self.header_len).min(data.len());
            self.header[self.header_len..self.header_len + n].copy_from_slice(&data[..n]);
            self.header_len += n;
            data = &data[n..];
            if self.header_len == 5 {
                self.header_len = 0;
                self.body_left = u16::from_be_bytes([self.header[3], self.header[4]]) as usize;
                if self.header[0] == 23 {
                    self.records += 1;
                    self.total += self.body_left.saturating_sub(24) as u64;
                    if self.total > self.cap {
                        return Err(io::Error::other(format!(
                            "{} exceeds the verifier's {} policy: at least {} bytes, cap {}",
                            self.what, self.flag, self.total, self.cap
                        )));
                    }
                }
            }
        }
        Ok(())
    }
}

/// The verifier's upstream connection in proxy mode. tlsn's proxy mode has no
/// data caps of its own, so the verifier enforces its policy here by failing
/// the stream the moment either direction passes its cap.
pub struct RecordCap<T> {
    inner: T,
    sent: RecordMeter,
    recv: RecordMeter,
}

impl<T> RecordCap<T> {
    pub fn new(inner: T, max_sent: usize, max_recv: usize) -> Self {
        Self {
            inner,
            sent: RecordMeter::new("request", "--max-sent", max_sent),
            recv: RecordMeter::new("response", "--max-recv", max_recv),
        }
    }
}

impl<T: AsyncRead + Unpin> AsyncRead for RecordCap<T> {
    fn poll_read(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &mut ReadBuf<'_>,
    ) -> Poll<io::Result<()>> {
        let this = self.get_mut();
        let before = buf.filled().len();
        match Pin::new(&mut this.inner).poll_read(cx, buf) {
            Poll::Ready(Ok(())) => Poll::Ready(this.recv.feed(&buf.filled()[before..])),
            other => other,
        }
    }
}

impl<T: AsyncWrite + Unpin> AsyncWrite for RecordCap<T> {
    fn poll_write(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &[u8],
    ) -> Poll<io::Result<usize>> {
        let this = self.get_mut();
        // Refuse before forwarding, so over-cap bytes never reach the server.
        this.sent.clone().feed(buf)?;
        let poll = Pin::new(&mut this.inner).poll_write(cx, buf);
        if let Poll::Ready(Ok(n)) = poll {
            this.sent.feed(&buf[..n])?;
        }
        poll
    }

    fn poll_flush(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<io::Result<()>> {
        Pin::new(&mut self.get_mut().inner).poll_flush(cx)
    }

    fn poll_shutdown(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<io::Result<()>> {
        Pin::new(&mut self.get_mut().inner).poll_shutdown(cx)
    }
}

/// Application-data records that have crossed one TLS connection, whole or
/// begun, by direction, and when the server's arrived.
#[derive(Clone, Default)]
pub struct AppData {
    sent: Arc<AtomicU64>,
    recv: Arc<AtomicU64>,
    /// The first server application-data record begun, and the server's last
    /// bytes of any kind.
    recv_times: Arc<Mutex<(Option<Instant>, Option<Instant>)>>,
}

impl AppData {
    pub fn sent(&self) -> u64 {
        self.sent.load(Ordering::Relaxed)
    }

    pub fn recv(&self) -> u64 {
        self.recv.load(Ordering::Relaxed)
    }

    /// When the server's first application-data record and its last bytes
    /// arrived on the wire.
    pub fn recv_times(&self) -> (Option<Instant>, Option<Instant>) {
        *self.recv_times.lock().unwrap()
    }
}

/// Counts the application-data records on a TLS connection this process
/// holds. On the prover's own server connection in MPC mode, a record written
/// means the request has left this host; none written means it has not.
/// On the verifier's upstream connection in proxy mode, `--stop-at` acts here
/// before the server's bytes are relayed: `during_handshake` at its first
/// bytes, `after_request` at its first application-data record. The stop note
/// then counts what was relayed before them; at any later point it counts
/// everything relayed, since it is refreshed after every read and write.
pub struct RecordTap<T> {
    inner: T,
    sent: RecordMeter,
    recv: RecordMeter,
    counts: AppData,
    stops: bool,
}

impl<T> RecordTap<T> {
    pub fn new(inner: T) -> (Self, AppData) {
        let counts = AppData::default();
        let meter = |what| RecordMeter::new(what, "", usize::MAX);
        let tap = Self {
            inner,
            sent: meter("sent"),
            recv: meter("received"),
            counts: counts.clone(),
            stops: false,
        };
        (tap, counts)
    }

    /// With the verifier's proxy-mode stop points.
    pub fn with_stops(inner: T) -> Self {
        Self {
            stops: true,
            ..Self::new(inner).0
        }
    }

    fn note(&self) {
        crate::stop::note(
            "upstream_seen",
            json!({
                "bytes_to_server": self.sent.bytes,
                "app_data_records_to_server": self.sent.records,
                "bytes_from_server_relayed": self.recv.bytes,
                "app_data_records_from_server_relayed": self.recv.records,
            }),
        );
    }
}

impl<T: AsyncRead + Unpin> AsyncRead for RecordTap<T> {
    fn poll_read(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &mut ReadBuf<'_>,
    ) -> Poll<io::Result<()>> {
        use crate::stop::{StopAt, at};
        let this = self.get_mut();
        let before = buf.filled().len();
        let poll = Pin::new(&mut this.inner).poll_read(cx, buf);
        if let Poll::Ready(Ok(())) = poll {
            let new = &buf.filled()[before..];
            if this.stops && this.recv.bytes == 0 && !new.is_empty() {
                this.note();
                at(
                    StopAt::DuringHandshake,
                    "proxy: the server's first bytes arrived at the verifier and were not relayed",
                );
            }
            let records = this.recv.records;
            let mut recv = this.recv.clone();
            let _ = recv.feed(new);
            if this.stops && recv.records > records {
                this.note();
                at(
                    StopAt::AfterRequest,
                    "proxy: the server's first application-data record arrived at the verifier and was not relayed",
                );
            }
            if !new.is_empty() {
                let mut times = this.counts.recv_times.lock().unwrap();
                if recv.records > 0 && times.0.is_none() {
                    times.0 = Some(Instant::now());
                }
                times.1 = Some(Instant::now());
            }
            this.recv = recv;
            this.counts.recv.store(this.recv.records, Ordering::Relaxed);
            if this.stops {
                this.note();
            }
        }
        poll
    }
}

impl<T: AsyncWrite + Unpin> AsyncWrite for RecordTap<T> {
    fn poll_write(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &[u8],
    ) -> Poll<io::Result<usize>> {
        let this = self.get_mut();
        let poll = Pin::new(&mut this.inner).poll_write(cx, buf);
        if let Poll::Ready(Ok(n)) = poll {
            let _ = this.sent.feed(&buf[..n]);
            this.counts.sent.store(this.sent.records, Ordering::Relaxed);
            if this.stops {
                this.note();
            }
        }
        poll
    }

    fn poll_flush(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<io::Result<()>> {
        Pin::new(&mut self.get_mut().inner).poll_flush(cx)
    }

    fn poll_shutdown(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<io::Result<()>> {
        Pin::new(&mut self.get_mut().inner).poll_shutdown(cx)
    }
}

type Connecting = Pin<Box<dyn Future<Output = Result<TcpStream>> + Send>>;

enum Upstream {
    Closed(Connecting),
    Open(TcpStream),
    Failed,
}

/// The verifier's upstream connection in proxy mode, opened only when the
/// prover's first TLS bytes arrive. A pre-warmed prover sends none until its
/// request file has arrived and passed its checks, so no upstream connection
/// sits idle while the session waits.
pub struct LazyUpstream {
    state: Upstream,
    reader: Option<Waker>,
}

impl LazyUpstream {
    pub fn new(connect: Connecting) -> Self {
        Self {
            state: Upstream::Closed(connect),
            reader: None,
        }
    }
}

impl AsyncRead for LazyUpstream {
    fn poll_read(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &mut ReadBuf<'_>,
    ) -> Poll<io::Result<()>> {
        let this = self.get_mut();
        match &mut this.state {
            Upstream::Open(tcp) => Pin::new(tcp).poll_read(cx, buf),
            Upstream::Closed(_) => {
                this.reader = Some(cx.waker().clone());
                Poll::Pending
            }
            Upstream::Failed => Poll::Ready(Err(io::Error::other("the upstream connection failed"))),
        }
    }
}

impl AsyncWrite for LazyUpstream {
    fn poll_write(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &[u8],
    ) -> Poll<io::Result<usize>> {
        let this = self.get_mut();
        if let Upstream::Closed(connect) = &mut this.state {
            let opened = match connect.as_mut().poll(cx) {
                Poll::Pending => return Poll::Pending,
                Poll::Ready(opened) => opened,
            };
            if let Some(reader) = this.reader.take() {
                reader.wake();
            }
            match opened {
                Ok(tcp) => this.state = Upstream::Open(tcp),
                Err(e) => {
                    this.state = Upstream::Failed;
                    return Poll::Ready(Err(io::Error::other(format!("{e:#}"))));
                }
            }
        }
        match &mut this.state {
            Upstream::Open(tcp) => Pin::new(tcp).poll_write(cx, buf),
            _ => Poll::Ready(Err(io::Error::other("the upstream connection failed"))),
        }
    }

    fn poll_flush(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<io::Result<()>> {
        match &mut self.get_mut().state {
            Upstream::Open(tcp) => Pin::new(tcp).poll_flush(cx),
            _ => Poll::Ready(Ok(())),
        }
    }

    fn poll_shutdown(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<io::Result<()>> {
        match &mut self.get_mut().state {
            Upstream::Open(tcp) => Pin::new(tcp).poll_shutdown(cx),
            _ => Poll::Ready(Ok(())),
        }
    }
}

/// A spawned task that is aborted when dropped, so an early error on one side
/// tears down the socket and the peer sees the failure instead of hanging.
pub struct AbortOnDrop<T>(pub JoinHandle<T>);

impl<T> Drop for AbortOnDrop<T> {
    fn drop(&mut self) {
        self.0.abort();
    }
}

impl<T> Future for AbortOnDrop<T> {
    type Output = Result<T, JoinError>;

    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        Pin::new(&mut self.get_mut().0).poll(cx)
    }
}

/// Runs one protocol step while watching the session driver. A tlsn step can
/// wait forever once the session's connection is gone, so the driver ending
/// first fails the step. The step's own result wins a tie: its error says more.
pub async fn step<F, T, E2, D, E>(what: &str, fut: F, driver: &mut AbortOnDrop<Result<D, E>>) -> Result<T>
where
    F: Future<Output = Result<T, E2>>,
    E2: std::error::Error + Send + Sync + 'static,
    E: std::error::Error + Send + Sync + 'static,
{
    let out = tokio::select! {
        biased;
        out = fut => out.map_err(anyhow::Error::new),
        end = driver => Err(session_ended(end)),
    };
    out.with_context(|| what.to_string())
}

/// Describes a session driver that finished while a step still needed it.
pub fn session_ended<T, E>(end: Result<Result<T, E>, JoinError>) -> anyhow::Error
where
    E: std::error::Error + Send + Sync + 'static,
{
    match end {
        Ok(Ok(_)) => anyhow!("the peer closed the session before this step finished"),
        Ok(Err(e)) => anyhow::Error::new(e).context("the session connection failed before this step finished"),
        Err(e) => anyhow::Error::new(e).context("session task"),
    }
}

/// Length-prefixed frame on the raw socket left after the session closes.
pub async fn write_frame<W: AsyncWrite + Unpin>(w: &mut W, body: &[u8]) -> io::Result<()> {
    w.write_all(&(body.len() as u32).to_be_bytes()).await?;
    w.write_all(body).await?;
    w.flush().await
}

pub async fn read_frame<R: AsyncRead + Unpin>(r: &mut R, max: usize) -> io::Result<Vec<u8>> {
    let mut len = [0u8; 4];
    r.read_exact(&mut len).await?;
    let len = u32::from_be_bytes(len) as usize;
    if len > max {
        return Err(io::Error::other(format!("frame of {len} bytes exceeds {max}")));
    }
    let mut body = vec![0; len];
    r.read_exact(&mut body).await?;
    Ok(body)
}

/// Opens TCP to `name`, at the `--resolve` override if one names it, else
/// `name:443`. Returns the stream and, for the run record, which process on
/// which host opened it (`by` names the role) and between which addresses.
pub async fn connect_upstream(name: &str, resolve: &[String], by: &str) -> Result<(TcpStream, Value)> {
    let mut addr = format!("{name}:443");
    for entry in resolve {
        let (n, a) = entry
            .split_once('=')
            .ok_or_else(|| anyhow!("--resolve {entry:?} is not NAME=HOST:PORT"))?;
        if n == name {
            addr = a.to_string();
        }
    }
    let stream = TcpStream::connect(&addr)
        .await
        .with_context(|| format!("connecting to {name} at {addr}"))?;
    stream.set_nodelay(true)?;
    let facts = json!({
        "opened_by": by,
        "host": hostname(),
        "pid": std::process::id(),
        "dialed": addr,
        "local_addr": stream.local_addr()?.to_string(),
        "peer_addr": stream.peer_addr()?.to_string(),
    });
    Ok((stream, facts))
}

fn hostname() -> String {
    std::fs::read_to_string("/proc/sys/kernel/hostname")
        .map(|s| s.trim().to_string())
        .unwrap_or_default()
}

/// The process writing a record: host, pid, and the allocator setting that
/// changes how a long-lived verifier's per-session peak RSS reads.
pub fn process_facts() -> Value {
    json!({
        "host": hostname(),
        "pid": std::process::id(),
        "malloc_arena_max": std::env::var("MALLOC_ARENA_MAX").ok(),
    })
}

/// Record header, handshake header, version, random, session id length, a
/// session id of up to 32 bytes, and the cipher suite.
const HELLO_PREFIX: usize = 5 + 4 + 2 + 32 + 1 + 32 + 2;

/// The first bytes the server sent, shared with the record writer.
pub type Hello = Arc<Mutex<Vec<u8>>>;

/// Keeps the first bytes read from the server, enough for a TLS 1.2
/// ServerHello up to its cipher suite. tlsn does not report the suite.
pub struct HelloTap<T> {
    inner: T,
    seen: Hello,
}

impl<T> HelloTap<T> {
    pub fn new(inner: T) -> (Self, Hello) {
        let seen = Hello::default();
        (
            Self {
                inner,
                seen: seen.clone(),
            },
            seen,
        )
    }
}

impl<T: AsyncRead + Unpin> AsyncRead for HelloTap<T> {
    fn poll_read(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &mut ReadBuf<'_>,
    ) -> Poll<io::Result<()>> {
        let this = self.get_mut();
        let before = buf.filled().len();
        let poll = Pin::new(&mut this.inner).poll_read(cx, buf);
        if let Poll::Ready(Ok(())) = poll {
            let mut seen = this.seen.lock().unwrap();
            let want = HELLO_PREFIX.saturating_sub(seen.len());
            let new = &buf.filled()[before..];
            seen.extend_from_slice(&new[..want.min(new.len())]);
        }
        poll
    }
}

impl<T: AsyncWrite + Unpin> AsyncWrite for HelloTap<T> {
    fn poll_write(self: Pin<&mut Self>, cx: &mut Context<'_>, buf: &[u8]) -> Poll<io::Result<usize>> {
        Pin::new(&mut self.get_mut().inner).poll_write(cx, buf)
    }

    fn poll_flush(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<io::Result<()>> {
        Pin::new(&mut self.get_mut().inner).poll_flush(cx)
    }

    fn poll_shutdown(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<io::Result<()>> {
        Pin::new(&mut self.get_mut().inner).poll_shutdown(cx)
    }
}

/// The protocol version and cipher suite in the server's first record, if it
/// is a ServerHello; otherwise what that record was.
pub fn server_hello(hello: &Hello) -> Value {
    let b = hello.lock().unwrap();
    if b.len() >= 7 && b[0] == 21 {
        return json!({ "first_record": "alert", "alert": [b[5], b[6]] });
    }
    if b.len() < 44 || b[0] != 22 || b[5] != 2 {
        return json!({ "first_record": b.first(), "server_hello": null });
    }
    let sid = b[43] as usize;
    let Some(suite) = b.get(44 + sid..46 + sid) else {
        return json!({ "server_hello": "truncated" });
    };
    let version = match [b[9], b[10]] {
        [3, 3] => "TLS 1.2".to_string(),
        v => format!("0x{}", hex::encode(v)),
    };
    let name = match [suite[0], suite[1]] {
        [0xc0, 0x2f] => "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256".to_string(),
        [0xc0, 0x2b] => "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256".to_string(),
        s => format!("0x{}", hex::encode(s)),
    };
    json!({ "version": version, "cipher_suite": name })
}

/// Runs `f` with the calling thread allowed only the first `n` of its CPUs.
/// tlsn starts its executor's worker threads when a session is created, one
/// per CPU the thread may use, so the session gets `n` workers. Afterwards
/// the calling thread and the workers may use every CPU again: only the
/// number of workers is limited, not where they run.
#[cfg(target_os = "linux")]
pub fn with_cpus<T>(n: u16, f: impl FnOnce() -> T) -> Result<T> {
    let all = get_cpus(0)?;
    // SAFETY: cpu_set_t is plain data; CPU_ISSET and CPU_SET index within it.
    let mut few: libc::cpu_set_t = unsafe { std::mem::zeroed() };
    let mut k = 0;
    for c in 0..libc::CPU_SETSIZE as usize {
        if k < n && unsafe { libc::CPU_ISSET(c, &all) } {
            unsafe { libc::CPU_SET(c, &mut few) };
            k += 1;
        }
    }
    let before = threads()?;
    set_cpus(0, &few)?;
    let out = f();
    set_cpus(0, &all)?;
    // The workers are the threads that appeared meanwhile. They are found by
    // ID, not name: a new thread names itself only once it runs.
    for tid in threads()?.difference(&before) {
        // A thread that has already exited needs nothing.
        if let Err(e) = set_cpus(*tid, &all)
            && std::path::Path::new(&format!("/proc/self/task/{tid}")).exists()
        {
            return Err(e);
        }
    }
    Ok(out)
}

/// Elsewhere the executor starts one worker per CPU.
#[cfg(not(target_os = "linux"))]
pub fn with_cpus<T>(_n: u16, f: impl FnOnce() -> T) -> Result<T> {
    Ok(f())
}

#[cfg(target_os = "linux")]
fn threads() -> Result<std::collections::BTreeSet<libc::pid_t>> {
    let mut tids = std::collections::BTreeSet::new();
    for task in std::fs::read_dir("/proc/self/task")? {
        tids.insert(task?.file_name().to_string_lossy().parse()?);
    }
    Ok(tids)
}

#[cfg(target_os = "linux")]
fn get_cpus(tid: libc::pid_t) -> Result<libc::cpu_set_t> {
    // SAFETY: the kernel writes at most size_of::<cpu_set_t>() bytes into it.
    unsafe {
        let mut set: libc::cpu_set_t = std::mem::zeroed();
        if libc::sched_getaffinity(tid, std::mem::size_of::<libc::cpu_set_t>(), &mut set) != 0 {
            bail!("reading the CPU set: {}", std::io::Error::last_os_error());
        }
        Ok(set)
    }
}

#[cfg(target_os = "linux")]
fn set_cpus(tid: libc::pid_t, set: &libc::cpu_set_t) -> Result<()> {
    // SAFETY: the kernel reads size_of::<cpu_set_t>() bytes from it.
    if unsafe { libc::sched_setaffinity(tid, std::mem::size_of::<libc::cpu_set_t>(), set) } != 0 {
        bail!("setting the CPU set of thread {tid}: {}", std::io::Error::last_os_error());
    }
    Ok(())
}

/// The cores a witness bounded to N threads is pinned to, and how they were
/// chosen.
pub struct Pinned {
    /// Empty where pinning is not available.
    pub cpus: Vec<usize>,
    pub how: String,
    /// CPUs the process was allowed before pinning.
    pub allowed: Option<usize>,
}

/// Pins the whole process to `n` cores: the ones `named` (from --cpus), or
/// else a choice made from the CPUs the process is allowed. The choice is
/// the last NUMA node that has `n` allowed physical cores, and on it the
/// lowest-numbered ones, one hardware thread each; failing that, the last
/// node with `n` allowed hardware threads, physical cores first; failing
/// that, the same order across nodes. The last node, so that CPU 0 and its
/// node's housekeeping are avoided where there is a choice. Must run before
/// any other thread starts, so every thread inherits the set.
#[cfg(target_os = "linux")]
pub fn pin(n: u16, named: Option<&str>) -> Result<Pinned> {
    let all = get_cpus(0)?;
    let allowed: Vec<usize> = (0..libc::CPU_SETSIZE as usize)
        // SAFETY: c is within the set.
        .filter(|&c| unsafe { libc::CPU_ISSET(c, &all) })
        .collect();
    let n = n as usize;
    let (cpus, how) = match named {
        Some(list) => {
            let cpus = parse_cpu_list(list)?;
            if cpus.len() != n {
                bail!("--cpus {list} names {} CPUs; --threads is {n}", cpus.len());
            }
            if let Some(c) = cpus.iter().find(|c| !allowed.contains(c)) {
                bail!("--cpus {list}: CPU {c} is not among the {} this process may use", allowed.len());
            }
            (cpus, "named by --cpus".to_string())
        }
        None => choose(n, &allowed)?,
    };
    // SAFETY: cpu_set_t is plain data; CPU_SET indexes within it.
    let mut set: libc::cpu_set_t = unsafe { std::mem::zeroed() };
    for &c in &cpus {
        unsafe { libc::CPU_SET(c, &mut set) };
    }
    set_cpus(0, &set)?;
    Ok(Pinned { cpus, how, allowed: Some(allowed.len()) })
}

#[cfg(not(target_os = "linux"))]
pub fn pin(_n: u16, named: Option<&str>) -> Result<Pinned> {
    if named.is_some() {
        bail!("--cpus: pinning is not available on this platform");
    }
    Ok(Pinned { cpus: vec![], how: "not available on this platform; threads bounded only".into(), allowed: None })
}

#[cfg(target_os = "linux")]
fn choose(n: usize, allowed: &[usize]) -> Result<(Vec<usize>, String)> {
    if allowed.len() < n {
        bail!("--threads {n}: this process may use only {} CPUs", allowed.len());
    }
    let read = |p: String| std::fs::read_to_string(p).ok().and_then(|s| parse_cpu_list(s.trim()).ok());
    // NUMA nodes in order, each with its allowed CPUs.
    let mut nodes: Vec<(usize, Vec<usize>)> = std::fs::read_dir("/sys/devices/system/node")
        .into_iter()
        .flatten()
        .flatten()
        .filter_map(|e| {
            let k: usize = e.file_name().to_str()?.strip_prefix("node")?.parse().ok()?;
            let cpus = read(format!("/sys/devices/system/node/node{k}/cpulist"))?;
            Some((k, cpus.into_iter().filter(|c| allowed.contains(c)).collect()))
        })
        .collect();
    nodes.sort();
    // An allowed CPU is a physical core's first thread when no lower allowed
    // CPU shares that core.
    let first_thread = |c: usize| {
        read(format!("/sys/devices/system/cpu/cpu{c}/topology/thread_siblings_list"))
            .is_none_or(|sib| !sib.iter().any(|s| *s < c && allowed.contains(s)))
    };
    // Physical cores first, then their sibling threads, each by number.
    let ordered = |cpus: &[usize]| {
        let mut v = cpus.to_vec();
        v.sort_by_key(|&c| (!first_thread(c), c));
        v
    };
    for (k, cpus) in nodes.iter().rev() {
        let cores: Vec<usize> = cpus.iter().copied().filter(|&c| first_thread(c)).collect();
        if cores.len() >= n {
            return Ok((cores[..n].to_vec(), format!("node{k}, one hardware thread per physical core")));
        }
    }
    for (k, cpus) in nodes.iter().rev() {
        if cpus.len() >= n {
            return Ok((ordered(cpus)[..n].to_vec(), format!("node{k}, sibling hardware threads included")));
        }
    }
    let how = if nodes.is_empty() { "no NUMA information" } else { "across NUMA nodes" };
    Ok((ordered(allowed)[..n].to_vec(), how.to_string()))
}

/// A CPU list such as `16-19` or `0,2,4-6`, in the order given, without
/// repeats.
pub fn parse_cpu_list(list: &str) -> Result<Vec<usize>> {
    let mut cpus = Vec::new();
    for part in list.split(',').filter(|p| !p.is_empty()) {
        let (a, b) = part.split_once('-').unwrap_or((part, part));
        let (a, b): (usize, usize) = (a.trim().parse()?, b.trim().parse()?);
        if a > b {
            bail!("CPU range {part} runs backwards");
        }
        for c in a..=b {
            if cpus.contains(&c) {
                bail!("CPU {c} is named twice");
            }
            cpus.push(c);
        }
    }
    if cpus.is_empty() {
        bail!("no CPUs in {list:?}");
    }
    Ok(cpus)
}

/// `cpus` as a list such as `14-17`.
pub fn cpu_list(cpus: &[usize]) -> String {
    let mut out: Vec<String> = Vec::new();
    let mut i = 0;
    while i < cpus.len() {
        let mut j = i;
        while j + 1 < cpus.len() && cpus[j + 1] == cpus[j] + 1 {
            j += 1;
        }
        out.push(if i == j { cpus[i].to_string() } else { format!("{}-{}", cpus[i], cpus[j]) });
        i = j + 1;
    }
    out.join(",")
}
