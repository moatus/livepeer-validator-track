//! The no-CR/LF proof over the withheld credential header values: a Noir circuit
//! proven with barretenberg's UltraHonk through noir-rs.
//!
//! tlsn commits to the withheld spans of a session as SHA-256 over their
//! bytes in order, then a 16-byte blinder. The circuit
//! (`circuit/src/main.nr`) proves knowledge of a value of the public length
//! whose commitment is the public hash and which holds no CR or LF; the value
//! is every withheld span joined, so one proof covers all of them. The circuit
//! is compiled at several bounds on the value's length, and both roles use the
//! smallest that fits: proving cost grows with the bound, not the value. Both
//! load the compiled circuits built into this binary and an SRS file pinned by
//! SHA-256; the verifier builds its verification keys from them.

use std::{
    path::Path,
    sync::{Mutex, OnceLock, RwLock},
    time::Instant,
};

use anyhow::{Context, Result, anyhow, bail};
use noir::barretenberg::{
    api,
    srs::{netsrs::NetSrs, setup_srs},
    utils::{compute_subgroup_size, get_circuit_size},
    verify::{get_ultra_honk_verification_key, verify_ultra_honk},
};
use serde_json::{Value, json};

use crate::record::{ms, sha256_hex};

/// Pinned by build.rs, smallest bound first.
const CIRCUIT_JSONS: [&str; 4] = [
    include_str!("../circuit/auth_value_240.json"),
    include_str!("../circuit/auth_value_640.json"),
    include_str!("../circuit/auth_value_1280.json"),
    include_str!("../circuit/auth_value_2560.json"),
];

/// The first 2,097,153 G1 points of Aztec's ceremony output,
/// https://crs.aztec.network/g1.dat: what the largest circuit needs. A
/// smaller circuit reads a prefix of it.
const SRS_URL: &str = "https://crs.aztec.network/g1.dat";
const SRS_BYTES: u64 = 134_217_792;
const SRS_SHA256: &str = "ea6069e3563ad79f186d1c0088499309cbdaeb54254346760ffec7fe15ae49cd";

const BLINDER_LEN: usize = 16;
/// Public inputs: the 32 hash bytes, then the value's length.
const PUBLIC_INPUTS: usize = 33;

// Only sizing/setup mutate process-global library state. Setup's high-level
// VK builder configures memory; SRS growth replaces the process-wide table.
// Proof/check calls hold shared access so neither mutation can overlap them.
// Do not use noir-rs's high-level prove wrapper here: it writes the non-atomic
// slow_low_memory global on EVERY call (api.rs:129-145 at pinned 0e4fdc9).
// Its lower-level API creates a fresh FfiBackend and local input/output buffers
// per call (api.rs:get_api; barretenberg-rs ffi.rs:Backend::call).
static LIBRARY: RwLock<()> = RwLock::new(());

/// One compiled circuit, as built into this binary.
pub struct Def {
    bytecode: String,
    /// Length of the circuit's private input: the longest value plus the blinder.
    input_len: usize,
    pub sha256: String,
    /// SRS points it needs, less one: dyadic gates times 8, rounded up to a
    /// power of two, as noir-rs's setup_srs_from_bytecode.
    subgroup: u32,
    gates: u32,
}

impl Def {
    pub fn max_value_len(&self) -> usize {
        self.input_len - BLINDER_LEN
    }

    fn about(&self) -> Value {
        json!({
            "circuit_sha256": self.sha256,
            "max_value_len": self.max_value_len(),
            "dyadic_gates": self.gates,
        })
    }
}

fn parse(text: &str) -> Result<Def> {
    let json: Value = serde_json::from_str(text).context("parsing a built-in circuit")?;
    let bytecode = json["bytecode"]
        .as_str()
        .ok_or_else(|| anyhow!("a built-in circuit has no bytecode"))?
        .to_string();
    let input_len = json["abi"]["parameters"]
        .as_array()
        .and_then(|params| params.iter().find(|p| p["name"] == "input"))
        .and_then(|p| p["type"]["length"].as_u64())
        .ok_or_else(|| anyhow!("a built-in circuit has no input array"))?
        as usize;
    let _library = LIBRARY.write().unwrap_or_else(|e| e.into_inner());
    let gates = get_circuit_size(&bytecode, false);
    if gates == 0 {
        bail!("barretenberg could not size a built-in circuit");
    }
    Ok(Def {
        bytecode,
        input_len,
        sha256: sha256_hex(text.as_bytes()),
        subgroup: compute_subgroup_size(gates * 8),
        gates,
    })
}

