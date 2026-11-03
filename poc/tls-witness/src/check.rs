//! Checker: for one customer's receipt, shows that its exchange record is a
//! leaf under the root the session verdict signs, then walks the links from
//! the witness's signature to the delivered file, in order, and reports PASS
//! or the first step that fails. Given an epoch report and its paths file, it
//! also shows that the session's root is in the epoch's. Reads only the files
//! it is given and makes no network calls. A PASS appends the job to the
//! ledger.

use std::{
    fs,
    io::{Read, Write},
};

use anyhow::{Context, Result, anyhow, bail};
use serde_json::{Value, json};

use crate::{
    CheckArgs, Profile, merkle,
    record::{ExchangeRecord, Receipt, Verdict, now_rfc3339, sha256_hex, verify_signature},
    seal::{self, Seal},
    zk,
};

/// Returns whether the check passed.
pub fn run(args: CheckArgs) -> Result<bool> {
    if args.evidence.is_some() {
        return crate::router::check(&args);
    }
    if args.receipt.is_none()
        || args.seal.is_none()
        || args.delivered.is_none()
        || args.verifier_pub.is_none()
        || args.ledger.is_none()
    {
        bail!("sealed check requires receipt, seal, delivered, verifier-pub and ledger");
    }
    let mut passed = Vec::new();
    let mut delivered = String::new();
    let mut kind = None;
    let failure = links(&args, &mut passed, &mut delivered, &mut kind);
    let receipt = args.receipt.as_ref().unwrap().display().to_string();
    let report = match &failure {
        None => {
            json!({ "result": "PASS", "receipt": receipt, "passed": passed, "delivered": delivered })
        }
        Some((link, reason)) => json!({
            "result": "FAIL",
            "receipt": receipt,
            "link": link,
            "reason": reason,
            "passed": passed,
        }),
    };
    let mut report = report;
    report["profile"] = json!(kind);
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(failure.is_none())
}

type Failure = Option<(&'static str, String)>;

fn links(
    args: &CheckArgs,
    passed: &mut Vec<&'static str>,
    delivered: &mut String,
    kind: &mut Option<Profile>,
) -> Failure {
    let mut link = |name: &'static str, result: Result<()>| -> Failure {
        match result {
            Ok(()) => {
                passed.push(name);
                None
            }
            Err(e) => Some((name, format!("{e:#}"))),
        }
    };

    let mut receipt = None;
    if let Some(f) = link("inclusion", inclusion(args).map(|r| receipt = Some(r))) {
        return Some(f);
    }
    let (receipt, verdict) = receipt.expect("set when the link passed");
    if let Some(f) = link(
        "witness_signature",
        witness_signature(args, &receipt.verdict),
    ) {
        return Some(f);
    }
    let handling = verdict.profile;
    *kind = Some(handling);
    let verdict = Signed {
        profile: handling,
        server_name: verdict.server_name,
        sig: verdict.sig,
        root: verdict.root,
        session_id: verdict.session_id,
        ex: receipt.record,
    };
    let mut seal = None;
    if let Some(f) = link(
        "customer_seal",
        seal::load(args.seal.as_ref().unwrap()).map(|(s, _)| seal = Some(s)),
    ) {
        return Some(f);
    }
    let seal = seal.expect("set when the link passed");
    if let Some(f) = link("destination", destination(args, &verdict, &seal)) {
        return Some(f);
    }
    if let Some(f) = link("request_match", request_match(args, &verdict, &seal)) {
        return Some(f);
    }
    if let Some(f) = link(
        "response_delivery",
        response_delivery(args, &verdict).map(|d| *delivered = d),
    ) {
        return Some(f);
    }
    if let (Some(report), Some(paths)) = (&args.epoch, &args.epoch_paths)
        && let Some(f) = link("epoch", epoch(args, report, paths, &verdict))
    {
        return Some(f);
    }
    if let Some(f) = link("duplicate", duplicate(args, &verdict, &seal)) {
        return Some(f);
    }
    None
}

/// The verdict's server identity and root, and the one exchange record the
/// receipt proves under it.
struct Signed {
    profile: Profile,
    server_name: String,
    sig: String,
    root: String,
    session_id: String,
    ex: ExchangeRecord,
}

