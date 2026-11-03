//! Epoch reports. Epochs are `--epoch-secs` long, counted from the Unix
//! epoch, and a session belongs to the epoch its final record was written
//! in. For each one the verifier signs, with its own key, a report built from
//! its own session records only: the sessions and exchanges by outcome, and
//! a Merkle root over the roots of the sessions it verified, in the order
//! their records were written. Beside each report it writes every verified
//! session's path to that root, so a receipt's session can be shown to be in
//! it.

use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};

use anyhow::{Context, Result, anyhow, bail};
use chrono::{DateTime, Utc};
use ed25519_dalek::SigningKey;
use serde_json::{Value, json};

use crate::{
    merkle,
    record::{now_ms_rfc3339, sign, write_json_atomic},
};

/// The outcome of a session record written at its start and not yet replaced.
pub const OPEN: &str = "open";

/// Every session outcome, so a report names each one even at zero.
pub const SESSION_OUTCOMES: [&str; 6] = ["verified", "unwitnessed", "aborted", "not_sent", "refused", "interrupted"];
const EXCHANGE_OUTCOMES: [&str; 2] = ["verified", "unwitnessed"];

/// Outcomes in which no request reached the server, so a session's exchange
/// count is known to be zero even when no request was parsed.
const NONE_SENT: [&str; 2] = ["not_sent", "refused"];

/// After an epoch ends, how long sessions finishing on the boundary get to
/// write their records before the report is built.
const GRACE: Duration = Duration::from_secs(2);

struct Session {
    id: String,
    outcome: String,
    recorded_ms: i64,
    root: Option<String>,
    exchanges: Vec<String>,
}

fn records(dir: &Path) -> Result<Vec<PathBuf>> {
    let mut out = Vec::new();
    for entry in fs::read_dir(dir).with_context(|| format!("reading {}", dir.display()))? {
        let path = entry?.path();
        if path.to_str().is_some_and(|p| p.ends_with(".record.json")) {
            out.push(path);
        }
    }
    out.sort();
    Ok(out)
}

fn read(path: &Path) -> Result<Value> {
    let text = fs::read_to_string(path).with_context(|| format!("reading {}", path.display()))?;
    serde_json::from_str(&text).with_context(|| format!("parsing {}", path.display()))
}

/// Rewrites every open session record as interrupted: the process that
/// wrote it stopped before the session ended. Assumes one verifier per
/// record directory, so a record open at startup is not another's live one.
pub fn close_interrupted(dir: &Path) -> Result<Vec<String>> {
    let mut closed = Vec::new();
    for path in records(dir)? {
        let mut record = read(&path)?;
        if record["outcome"] != OPEN {
            continue;
        }
        record["outcome"] = json!("interrupted");
        record["error"] = json!("the witness process stopped during the session; its record was found open at the next start");
        record["recorded_at"] = json!(now_ms_rfc3339());
        write_json_atomic(&path, &record)?;
        closed.push(record["detail"]["session_id"].as_str().unwrap_or_default().to_string());
    }
    Ok(closed)
}

/// Final session records written at or after `since` (by file time, with a
/// second's slack; the record's own `recorded_at` decides its epoch).
fn sessions(dir: &Path, since: Option<i64>) -> Result<Vec<Session>> {
    let mut out = Vec::new();
    for path in records(dir)? {
        if let Some(since) = since {
            let mtime = fs::metadata(&path)?.modified()?.duration_since(UNIX_EPOCH)?.as_secs() as i64;
            if mtime < since - 1 {
                continue;
            }
        }
        let record = read(&path)?;
        // Open records, and records from before records were dated, are no
        // epoch's.
        let Some(at) = record["recorded_at"].as_str() else {
            continue;
        };
        let recorded_ms = DateTime::parse_from_rfc3339(at)
            .with_context(|| format!("{}: recorded_at {at:?}", path.display()))?
            .timestamp_millis();
        let outcome = record["outcome"].as_str().unwrap_or_default().to_string();
        let root = record["detail"]["session_root"].as_str().map(str::to_string);
        if outcome == "verified" && root.is_none() {
            bail!("{}: a verified session with no session_root", path.display());
        }
        out.push(Session {
            id: record["detail"]["session_id"].as_str().unwrap_or_default().to_string(),
            outcome,
            recorded_ms,
            root,
            exchanges: record["exchanges"]
                .as_array()
                .map(|xs| xs.iter().map(|x| x["outcome"].as_str().unwrap_or_default().to_string()).collect())
                .unwrap_or_default(),
        });
    }
    Ok(out)
}

fn stamp(secs: i64) -> String {
    DateTime::<Utc>::from_timestamp(secs, 0)
        .map(|t| t.format("%Y%m%dT%H%M%SZ").to_string())
        .unwrap_or_default()
}

fn rfc3339(secs: i64) -> String {
    DateTime::<Utc>::from_timestamp(secs, 0)
        .map(|t| t.to_rfc3339_opts(chrono::SecondsFormat::Secs, true))
        .unwrap_or_default()
}

/// The report's file name; the paths file is the same with `.paths.json`.
pub fn report_name(start: i64, secs: u64) -> String {
    format!("epoch-{}-{secs}s", stamp(start))
}