/// Built-in bounds and their definitions. Only a selected circuit is sized.
const BOUNDS: [usize; 4] = [240, 640, 1280, 2560];
static DEFS: [OnceLock<Result<Def, String>>; 4] = [const { OnceLock::new() }; 4];

/// The smallest built-in circuit that takes a value of `len` bytes.
pub fn circuit_for(len: usize) -> Result<&'static Def> {
    let index = BOUNDS.iter().position(|bound| len <= *bound)
        .ok_or_else(|| anyhow!("the withheld values are {len} bytes together; the largest no-CR/LF circuit takes {}", max_value_len()))?;
    DEFS[index].get_or_init(|| {
        let def = parse(CIRCUIT_JSONS[index]).map_err(|e| format!("{e:#}"))?;
        if def.max_value_len() != BOUNDS[index] {
            return Err("built-in circuit bound differs from its ABI".into());
        }
        Ok(def)
    }).as_ref().map_err(|e| anyhow!("{e}"))
}

/// First-use sizing can block on library setup and performs native work.
pub async fn select_circuit(len: usize) -> Result<&'static Def> {
    tokio::task::spawn_blocking(move || circuit_for(len))
        .await.context("sizing the selected circuit")?
}

pub fn max_value_len() -> usize {
    *BOUNDS.last().unwrap()
}

/// Whether `sha256` names a built-in circuit.
pub fn known(sha256: &str) -> bool {
    CIRCUIT_JSONS
        .iter()
        .any(|t| sha256_hex(t.as_bytes()) == sha256)
}

/// A circuit ready to prove or check: its verification key is built.
#[derive(Clone)]
pub struct Circuit {
    def: &'static Def,
    vk: Vec<u8>,
}

impl Circuit {
    pub fn def(&self) -> &'static Def {
        self.def
    }
}

/// The SRS file, checked against the pin.
#[derive(Clone)]
pub struct Srs {
    path: String,
    about: Value,
}

/// Checks the SRS file against the pin, fetching it to `path` first if it is
/// missing. Fast once the file is cached, so a prover can do it before it
/// sends anything.
pub fn srs(path: &Path) -> Result<Srs> {
    let t = Instant::now();
    let cpu = crate::record::cpu_seconds();
    let points = SRS_BYTES / 64;
    let mut fetched = Value::Null;
    if !path.exists() {
        let f = Instant::now();
        fetch_srs(path, points as u32)?;
        fetched = json!({ "url": SRS_URL, "ms": ms(f) });
    }
    let data =
        std::fs::read(path).with_context(|| format!("reading SRS file {}", path.display()))?;
    let hash = sha256_hex(&data);
    if data.len() as u64 != SRS_BYTES || hash != SRS_SHA256 {
        bail!(
            "SRS file {} is {} bytes with sha256 {hash}, not the pinned {SRS_BYTES} bytes with sha256 \
             {SRS_SHA256}; refusing it (delete the file to fetch it again)",
            path.display(),
            data.len()
        );
    }
    let about = json!({
        "srs_file": path,
        "srs_sha256": hash,
        "srs_fetched": fetched,
        "srs_check_ms": ms(t),
        "srs_check_cpu_s": crate::record::cpu_seconds() - cpu,
    });
    let path = path
        .to_str()
        .ok_or_else(|| anyhow!("SRS path is not UTF-8"))?
        .to_string();
    Ok(Srs { path, about })
}