/// The receipt's record, hashed, and its path give the root the verdict
/// carries, at the record's own place among the verdict's leaves. Whether
/// the witness signed that root is the next step.
fn inclusion(args: &CheckArgs) -> Result<(Receipt, Verdict)> {
    let text = fs::read(args.receipt.as_ref().unwrap())
        .with_context(|| format!("reading {}", args.receipt.as_ref().unwrap().display()))?;
    let receipt: Receipt = serde_json::from_slice(&text).context("the receipt is not a receipt")?;
    let verdict: Verdict = serde_json::from_value(receipt.verdict.clone())
        .context("the receipt's verdict has an unexpected shape")?;
    let record = &receipt.record;
    if record.outcome != "verified" {
        bail!(
            "the exchange record's outcome is {:?}, not \"verified\"",
            record.outcome
        );
    }
    let index = record
        .n
        .checked_sub(1)
        .ok_or_else(|| anyhow!("the exchange record's n is 0; exchanges count from 1"))?;
    let path = receipt
        .path
        .iter()
        .map(|h| merkle::from_hex(h))
        .collect::<Result<Vec<_>>>()
        .context("the receipt's path")?;
    let root = merkle::root_from_path(record.leaf()?, index, verdict.exchanges, &path)
        .with_context(|| {
            format!(
                "exchange {} of the verdict's {}",
                record.n, verdict.exchanges
            )
        })?;
    if hex::encode(root) != verdict.root {
        bail!(
            "exchange {} of {} with this path hashes to root {}, but the verdict's root is {}",
            record.n,
            verdict.exchanges,
            hex::encode(root),
            verdict.root
        );
    }
    Ok((receipt, verdict))
}

fn expected_pub(args: &CheckArgs) -> Result<String> {
    let text = fs::read_to_string(args.verifier_pub.as_ref().unwrap())
        .with_context(|| format!("reading {}", args.verifier_pub.as_ref().unwrap().display()))?;
    Ok(text.trim().to_string())
}

/// The verdict is signed by the expected verifier, over every field as
/// written, the root included.
fn witness_signature(args: &CheckArgs, verdict: &Value) -> Result<()> {
    let expected = expected_pub(args)?;
    if verdict["verifier_pub"].as_str() != Some(expected.as_str()) {
        bail!(
            "the verdict is signed by {}, not the expected verifier {expected}",
            verdict["verifier_pub"]
        );
    }
    verify_signature(verdict, "verifier_pub").map_err(|e| anyhow!("verdict {e}"))
}

/// The epoch report is signed by the same verifier, and the session's root,
/// with its path from the paths file, gives the report's root.
fn epoch(
    args: &CheckArgs,
    report: &std::path::Path,
    paths: &std::path::Path,
    verdict: &Signed,
) -> Result<()> {
    let read = |p: &std::path::Path| -> Result<Value> {
        let text = fs::read(p).with_context(|| format!("reading {}", p.display()))?;
        serde_json::from_slice(&text).with_context(|| format!("{} is not JSON", p.display()))
    };
    let (report, paths) = (read(report)?, read(paths)?);
    let expected = expected_pub(args)?;
    if report["verifier_pub"].as_str() != Some(expected.as_str()) {
        bail!(
            "the epoch report is signed by {}, not the expected verifier {expected}",
            report["verifier_pub"]
        );
    }
    verify_signature(&report, "verifier_pub").map_err(|e| anyhow!("epoch report {e}"))?;
    let epoch_root = report["root"].as_str().unwrap_or_default();
    let leaves = report["leaves"]
        .as_u64()
        .ok_or_else(|| anyhow!("the epoch report has no leaf count"))? as usize;
    let entry = paths["sessions"]
        .as_array()
        .into_iter()
        .flatten()
        .find(|s| s["session_id"] == verdict.session_id.as_str())
        .ok_or_else(|| anyhow!("the paths file has no session {}", verdict.session_id))?;
    if entry["root"] != verdict.root.as_str() {
        bail!(
            "the paths file gives session {} root {}, the verdict {}",
            verdict.session_id,
            entry["root"],
            verdict.root
        );
    }
    let index = entry["index"]
        .as_u64()
        .ok_or_else(|| anyhow!("the paths entry has no index"))? as usize;
    let path = entry["path"]
        .as_array()
        .into_iter()
        .flatten()
        .map(|h| merkle::from_hex(h.as_str().unwrap_or_default()))
        .collect::<Result<Vec<_>>>()
        .context("the session's epoch path")?;
    let root = merkle::root_from_path(merkle::from_hex(&verdict.root)?, index, leaves, &path)
        .with_context(|| format!("session {} of the epoch's {leaves}", index + 1))?;
    if hex::encode(root) != epoch_root {
        bail!(
            "session {} with this path hashes to epoch root {}, but the report's root is {epoch_root}",
            verdict.session_id,
            hex::encode(root)
        );
    }
    Ok(())
}

fn destination(args: &CheckArgs, verdict: &Signed, seal: &Seal) -> Result<()> {
    if verdict.server_name != args.expect_host {
        bail!(
            "the witness validated a certificate for {}, not {}",
            verdict.server_name,
            args.expect_host
        );
    }
    if seal.host != verdict.ex.request.host || seal.host != verdict.server_name {
        bail!(
            "the seal names host {}, the verdict {} (certificate for {})",
            seal.host,
            verdict.ex.request.host,
            verdict.server_name
        );
    }
    if seal.path != verdict.ex.request.path {
        bail!(
            "the seal names path {}, the verdict {}",
            seal.path,
            verdict.ex.request.path
        );
    }
    Ok(())
}

