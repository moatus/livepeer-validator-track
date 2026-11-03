//! Refuses to build against a barretenberg library, compiled circuits or a
//! patched tlsn-mux or tlsn session channel other than the pinned ones.

use std::{env, fs, path::Path};

use sha2::{Digest, Sha256};

/// `libbb-external.a` from barretenberg-static-amd64-linux.tar.gz, release
/// v4.2.0-aztecnr-rc.2 of AztecProtocol/aztec-packages, the version
/// barretenberg-rs 4.2.0-aztecnr-rc.2 links.
const BB_LIB_SHA256: &str = "69e23cf1d3d1fe3875f4ab5d36a209a7308aad49096ad101e1366a0d8fbc09ce";
const BB_LIB_URL: &str = "https://github.com/AztecProtocol/aztec-packages/releases/download/v4.2.0-aztecnr-rc.2/barretenberg-static-amd64-linux.tar.gz";

/// `circuit/auth_value_<MAX>.json`: `nargo compile` (nargo 1.0.0-beta.19) of
/// `circuit/` with `global MAX` set to MAX (240 as committed; `mod tests`
/// dropped for the others, whose tests assume 240), trimmed with
/// `jq -c '{noir_version, hash, abi, bytecode}'`.
const CIRCUITS: [(&str, &str); 4] = [
    (
        "circuit/auth_value_240.json",
        "431064964f5d2f0f987d2f1a4d38e1c946065a0de9f9e2fbff2a09082a1edd1c",
    ),
    (
        "circuit/auth_value_640.json",
        "504c3254ea2da2cbbce48ca37953cb591710ad1b4a494ac5cb5858050d77ad3d",
    ),
    (
        "circuit/auth_value_1280.json",
        "a59c1d2d199d0ff0a660314fd08df73b417e9b1ebee23be7d30675474ff79c57",
    ),
    (
        "circuit/auth_value_2560.json",
        "f475261ee6fba85d17dddbd4d183fcc925ff791ceb3c6d969c078214af7dd342",
    ),
];

/// `src/lib.rs` of tlsn-mux at the revision tlsn v0.1.0-alpha.15 pins, with
/// `patch/tlsn-mux-stream-cap.diff` applied by `patch/apply.sh`.
const PATCHED_MUX: (&str, &str) = (
    "patch/apply.sh.out/tlsn-mux/src/lib.rs",
    "3cda73675714db13210b0b5e5248ac01cfd1cb291d8854e2723fc5d2e7bab69b",
);

/// tlsn session.rs with patch/tlsn-session-frame-limit.diff applied.
const PATCHED_SESSION: (&str, &str) = (
    "patch/apply.sh.out/tlsn/src/session.rs",
    "d3fccd8aa668b9888ce5ba3c7fb045ea672b11f8711db0ea8c162b0aafb12d2a",
);

fn sha256_of(path: &Path) -> Option<String> {
    fs::read(path).ok().map(|b| hex::encode(Sha256::digest(b)))
}

mod hex {
    pub fn encode(bytes: impl AsRef<[u8]>) -> String {
        bytes.as_ref().iter().map(|b| format!("{b:02x}")).collect()
    }
}

fn main() {
    println!("cargo:rerun-if-env-changed=BB_LIB_DIR");

    let dir = env::var("BB_LIB_DIR").unwrap_or_else(|_| panic!("BB_LIB_DIR is not set; see .cargo/config.toml"));
    let lib = Path::new(&dir).join("libbb-external.a");
    println!("cargo:rerun-if-changed={}", lib.display());
    match sha256_of(&lib) {
        Some(hash) if hash == BB_LIB_SHA256 => {}
        found => panic!(
            "{} has sha256 {}, expected the pinned {BB_LIB_SHA256}. Fetch it with:\n  \
             mkdir -p {dir} && curl -fL {BB_LIB_URL} | tar -xz -C {dir}",
            lib.display(),
            found.as_deref().unwrap_or("(missing)"),
        ),
    }

    for (mux, pinned) in [PATCHED_MUX, PATCHED_SESSION] {
        println!("cargo:rerun-if-changed={mux}");
        match sha256_of(Path::new(mux)) {
            Some(hash) if hash == pinned => {}
            found => panic!(
                "{mux} has sha256 {}, expected the patched {pinned}. Rebuild it with:\n  \
                 rm -r patch/apply.sh.out && sh patch/apply.sh",
                found.as_deref().unwrap_or("(missing)")
            ),
        }
    }

    for (circuit, pinned) in CIRCUITS {
        println!("cargo:rerun-if-changed={circuit}");
        match sha256_of(Path::new(circuit)) {
            Some(hash) if hash == pinned => {}
            found => panic!(
                "{circuit} has sha256 {}, expected the pinned {pinned}",
                found.as_deref().unwrap_or("(missing)")
            ),
        }
    }
}