impl Srs {
    /// Loads as much of the checked SRS as `def` needs and builds its
    /// verification key. Returns facts for the record.
    pub fn setup(&self, def: &'static Def) -> Result<(Circuit, Value)> {
        // barretenberg keeps one SRS for the process. It is loaded only when
        // it holds fewer points than `def` needs, so a circuit set up earlier
        // never finds it shrunk.
        static LOADED: Mutex<u32> = Mutex::new(0);
        let _library = LIBRARY.write().unwrap_or_else(|e| e.into_inner());
        if (def.subgroup as u64 + 1) * 64 > SRS_BYTES {
            bail!("selected circuit exceeds the pinned SRS");
        }
        let t = Instant::now();
        let cpu = crate::record::cpu_seconds();
        {
            let mut loaded = LOADED.lock().unwrap_or_else(|e| e.into_inner());
            if *loaded < def.subgroup {
                setup_srs(def.subgroup, Some(&self.path)).map_err(|e| anyhow!("loading the SRS: {e}"))?;
                *loaded = def.subgroup;
            }
        }
        let srs_ms = ms(t);
        let srs_cpu = crate::record::cpu_seconds() - cpu;
        let v = Instant::now();
        let vk_cpu = crate::record::cpu_seconds();
        let vk = get_ultra_honk_verification_key(&def.bytecode, false)
            .map_err(|e| anyhow!("verification key: {e}"))?;
        let mut about = def.about();
        about["srs_ms"] = json!(srs_ms);
        about["srs_cpu_s"] = json!(srs_cpu);
        about["vk_sha256"] = json!(sha256_hex(&vk));
        about["vk_ms"] = json!(ms(v));
        about["vk_cpu_s"] = json!(crate::record::cpu_seconds() - vk_cpu);
        Ok((Circuit { def, vk }, about))
    }

    pub fn about(&self) -> &Value {
        &self.about
    }
}

/// A witness retains at most one key for each of the four built-in bounds.
/// Misses are serialized; only SRS/VKs are retained, never session material.
pub struct Keys {
    srs: Srs,
    circuits: Mutex<Vec<(Circuit, Value)>>,
}

impl Keys {
    pub fn new(path: &Path) -> Result<Self> {
        Ok(Self { srs: srs(path)?, circuits: Mutex::new(Vec::new()) })
    }

    pub fn about(&self) -> Value {
        json!({"srs": self.srs.about(), "circuits": [], "loading": "on demand; at most four keys"})
    }

    pub fn circuit(&self, def: &'static Def) -> Result<(Circuit, Value)> {
        let mut circuits = self.circuits.lock().unwrap_or_else(|e| e.into_inner());
        if let Some((circuit, facts)) = circuits.iter().find(|(c, _)| c.def().sha256 == def.sha256) {
            let mut facts = facts.clone();
            facts["set_up_earlier"] = json!(true);
            return Ok((circuit.clone(), facts));
        }
        let (circuit, facts) = self.srs.setup(def)?;
        circuits.push((circuit.clone(), facts.clone()));
        Ok((circuit, facts))
    }
}

/// Downloads the needed prefix of Aztec's g1.dat. noir-rs panics on a network
/// error, so the panic is caught and returned as an error.
fn fetch_srs(path: &Path, points: u32) -> Result<()> {
    if let Some(dir) = path.parent() {
        std::fs::create_dir_all(dir)?;
    }
    let srs = std::panic::catch_unwind(|| NetSrs::new(points).to_srs())
        .map_err(|_| anyhow!("fetching the SRS from {SRS_URL} failed"))?;
    std::fs::write(path, &srs.g1_data).with_context(|| format!("writing {}", path.display()))
}

