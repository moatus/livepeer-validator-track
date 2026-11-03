use serde_json::Value;
use std::{
    fs,
    io::{Read, Write},
    net::{TcpListener, TcpStream},
    path::PathBuf,
    process::{Child, Command, Stdio},
    time::{Duration, Instant},
};

const BIN: &str = env!("CARGO_BIN_EXE_witness");

#[test]
fn committed_evidence_cases() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("samples/evidence");
    for case in fs::read_dir(root).unwrap() {
        let dir = case.unwrap().path();
        if !dir.is_dir() {
            continue;
        }
        let expected: Value =
            serde_json::from_slice(&fs::read(dir.join("expected.json")).unwrap()).unwrap();
        let output = Command::new(BIN)
            .args(["check", "--evidence"])
            .arg(dir.join("package.json"))
            .arg("--client-request")
            .arg(dir.join("request.http"))
            .arg("--client-response")
            .arg(dir.join("response.http"))
            .arg("--trust-list")
            .arg(dir.join("trust.json"))
            .output()
            .unwrap();
        let got: Value = serde_json::from_slice(&output.stdout).unwrap();
        assert_eq!(
            got["result"],
            expected["result"],
            "{}: {got}",
            dir.display()
        );
        assert_eq!(got["link"], expected["link"], "{}: {got}", dir.display());
        assert_eq!(got["profile"], expected["profile"], "{}: {got}", dir.display());
        assert_eq!(output.status.success(), expected["result"] == "PASS");
        if output.status.success() {
            let package: Value =
                serde_json::from_slice(&fs::read(dir.join("package.json")).unwrap()).unwrap();
            assert_eq!(
                got["witness_time"],
                if package["kind"] == "job" {
                    package["chain"].as_array().unwrap().last().unwrap()["receipt"]["verdict"]["verified_at"].clone()
                } else { package["receipt"]["verdict"]["verified_at"].clone() }
            );
        }
    }
}

#[test]
fn evidence_rejects_unused_flags() {
    for extra in [
        vec!["--ledger", "unused"],
        vec!["--epoch", "unused", "--epoch-paths", "unused"],
        vec!["--delivered", "unused"],
        vec!["--verifier-pub", "unused"],
        vec!["--accept-revealed"],
        vec!["--expect-host", "openrouter.ai"],
        vec!["--seal", "unused"],
    ] {
        let output = Command::new(BIN)
            .args(["check", "--evidence", "unused"])
            .args(&extra)
            .output()
            .unwrap();
        assert_eq!(output.status.code(), Some(2), "{extra:?}");
        assert!(String::from_utf8_lossy(&output.stderr).contains("cannot be used with"));
    }
}

struct Stop(Child);
impl Drop for Stop {
    fn drop(&mut self) {
        let _ = self.0.kill();
        let _ = self.0.wait();
    }
}
fn send(s: &mut TcpStream, bytes: &[u8]) {
    s.write_all(&(bytes.len() as u32).to_be_bytes()).unwrap();
    s.write_all(bytes).unwrap();
}
fn recv(s: &mut TcpStream) -> Vec<u8> {
    let mut n = [0; 4];
    s.read_exact(&mut n).unwrap();
    let mut data = vec![0; u32::from_be_bytes(n) as usize];
    s.read_exact(&mut data).unwrap();
    data
}

#[test]
fn default_allowlist_refuses_fixture_before_dial() {
    let upstream = TcpListener::bind("127.0.0.1:0").unwrap();
    upstream.set_nonblocking(true).unwrap();
    let reserve = TcpListener::bind("127.0.0.1:0").unwrap();
    let addr = reserve.local_addr().unwrap();
    drop(reserve);
    let dir = std::env::temp_dir().join(format!("tlsw-ch-witness-allowlist-{}", std::process::id()));
    fs::create_dir_all(&dir).unwrap();
    let mut child = Stop(
        Command::new(BIN)
            .args([
                "verifier",
                "--profile",
                "credential-sequence",
                "--roots",
                "webpki",
                "--threads",
                "1",
                "--listen",
            ])
            .arg(addr.to_string())
            .arg("--key")
            .arg(dir.join("verifier.key"))
            .arg("--record-dir")
            .arg(dir.join("records"))
            .arg("--resolve")
            .arg(format!("test-server.io={}", upstream.local_addr().unwrap()))
            .env_remove("OPENROUTER_API_KEY")
            .env_remove("OPENROUTER_MANAGEMENT_KEY")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .unwrap(),
    );
    let deadline = Instant::now() + Duration::from_secs(15);
    let mut socket = loop {
        if let Ok(s) = TcpStream::connect(addr) {
            break s;
        }
        assert!(child.0.try_wait().unwrap().is_none(), "verifier exited");
        assert!(Instant::now() < deadline, "verifier did not listen");
        std::thread::sleep(Duration::from_millis(20));
    };
    socket
        .set_read_timeout(Some(Duration::from_secs(5)))
        .unwrap();
    send(&mut socket, b"credential-sequence");
    assert_eq!(recv(&mut socket), b"credential-sequence");
    let _session = recv(&mut socket);
    send(&mut socket, b"null");
    send(&mut socket, b"test-server.io");
    assert_eq!(
        recv(&mut socket),
        b"refused: server name is not on the upstream allowlist"
    );
    assert_eq!(
        upstream.accept().unwrap_err().kind(),
        std::io::ErrorKind::WouldBlock
    );
}

// A valid job must authenticate every session, even when all cross-step targets
// and body hashes agree. CLI sample checks alone do not mutate every position.
#[test]
fn job_authenticates_each_witness_signature() {
    let source = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("samples/evidence/job-complete");
    let original: Value = serde_json::from_slice(&fs::read(source.join("package.json")).unwrap()).unwrap();
    let dir = std::env::temp_dir().join(format!("tlsw-ch-witness-job-signatures-{}",std::process::id()));
    fs::create_dir_all(&dir).unwrap();
    for i in 0..original["chain"].as_array().unwrap().len() {
        let mut package = original.clone();
        package["chain"][i]["receipt"]["verdict"]["mode"] = Value::String("tampered".into());
        let path = dir.join(format!("step-{i}.json"));
        fs::write(&path,serde_json::to_vec(&package).unwrap()).unwrap();
        let output = Command::new(BIN).args(["check","--evidence"]).arg(path)
            .arg("--client-request").arg(source.join("request.http"))
            .arg("--client-response").arg(source.join("response.http"))
            .arg("--trust-list").arg(source.join("trust.json")).output().unwrap();
        let got: Value = serde_json::from_slice(&output.stdout).unwrap();
        assert_eq!(got["link"],"witness_signature","step {i}: {got}");
        assert!(!output.status.success());
    }
}