fn request_match(args: &CheckArgs, signed: &Signed, seal: &Seal) -> Result<()> {
    let verdict = &signed.ex;
    if seal.job_id != verdict.job_id {
        bail!(
            "the seal's job_id is {}, the verdict's {}",
            seal.job_id,
            verdict.job_id
        );
    }
    if seal.method != verdict.request.method {
        bail!(
            "the seal's method is {}, the verdict's {}",
            seal.method,
            verdict.request.method
        );
    }
    if seal.body_sha256 != verdict.request.body_sha256 {
        bail!(
            "the seal's body_sha256 is {}, the verdict's {}",
            seal.body_sha256,
            verdict.request.body_sha256
        );
    }
    if signed.profile != Profile::CredentialHidden {
        if !args.accept_revealed {
            bail!("revealed credential handling requires --accept-revealed");
        }
        if verdict.request.withheld.is_some() {
            bail!("revealed verdict must not contain request.withheld");
        }
        return Ok(());
    }
    // Without the proof, the withheld bytes could have added a header or
    // reframed the body, so the verdict's request is not the one sent.
    match &verdict.request.withheld {
        None => bail!("the verdict does not record a no-CR/LF proof for the withheld bytes"),
        Some(w) if w.start >= w.end || !matches!(w.header.as_str(), "authorization" | "x-api-key") => bail!("invalid credential placement or withheld range"),
        Some(w) if !zk::known(&w.no_cr_lf) => bail!(
            "the verdict's no-CR/LF proof used circuit {}, not one built into this checker",
            w.no_cr_lf
        ),
        Some(_) => Ok(()),
    }
}

/// The delivered file must be the witnessed response body, or one of the
/// base64 images inline in it as decoded by the witness. Returns which.
fn response_delivery(args: &CheckArgs, verdict: &Signed) -> Result<String> {
    let verdict = &verdict.ex;
    let delivered = fs::read(args.delivered.as_ref().unwrap())
        .with_context(|| format!("reading {}", args.delivered.as_ref().unwrap().display()))?;
    let hash = sha256_hex(&delivered);
    if hash == verdict.response.body_sha256 {
        return Ok("response body".into());
    }
    if let Some((i, image)) = verdict
        .response
        .images
        .iter()
        .enumerate()
        .find(|(_, im)| im.sha256 == hash)
    {
        return Ok(format!(
            "image {i} decoded from the response body ({}, {} bytes)",
            image.media_type, image.bytes
        ));
    }
    let images = match verdict.response.images.len() {
        0 => String::new(),
        n => format!(", nor any of its {n} inline images"),
    };
    bail!(
        "the delivered file has sha256 {hash} ({} bytes); the witnessed response has {} ({} bytes){images}",
        delivered.len(),
        verdict.response.body_sha256,
        verdict.response.body_bytes
    )
}

/// One JSON object per line; a job_id or nonce seen before fails the check.
/// The ledger stays locked from the read to the append, so checks of the same
/// job running at once cannot both pass.
fn duplicate(args: &CheckArgs, verdict: &Signed, seal: &Seal) -> Result<()> {
    let (sig, verdict_root) = (&verdict.sig, &verdict.root);
    let verdict = &verdict.ex;
    let ledger = args.ledger.as_ref().unwrap();
    let mut file = fs::OpenOptions::new()
        .read(true)
        .append(true)
        .create(true)
        .open(ledger)
        .with_context(|| format!("opening ledger {}", ledger.display()))?;
    file.lock()
        .with_context(|| format!("locking ledger {}", ledger.display()))?;
    let mut text = String::new();
    file.read_to_string(&mut text)
        .with_context(|| format!("reading ledger {}", ledger.display()))?;
    for (n, line) in text
        .lines()
        .enumerate()
        .filter(|(_, l)| !l.trim().is_empty())
    {
        let entry: Value = serde_json::from_str(line)
            .with_context(|| format!("ledger {} line {} is not JSON", ledger.display(), n + 1))?;
        if entry["job_id"] == verdict.job_id.as_str() {
            bail!(
                "job_id {} is already in the ledger (line {})",
                verdict.job_id,
                n + 1
            );
        }
        if entry["nonce"] == seal.nonce.as_str() {
            bail!(
                "nonce {} is already in the ledger (line {})",
                seal.nonce,
                n + 1
            );
        }
    }
    let entry = json!({
        "job_id": verdict.job_id,
        "nonce": seal.nonce,
        "response_sha256": verdict.response.body_sha256,
        "verdict_sig": sig,
        "session_root": verdict_root,
        "exchange": verdict.n,
        "checked_at": now_rfc3339(),
    });
    // The whole line in one write, not one write per JSON token.
    file.write_all(format!("{entry}\n").as_bytes())
        .with_context(|| format!("writing ledger {}", ledger.display()))
}