/// Proves that `value` holds no CR or LF and that SHA-256(value || blinder)
/// is `hash`. Witness order follows the circuit's ABI: committed_hash, len,
/// input.
pub fn prove(circuit: &Circuit, value: &[u8], blinder: &[u8], hash: &[u8]) -> Result<Vec<u8>> {
    if value.len() > circuit.def.max_value_len() {
        bail!(
            "the withheld value is {} bytes; the circuit takes at most {}",
            value.len(),
            circuit.def.max_value_len()
        );
    }
    let _library = LIBRARY.read().unwrap_or_else(|e| e.into_inner());
    let mut input = [value, blinder].concat();
    input.resize(circuit.def.input_len, 0);
    let mut witness: Vec<String> = hash.iter().map(|b| b.to_string()).collect();
    witness.push(value.len().to_string());
    witness.extend(input.iter().map(|b| b.to_string()));
    let refs: Vec<&str> = witness.iter().map(String::as_str).collect();
    let witness = noir::witness::from_vec_str_to_witness_map(refs).map_err(|e| anyhow!(e))?;
    // Same sequence/settings/encoding as noir-rs prove_ultra_honk, without
    // its per-call configure_memory(false, None). Srs::setup already configured
    // memory under exclusive access before this Circuit could be constructed.
    let solved = noir::execute::execute(&circuit.def.bytecode, witness)
        .map_err(|e| anyhow!("proving: {e}"))?;
    let solved = noir::witness::serialize_witness(solved).map_err(|e| anyhow!(e))?;
    let acir = noir::circuit::get_acir_buffer_uncompressed(&circuit.def.bytecode)
        .map_err(|e| anyhow!(e))?;
    let response = api::circuit_prove(
        &acir, &solved, &circuit.vk, &api::settings_ultra_honk_poseidon2(),
    ).map_err(|e| anyhow!("proving: {e}"))?;
    let mut proof = (response.public_inputs.len() as u32).to_be_bytes().to_vec();
    proof.extend(api::proof_fields_to_bytes(&response.public_inputs));
    proof.extend(api::proof_fields_to_bytes(&response.proof));
    Ok(proof)
}

/// The public inputs as the proof lays them out: one 32-byte big-endian field
/// element per hash byte, then the length.
fn public_inputs(hash: &[u8], len: usize) -> Vec<u8> {
    let mut out = Vec::with_capacity(PUBLIC_INPUTS * 32);
    for b in hash {
        out.extend_from_slice(&[0u8; 31]);
        out.push(*b);
    }
    out.extend_from_slice(&[0u8; 28]);
    out.extend_from_slice(&(len as u32).to_be_bytes());
    out
}

/// Accepts the proof only if its public inputs are exactly `hash` and `len`
/// and it verifies against the verification key built from this binary's
/// circuit for `len`.
pub fn check(circuit: &Circuit, proof: &[u8], hash: &[u8], len: usize) -> Result<()> {
    if hash.len() != 32 {
        bail!("the committed hash is {} bytes, not 32", hash.len());
    }
    let prefix = 4 + PUBLIC_INPUTS * 32;
    if proof.len() < prefix {
        bail!("the proof is {} bytes, shorter than its public inputs", proof.len());
    }
    let count = u32::from_be_bytes(proof[0..4].try_into()?) as usize;
    if count != PUBLIC_INPUTS {
        bail!("the proof has {count} public inputs, expected {PUBLIC_INPUTS}");
    }
    if proof[4..prefix] != public_inputs(hash, len)[..] {
        bail!("the proof's public inputs are not the committed hash and the withheld length");
    }
    let _library = LIBRARY.read().unwrap_or_else(|e| e.into_inner());
    let ok = verify_ultra_honk(proof.to_vec(), circuit.vk.clone()).map_err(|e| anyhow!("proof verification: {e}"))?;
    if !ok {
        bail!("the proof does not verify");
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use sha2::{Digest, Sha256};

    #[test]
    fn circuit_rejects_line_breaks_in_committed_value() -> Result<()> {
        // Exercise the actual pinned bytecode and production proving path.
        // The existing cached pin is mandatory: tests never fetch an SRS.
        let path = Path::new("target/srs/g1.dat");
        anyhow::ensure!(path.exists(), "local pinned SRS required for this test");
        let (circuit, _) = srs(path)?.setup(circuit_for(32)?)?;
        let blinder = [42; BLINDER_LEN];
        for value in [b"tlsw-fixture-valid".as_slice(), b"tlsw-fixture-\rinjected", b"tlsw-fixture-\ninjected"] {
            let hash = Sha256::digest([value, &blinder].concat());
            let result = prove(&circuit, value, &blinder, &hash);
            if value.contains(&13) || value.contains(&10) {
                let error = result.expect_err("circuit must refuse a committed line break");
                anyhow::ensure!(format!("{error:#}").contains("Failed assertion"), "unexpected circuit refusal: {error:#}");
            } else {
                check(&circuit, &result?, &hash, value.len())?;
            }
        }
        Ok(())
    }
}