/// Builds, signs and writes the report for the epoch from `start`, from
/// `all`, which may hold sessions of other epochs.
fn write(dir: &Path, secs: u64, start: i64, all: &[Session], key: &SigningKey, scan: Duration) -> Result<()> {
    let end = start + secs as i64;
    let mut ours: Vec<&Session> = all
        .iter()
        .filter(|s| s.recorded_ms >= start * 1000 && s.recorded_ms < end * 1000)
        .collect();
    ours.sort_by(|a, b| (a.recorded_ms, &a.id).cmp(&(b.recorded_ms, &b.id)));

    let mut by_outcome: BTreeMap<String, usize> = SESSION_OUTCOMES.iter().map(|o| (o.to_string(), 0)).collect();
    let mut exchanges: BTreeMap<String, usize> = EXCHANGE_OUTCOMES.iter().map(|o| (o.to_string(), 0)).collect();
    let mut unknown = 0;
    for s in &ours {
        *by_outcome.entry(s.outcome.clone()).or_default() += 1;
        for x in &s.exchanges {
            *exchanges.entry(x.clone()).or_default() += 1;
        }
        if s.exchanges.is_empty() && s.outcome != "verified" && !NONE_SENT.contains(&s.outcome.as_str()) {
            unknown += 1;
        }
    }
    let verified: Vec<&Session> = ours.iter().copied().filter(|s| s.outcome == "verified").collect();
    let t = Instant::now();
    let leaves = verified
        .iter()
        .map(|s| merkle::from_hex(s.root.as_deref().expect("checked when read")))
        .collect::<Result<Vec<_>>>()?;
    let root = merkle::root(&leaves);
    let paths: Vec<Value> = verified
        .iter()
        .zip(merkle::paths(&leaves))
        .enumerate()
        .map(|(i, (s, path))| {
            json!({
                "session_id": s.id,
                "root": s.root,
                "index": i,
                "path": path.iter().map(hex::encode).collect::<Vec<_>>(),
            })
        })
        .collect();
    let hash = t.elapsed();

    let name = report_name(start, secs);
    let mut report = json!({
        "v": 1,
        "start": rfc3339(start),
        "end": rfc3339(end),
        "epoch_secs": secs,
        "root": hex::encode(root),
        "leaves": leaves.len(),
        "sessions": by_outcome,
        "exchanges": exchanges,
        "sessions_exchanges_unknown": unknown,
        "written_at": now_ms_rfc3339(),
    });
    let t = Instant::now();
    sign(&mut report, "verifier_pub", key);
    let signing = t.elapsed();
    let paths = json!({ "report": format!("{name}.json"), "root": hex::encode(root), "sessions": paths });
    // The report goes in last: an epoch is done when its report exists, and a
    // stop before that leaves it to be written whole at the next start.
    let paths_bytes = write_json_atomic(&dir.join(format!("{name}.paths.json")), &paths)?;
    let report_bytes = write_json_atomic(&dir.join(format!("{name}.json")), &report)?;
    println!(
        "epoch {name}: sessions {} {} exchanges {} unknown {unknown} root {} report_bytes {} paths_bytes {} scan_ms {:.1} hash_us {:.1} sign_us {:.1}",
        ours.len(),
        serde_json::to_string(&report["sessions"])?,
        serde_json::to_string(&report["exchanges"])?,
        &hex::encode(root)[..16],
        report_bytes,
        paths_bytes,
        scan.as_secs_f64() * 1e3,
        hash.as_secs_f64() * 1e6,
        signing.as_secs_f64() * 1e6,
    );
    Ok(())
}

fn now_secs() -> i64 {
    SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs() as i64).unwrap_or_default()
}

/// At startup: a report for every ended epoch that has session records but
/// no report, as when the process was stopped across a boundary. Returns the
/// start of the current epoch, the first one `every` reports.
pub fn catch_up(dir: &Path, secs: u64, key: &SigningKey) -> Result<i64> {
    let t = Instant::now();
    let all = sessions(dir, None)?;
    let scan = t.elapsed();
    let current = now_secs().div_euclid(secs as i64);
    let ended: BTreeSet<i64> = all
        .iter()
        .map(|s| s.recorded_ms.div_euclid(secs as i64 * 1000))
        .filter(|e| *e < current)
        .collect();
    for e in ended {
        let start = e * secs as i64;
        if !dir.join(format!("{}.json", report_name(start, secs))).exists() {
            write(dir, secs, start, &all, key, scan)?;
        }
    }
    Ok(current * secs as i64)
}

/// Writes a report for every epoch from the one starting at `next`, in order,
/// each once it has ended and the grace has passed, for as long as the
/// process runs. An epoch with no sessions gets one too, and a late wake
/// writes every epoch it passed.
pub async fn every(dir: PathBuf, secs: u64, key: SigningKey, mut next: i64) {
    let (secs_i, grace) = (secs as i64, GRACE.as_secs() as i64);
    loop {
        let wait = (next + secs_i + grace - now_secs()).max(0) as u64;
        tokio::time::sleep(Duration::from_secs(wait)).await;
        let t = Instant::now();
        let all = sessions(&dir, Some(next));
        let scan = t.elapsed();
        while next + secs_i + grace <= now_secs() {
            let name = report_name(next, secs);
            let done = match &all {
                Ok(_) if dir.join(format!("{name}.json")).exists() => Err(anyhow!("a report for this epoch is already written")),
                Ok(all) => write(&dir, secs, next, all, &key, scan),
                Err(e) => Err(anyhow!("{e:#}")),
            };
            if let Err(e) = done {
                eprintln!("epoch {name}: {e:#}");
            }
            next += secs_i;
        }
    }
}
