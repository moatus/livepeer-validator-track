"""Independently reconcile the frozen baseline and embedded measured evidence."""
import hashlib
from copy import deepcopy
from decimal import Decimal as D, getcontext
from tempfile import TemporaryDirectory
from pathlib import Path
from read_snapshot import load_snapshot, round_inputs, canonical

getcontext().prec = 78


def close(a, b, tolerance="1e-18"):
    if abs(D(a) - D(b)) > D(tolerance):
        raise AssertionError((a, b))


def verify():
    data = load_snapshot()
    src = {name: row["data"] for name, row in data["provenance"]["sources"].items()}
    for row in data["provenance"]["sources"].values():
        assert hashlib.sha256(canonical(row["data"])).hexdigest() == row["embedded_data_sha256"]
    assert data["capture"]["block_number"] == 513206238
    assert data["capture"]["block_hash"] == "0x72c814416751eb16375d659b9c304625e64cd4cb71865967c30c8030af6c848b"
    assert src["meta"]["_meta"]["hasIndexingErrors"] is False
    assert src["operator_stake_rpc"]["block_hash"] == data["capture"]["block_hash"]
    assert src["chain_checks"]["blockHeader"]["hash"] == data["capture"]["block_hash"]
    for query in list(src["queries"].values()) + src["ticket_queries"] + src["mints"]["queries"]:
        assert "block:{number:513206238}" in query
    for check in src["chain_checks"]["checks"].values():
        assert check["block"] == 513206238
        assert int(check["rawResult"], 16) == int(check["value"])
    tickets, mints = src["tickets"]["events"], src["mints"]["events"]
    assert len(tickets) == len({e["id"] for e in tickets}) == 4947
    assert len(mints) == len({e["id"] for e in mints}) == 3183
    assert all(1788912000 <= e["timestamp"] < 1791504000 for e in tickets + mints)
    assert all(e["to"] == "0xc20de37170b45774e6cd3d2304017fc962f27252" for e in mints)
    window = data["window_30d"]
    for event_key, metric, daily_key in [("faceValue", "fees_eth_raw", "volumeETH"),
                                         ("faceValueUSD", "fees_usd_raw", "volumeUSD")]:
        amount = sum((D(e[event_key]) for e in tickets), D(0))
        close(amount, window[metric])
        days = [d for d in src["days"]["days"] if 1788912000 <= d["date"] < 1791504000]
        assert len(days) == 30
        close(amount, sum((D(d[daily_key]) for d in days), D(0)))
    close(window["fees_usd_raw"], "31127.739483773676", "1e-6")
    close(window["fees_usd_explorer_adjusted"], "27023.280281809715", "1e-6")
    excluded = set(window["excluded_sender_addresses"])
    excluded_usd = sum((D(e["faceValueUSD"]) for e in tickets if e["sender"]["id"] in excluded), D(0))
    close(excluded_usd, window["fees_usd_excluded"])
    close(D(window["fees_usd_raw"]) - excluded_usd, window["fees_usd_explorer_adjusted"])
    close(excluded_usd, sum((D(e["volumeUSD"]) for e in src["excluded_senders"]["broadcasterDays"]
                           if 1788912000 <= e["date"] < 1791504000), D(0)))
    close(sum((D(e["amount"]) for e in mints), D(0)), window["gross_inflation_minted_lpt"])
    close(window["gross_inflation_minted_lpt"], "985454.6341961339", "1e-6")
    close(D(window["gross_inflation_minted_lpt"]) * D(data["prices"]["lpt_usd_spot"]),
          window["gross_mint_usd_at_snapshot_price"])
    ops = data["orchestrators"]
    assert len(data["fee_recipients"]) == 65
    assert sum(not r["active_at_capture"] for r in data["fee_recipients"]) == 1
    close(sum((D(r["fees_usd_raw"]) for r in data["fee_recipients"]), D(0)), window["fees_usd_raw"])
    close(sum((D(r["fees_usd_explorer_adjusted"]) for r in data["fee_recipients"]), D(0)), window["fees_usd_explorer_adjusted"])
    close(sum((D(o["fees_usd_30d_raw"]) for o in ops), D(0)) + D(window["fees_usd_to_recipients_inactive_at_capture"]), window["fees_usd_raw"])
    assert len(ops) == len({o["address"] for o in ops}) == 100
    assert len(data["delegations"]) == len({d["delegator_address"] for d in data["delegations"]}) == 3126
    assert max(o["indexed_positive_delegation_links"] for o in ops) < 1000  # nested query not capped
    calls = {o["address"]: o["calls"] for o in src["operator_stake_rpc"]["operators"]}
    for op in ops:
        pending = D(int(calls[op["address"]]["pendingStake(address,uint256)"], 16)) / D(10**18)
        close(pending, op["operator_address_pending_stake_lpt"])
        raw_delegator = calls[op["address"]]["getDelegator(address)"]
        close(D(int(raw_delegator[194:258], 16)) / D(10**18), op["live_pool_stake_lpt"])
        assert "0x" + format(int(raw_delegator[130:194], 16), "040x") == op["operator_address_delegate"]
        close(D(op["operator_address_stake_in_own_pool_lpt"]) + D(op["other_addresses_pool_stake_lpt"]),
              op["live_pool_stake_lpt"])
        assert op["organization_total_stake_lpt"] is None
        assert D(0) <= D(op["operator_address_fraction_of_own_pool"]) <= D(1)
        assert D(0) <= D(op["operator_reward_cut_fraction"]) <= D(1)
        assert D(0) <= D(op["delegator_fee_share_fraction"]) <= D(1)
        assert len([d for d in data["delegations"] if d["orchestrator_address"] == op["address"]]) == op["indexed_positive_delegation_links"]
    close(sum((D(o["live_pool_stake_lpt"]) for o in ops), D(0)), data["current_state"]["sum_live_pool_stake_lpt"])
    close(D(src["chain_checks"]["checks"]["BondingManager.getTotalBonded()"]["value"]) / D(10**18),
          data["current_state"]["protocol_active_stake_lpt"])
    for row in data["rounds"]:
        assert len(row["pools"]) == 100
        close(sum((D(p["stake_lpt"]) for p in row["pools"]), D(0)), row["active_stake_lpt"])
        close(sum((D(p["fees_eth"]) for p in row["pools"]), D(0)), row["fees_eth"])
        close(sum((D(p["stake_share"]) for p in row["pools"]), D(0)), "1")
        close(sum((D(p["actual_reward_lpt"]) for p in row["pools"]), D(0)), row["actual_pool_rewards_lpt"])
        if row["wholly_in_30d_window"]:
            close(sum((D(e["faceValue"]) for e in tickets if int(e["round"]["id"]) == row["round_id"]), D(0)), row["fees_eth"])
            close(sum((D(e["amount"]) for e in mints if int(e["round"]["id"]) == row["round_id"]), D(0)), row["actual_pool_rewards_lpt"])
    complete = [r for r in data["rounds"] if r["wholly_in_30d_window"]]
    assert [r["round_id"] for r in complete] == list(range(4331, 4364))
    inputs = round_inputs(data)
    assert inputs["round_id"] == 4364
    assert sum(p["fees_eth"] > 0 for p in inputs["pools"]) == 27
    close(inputs["fees_eth"], "0.33150916203312")
    close(inputs["actual_pool_rewards_lpt"], sum((D(e["amount"]) for e in src["mints"]["lastCompletedRound"]["mintEvents"]), D(0)))
    third = ops[2]
    assert third["address"].endswith("4dbc") and third["operator_reward_cut_fraction"] == "0.501"
    close(third["operator_address_stake_in_own_pool_lpt"], "721.039463091642702840")
    assert data["identity_context"][0]["current_signing_key_controller"] is None
    with TemporaryDirectory() as directory:
        path = Path(directory) / "changed.json"
        changed = deepcopy(data)
        changed["window_30d"]["fees_eth_raw"] = "0"
        path.write_text(__import__("json").dumps(changed))
        try:
            load_snapshot(path)
        except ValueError:
            pass
        else:
            raise AssertionError("Reader accepted a modified snapshot")
    try:
        round_inputs(data, 4365)
    except ValueError:
        pass
    else:
        raise AssertionError("Reader accepted an incomplete round")
    print("PASS: frozen content and source hashes, exact block pin, source queries and RPC reads.")
    print("PASS: 30-day fees/adjustment/mints, 100 operator stake splits and 3,126 delegation links.")
    print("PASS: all round stake/fee/reward totals; 33 within-window rounds match events.")
    print("PASS: same-round model inputs; tampering and incomplete-round selection rejected.")


if __name__ == "__main__":
    verify()
