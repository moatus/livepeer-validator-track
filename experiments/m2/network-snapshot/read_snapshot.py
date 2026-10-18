"""Standard-library reader for the single measured M2 baseline."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent / "livepeer-arbitrum-2026-10-09-v1.json"
DEFAULT_ID = "livepeer-arbitrum-2026-10-09-v1"
DEFAULT_SHA256 = "b879cc73be95d0e5bdcd5c5bc2f2bc342a7319eb27cb6ffdd2ee6c25f4bb60e8"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def load_snapshot(path=DEFAULT_PATH, expected_id=DEFAULT_ID, expected_sha256=DEFAULT_SHA256):
    """Reject changed inputs; models record snapshot_id plus content_sha256."""
    data = json.loads(Path(path).read_text())
    integrity = data["integrity"]
    body = {key: value for key, value in data.items() if key != "integrity"}
    actual = hashlib.sha256(canonical(body)).hexdigest()
    if actual != integrity["content_sha256"] or actual != expected_sha256:
        raise ValueError("Snapshot content hash differs from the declared/model-pinned version")
    if data["snapshot_id"] != expected_id or data["schema_version"] != "1.0.0":
        raise ValueError("Unsupported snapshot identity or schema")
    return data


def round_inputs(snapshot, round_id=None):
    """Return matched same-round observed inputs, never proposed reward outputs.

    Keep cost, score, emissions policy, fee currency conversion, ownership and
    any use of capture-time own-stake fractions as explicit model assumptions.
    """
    rid = round_id if round_id is not None else snapshot["capture"]["latest_completed_round_id"]
    row = next(r for r in snapshot["rounds"] if r["round_id"] == rid)
    if not row["complete_at_capture"]:
        raise ValueError("Use a completed round for a one-round baseline")
    return {
        "snapshot_id": snapshot["snapshot_id"],
        "snapshot_sha256": snapshot["integrity"]["content_sha256"],
        "round_id": rid, "start_utc": row["start_utc"], "end_utc_exclusive": row["end_utc_exclusive"],
        "fees_eth": Decimal(row["fees_eth"]), "fees_usd_indexed": Decimal(row["fees_usd_indexed"]),
        "active_stake_lpt": Decimal(row["active_stake_lpt"]),
        "scheduled_mint_ceiling_lpt": Decimal(row["scheduled_mint_ceiling_lpt"]),
        "actual_pool_rewards_lpt": Decimal(row["actual_pool_rewards_lpt"]),
        "pools": [{key: Decimal(value) if key in {
            "stake_lpt", "stake_share", "fees_eth", "fee_share", "actual_reward_lpt",
            "operator_reward_cut_fraction", "delegator_fee_share_fraction"} and value is not None else value
            for key, value in pool.items()} for pool in row["pools"]],
    }


if __name__ == "__main__":
    data = load_snapshot()
    inputs = round_inputs(data)
    print(data["snapshot_id"], data["integrity"]["content_sha256"])
    print(f"Round {inputs['round_id']}: {len(inputs['pools'])} pools, "
          f"{inputs['fees_eth']} ETH fees, {inputs['actual_pool_rewards_lpt']} LPT rewards")
