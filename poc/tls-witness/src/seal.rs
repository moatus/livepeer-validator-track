//! Seal: the customer's signed statement of the call it wants made, written
//! before the call. The prover refuses a request file that does not match it,
//! and the checker compares it with the verdict.

use std::{fs, path::Path};

use anyhow::{Context, Result, anyhow, bail};
use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::{
    SealArgs, http,
    record::{load_or_create_key, now_rfc3339, random_bytes, sha256_hex, sign, verify_signature, write_json},
};

#[derive(Serialize, Deserialize, Clone)]
pub struct Seal {
    pub v: u32,
    pub job_id: String,
    pub nonce: String,
    pub created_at: String,
    pub method: String,
    pub host: String,
    pub path: String,
    pub body_sha256: String,
    pub customer_pub: String,
    #[serde(default)]
    pub sig: String,
}

/// Job ids travel in the `X-Job-Id` header and in file names.
pub fn check_job_id(job_id: &str) -> Result<()> {
    let ok = (1..=64).contains(&job_id.len())
        && job_id.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_');
    if !ok {
        bail!("job id {job_id:?} must be 1 to 64 characters of A-Z, a-z, 0-9, '-' or '_'");
    }
    Ok(())
}

pub fn read_request(path: &Path) -> Result<http::RequestFile> {
    let text = fs::read(path).with_context(|| format!("reading {}", path.display()))?;
    serde_json::from_slice(&text).with_context(|| format!("parsing request file {}", path.display()))
}

pub fn run(args: SealArgs) -> Result<()> {
    check_job_id(&args.job_id)?;
    let req = read_request(&args.request)?;
    let key = load_or_create_key(&args.key)?;
    let seal = Seal {
        v: 1,
        job_id: args.job_id,
        nonce: hex::encode(random_bytes::<16>()?),
        created_at: now_rfc3339(),
        method: req.method.clone(),
        host: req.host.clone(),
        path: req.path.clone(),
        body_sha256: sha256_hex(req.body_bytes()),
        customer_pub: String::new(),
        sig: String::new(),
    };
    let mut value = serde_json::to_value(&seal)?;
    sign(&mut value, "customer_pub", &key);
    write_json(&args.out, &value)?;
    println!("seal:    {}", args.out.display());
    println!("job_id:  {}", seal.job_id);
    println!("body:    {}", seal.body_sha256);
    println!("customer_pub: {}", value["customer_pub"].as_str().unwrap_or_default());
    Ok(())
}

/// Reads a seal and checks its signature against the key it names.
pub fn load(path: &Path) -> Result<(Seal, Value)> {
    let text = fs::read(path).with_context(|| format!("reading seal {}", path.display()))?;
    let value: Value = serde_json::from_slice(&text).with_context(|| format!("parsing seal {}", path.display()))?;
    verify_signature(&value, "customer_pub").map_err(|e| anyhow!("seal {}: {e}", path.display()))?;
    let seal: Seal = serde_json::from_value(value.clone()).with_context(|| format!("reading seal {}", path.display()))?;
    Ok((seal, value))
}

/// The fields where the seal and the request file disagree, each with both
/// values.
pub fn mismatches(seal: &Seal, req: &http::RequestFile) -> Vec<String> {
    let body_sha256 = sha256_hex(req.body_bytes());
    let pairs = [
        ("method", &seal.method, &req.method),
        ("host", &seal.host, &req.host),
        ("path", &seal.path, &req.path),
        ("body_sha256", &seal.body_sha256, &body_sha256),
    ];
    pairs
        .into_iter()
        .filter(|(_, sealed, requested)| sealed != requested)
        .map(|(field, sealed, requested)| format!("{field} (seal {sealed}, request file {requested})"))
        .collect()
}
