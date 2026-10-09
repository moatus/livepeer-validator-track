"""Check exact agent extracts, pagination, context denominators and output limits."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from query import query, pointer
from read_snapshot import load_snapshot, canonical

HERE = Path(__file__).resolve().parent


def cli(*args, expect=0):
    response = subprocess.run([sys.executable, str(HERE / "query.py"), *args],
                              capture_output=True, check=False)
    assert response.returncode == expect, (args, response.stderr.decode())
    if expect:
        assert response.stdout == b""  # never emit a partially truncated dataset
        assert "error" in json.loads(response.stderr)
        return response.stderr
    assert len(response.stdout) <= 12001
    return json.loads(response.stdout)


def verify():
    snapshot = load_snapshot()
    original = hashlib.sha256((HERE / "livepeer-arbitrum-2026-10-09-v1.json").read_bytes()).hexdigest()
    catalog = cli("catalog")
    assert next(s for s in catalog["data"]["sections"] if s["json_pointer"] == "/delegations")["rows"] == 3126
    summary = cli("summary")
    assert summary["data"]["current_state"]["active_orchestrators"] == 100
    assert "orchestrators" not in summary["data"] and "provenance" not in summary["data"]
    one = cli("operator", "4dbc", "--fields", "address,operator_reward_cut_fraction,operator_address_stake_in_own_pool_lpt")
    assert one["selection"]["json_pointer"] == "/orchestrators/2"
    assert one["data"]["operator_reward_cut_fraction"] == "0.501"
    assert one["data"]["operator_address_stake_in_own_pool_lpt"] == "721.03946309164270284"
    assert "identity_context" in one["context"]
    assert one["snapshot_sha256"] == snapshot["integrity"]["content_sha256"]
    pools = cli("pools", "--round", "4364", "--top", "10")
    assert len(pools["data"]["rows"]) == 10
    assert pools["context"]["total_pool_count"] == 100
    assert pools["context"]["fees_eth"] == "0.33150916203312"
    assert pools["context"]["active_stake_lpt"] == snapshot["latest_completed_round"]["active_stake_lpt"]
    assert pools["context"]["shares_are_not_renormalized_to_selected_rows"] is True
    assert {r["values"][0] for r in pools["data"]["rows"]} == {o["address"] for o in snapshot["orchestrators"][:10]}
    for result in [catalog, summary, one, pools]:
        assert result["selected_data_sha256"] == hashlib.sha256(canonical(result["data"])).hexdigest()
    for item in pools["data"]["rows"]:
        raw = pointer(snapshot, item["json_pointer"])
        assert item["values"] == [raw[k] for k in pools["data"]["columns"]]
    # A fourteen-address pool spans pages; page boundaries must lose no records.
    delegates = [cli("table", "delegations", "--operator", "4dbc", "--limit", "10", "--offset", str(offset))
                 for offset in [0, 10]]
    assert [d["data"]["page"]["returned"] for d in delegates] == [10, 4]
    assert delegates[0]["data"]["page"]["next_offset"] == 10
    assert delegates[1]["data"]["page"]["has_more"] is False
    selected = [r["values"][0] for page in delegates for r in page["data"]["rows"]]
    expected = [d["delegator_address"] for d in snapshot["delegations"] if d["orchestrator_address"] == one["data"]["address"]]
    assert selected == expected and len(set(selected)) == 14
    # Larger pages are checked in-process without sending bulk data to context.
    for section in ["orchestrators", "delegations", "fee_recipients"]:
        pointers = []
        for offset in range(0, len(snapshot[section]), 37):
            args = SimpleNamespace(command="table", section=section, fields=None,
                                   operator=None, top=None, offset=offset, limit=37)
            page = query(snapshot, args)["data"]
            pointers.extend(r["json_pointer"] for r in page["rows"])
        assert pointers == [f"/{section}/{i}" for i in range(len(snapshot[section]))]
    evidence = cli("get", "/provenance/sources/operator_stake_rpc/data/operators/2")
    assert evidence["data"]["address"] == one["data"]["address"]
    assert set(evidence["data"]["calls"]) == {"pendingStake(address,uint256)", "getDelegator(address)"}
    assert cli("get", "/definitions/own_stake")["data"] == snapshot["definitions"]["own_stake"]
    assert pointer({"a/b": {"c~d": 3}}, "/a~1b/c~0d") == 3
    for args in [("get", "/provenance"), ("--max-bytes", "512", "summary"),
                 ("operator", "zzzz"), ("operator", "4dbc", "--fields", "missing_field"),
                 ("table", "delegations", "--offset", "-1"), ("table", "orchestrators", "--limit", "101"),
                 ("get", "/orchestrators/-1"), ("get", "/definitions/~2"),
                 ("pools", "--round", "4365"), ("round", "9999")]:
        cli(*args, expect=2)
    altered = {**snapshot, "orchestrators": [{**snapshot["orchestrators"][0], "ens_name_observed_unpinned": "same.eth"},
                                            {**snapshot["orchestrators"][1], "ens_name_observed_unpinned": "same.eth"}]}
    from query import resolve_operator
    try:
        resolve_operator(altered, "same.eth")
    except ValueError:
        pass
    else:
        raise AssertionError("Ambiguous label selected silently")
    assert hashlib.sha256((HERE / "livepeer-arbitrum-2026-10-09-v1.json").read_bytes()).hexdigest() == original
    print("PASS: exact projected fields and pointers, operator/evidence selection, snapshot and selection hashes.")
    print("PASS: delegation and whole-table pagination; selected pools retain all-network denominators.")
    print("PASS: output budget prevents bulk dumps; unknown/ambiguous inputs and incomplete round rejected.")
    print("PASS: authoritative snapshot unchanged.")
    for args in [("summary",), ("operator", "4dbc"), ("table", "orchestrators", "--top", "10")]:
        response = subprocess.run([sys.executable, str(HERE / "query.py"), *args], capture_output=True, check=True)
        print("Output bytes:", " ".join(args), len(response.stdout))


if __name__ == "__main__":
    verify()
