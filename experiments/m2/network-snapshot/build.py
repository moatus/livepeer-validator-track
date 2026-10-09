"""Assemble a measured, self-contained M2 baseline from the saved public capture."""
import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal as D, getcontext
from pathlib import Path

getcontext().prec = 78
HERE = Path(__file__).resolve().parent
ARTIFACT = HERE / "livepeer-arbitrum-2026-10-09-v1.json"
START, END = 1788912000, 1791504000
EXCLUDED = {"0xca3331d67e87816adb30d9562a6e8c0623fb7fef", "0xc3c7c4c8f7061b7d6a72766eee5359fe4f36e61e"}
SOURCE_FILES = ["meta", "protocol", "days", "rounds", "orchestrators", "tickets",
                "mints", "excluded_senders", "queries", "ticket_queries", "prices",
                "chain_checks", "explorer_contracts", "explorer_ens-data"]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def number(value):
    return format(D(str(value)), "f")


def utc(timestamp):
    return datetime.fromtimestamp(int(timestamp), timezone.utc).isoformat().replace("+00:00", "Z")


def total(rows, key):
    return sum((D(row[key]) for row in rows), D(0))


def assemble(raw, stake_file):
    sources = {}
    for name in SOURCE_FILES:
        path = raw / (name + ".json")
        sources[name] = {"original_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                         "data": json.loads(path.read_text())}
    sources["operator_stake_rpc"] = {"original_file_sha256": hashlib.sha256(stake_file.read_bytes()).hexdigest(),
                                     "data": json.loads(stake_file.read_text())}
    # Preserve exact ABI values in tools whose JSON parsers use IEEE-754 doubles.
    for check in sources["chain_checks"]["data"]["checks"].values():
        check["value"] = str(check["value"])
    for source in sources.values():
        source["embedded_data_sha256"] = digest(source["data"])
    read = lambda name: sources[name]["data"]
    pin = read("meta")["_meta"]["block"]
    protocol = read("protocol")["protocol"]
    current_round_id = int(protocol["currentRound"]["id"])
    stake = read("operator_stake_rpc")
    if (stake["block_number"], stake["block_hash"]) != (pin["number"], pin["hash"]):
        raise ValueError("Operator reads must use the original capture block and hash")
    operators = read("orchestrators")["transcoders"]
    operator_reads = {row["address"]: row for row in stake["operators"]}
    if set(operator_reads) != {row["id"] for row in operators}:
        raise ValueError("Need exact stake reads for every captured active operator")
    tickets = read("tickets")["events"]
    mint_events = read("mints")["events"]
    days = [row for row in read("days")["days"] if START <= row["date"] < END]
    rounds = sorted(read("rounds")["rounds"], key=lambda row: int(row["id"]))
    next_round = {int(row["id"]): row for row in rounds}
    names = {row["id"]: row.get("name") for row in read("explorer_ens-data")}
    recipient_fees, sender_fees = defaultdict(list), defaultdict(list)
    for event in tickets:
        recipient_fees[event["recipient"]["id"]].append(event)
        sender_fees[event["sender"]["id"]].append(event)
    mint_30d = total(mint_events, "amount")
    price = read("prices")["LPT"]["response"]["data"]["amount"]
    raw_eth, raw_usd = total(tickets, "faceValue"), total(tickets, "faceValueUSD")
    excluded_events = [e for e in tickets if e["sender"]["id"] in EXCLUDED]
    excluded_eth, excluded_usd = total(excluded_events, "faceValue"), total(excluded_events, "faceValueUSD")
    active_addresses = {o["id"] for o in operators}
    other_recipient_events = [e for e in tickets if e["recipient"]["id"] not in active_addresses]
    live_stake = total(operators, "totalStake")
    round_rows = []
    for row in rounds:
        rid = int(row["id"])
        finish = next_round.get(rid + 1, {}).get("startTimestamp")
        fee, active = D(row["volumeETH"]), D(row["totalActiveStake"])
        pools = [{"address": p["delegate"]["id"], "pool_id": p["id"],
                  "stake_lpt": p["totalStake"], "stake_share": number(D(p["totalStake"]) / active),
                  "fees_eth": p["fees"], "fee_share": number(D(p["fees"]) / fee) if fee else None,
                  "actual_reward_lpt": p["rewardTokens"] or "0",
                  "reward_tokens_reported": p["rewardTokens"] is not None,
                  "operator_reward_cut_fraction": number(D(p["rewardCut"]) / D(10**6)),
                  "delegator_fee_share_fraction": number(D(p["feeShare"]) / D(10**6))}
                 for p in row["pools"]]
        round_rows.append({"round_id": rid, "start_utc": utc(row["startTimestamp"]),
            "end_utc_exclusive": utc(finish) if finish else None,
            "complete_at_capture": rid < current_round_id,
            "wholly_in_30d_window": bool(finish and row["startTimestamp"] >= START and finish <= END),
            "l1_start_block": int(row["startBlock"]), "l1_end_block_exclusive": int(row["endBlock"]),
            "active_stake_lpt": row["totalActiveStake"], "fees_eth": row["volumeETH"],
            "fees_usd_indexed": row["volumeUSD"], "scheduled_mint_ceiling_lpt": row["mintableTokens"],
            "actual_pool_rewards_lpt": number(sum((D(p["actual_reward_lpt"]) for p in pools), D(0))),
            "pools": sorted(pools, key=lambda p: p["address"])})
    latest = next(row for row in round_rows if row["round_id"] == current_round_id - 1)
    latest_pools = {row["address"]: row for row in latest["pools"]}
    all_operators, delegations = [], []
    for rank, row in enumerate(sorted(operators, key=lambda x: D(x["totalStake"]), reverse=True), 1):
        address = row["id"]
        calls = operator_reads[address]["calls"]
        pending = D(int(calls["pendingStake(address,uint256)"], 16)) / D(10**18)
        words = [int(calls["getDelegator(address)"][2 + i:2 + i + 64], 16) for i in range(0, 448, 64)]
        delegate_address = "0x" + format(words[2], "040x")
        self_stake = pending if delegate_address == address else D(0)
        current_pool = D(row["totalStake"])
        if not D(0) <= self_stake <= current_pool:
            raise ValueError(f"Invalid own-address stake for {address}")
        own_events = recipient_fees.get(address, [])
        adjusted = [e for e in own_events if e["sender"]["id"] not in EXCLUDED]
        all_operators.append({"stake_rank_at_capture": rank, "address": address,
            "ens_name_observed_unpinned": names.get(address), "live_pool_stake_lpt": row["totalStake"],
            "operator_address_pending_stake_lpt": number(pending),
            "operator_address_delegate": delegate_address,
            "operator_address_stake_in_own_pool_lpt": number(self_stake),
            "other_addresses_pool_stake_lpt": number(current_pool - self_stake),
            "operator_address_fraction_of_own_pool": number(self_stake / current_pool),
            "organization_total_stake_lpt": None,
            "operator_reward_cut_fraction": number(D(row["rewardCut"]) / D(10**6)),
            "delegator_fee_share_fraction": number(D(row["feeShare"]) / D(10**6)),
            "indexed_operator_bonded_amount_lpt": row["delegator"]["bondedAmount"],
            "indexed_positive_delegation_links": len(row["delegators"]),
            "fees_eth_30d_raw": number(total(own_events, "faceValue")),
            "fees_usd_30d_raw": number(total(own_events, "faceValueUSD")),
            "fees_eth_30d_explorer_adjusted": number(total(adjusted, "faceValue")),
            "fees_usd_30d_explorer_adjusted": number(total(adjusted, "faceValueUSD")),
            "latest_completed_round": latest_pools.get(address)})
        delegations.extend({"delegator_address": d["id"], "orchestrator_address": address,
                            "indexed_bonded_amount_lpt": d["bondedAmount"],
                            "pending_stake_lpt": None, "beneficial_owner": None}
                           for d in row["delegators"])
    snapshot = {
        "schema_version": "1.0.0", "snapshot_id": "livepeer-arbitrum-2026-10-09-v1", "status": "drafted",
        "capture": {"chain": "arbitrum-one", "chain_id": 42161, "block_number": pin["number"],
            "block_hash": pin["hash"], "block_utc": utc(pin["timestamp"]),
            "original_retrieved_utc": read("meta")["retrievedUTC"],
            "operator_stake_supplement_retrieved_utc": stake["retrieved_utc"],
            "current_round_id": current_round_id, "latest_completed_round_id": latest["round_id"],
            "fee_window_start_utc": utc(START), "fee_window_end_utc_exclusive": utc(END)},
        "units": {"monetary_values": "Decimal strings; never binary floats in model accounting.",
            "lpt": "LPT token units, not wei", "eth": "ETH units, not wei",
            "fractions": "0–1 decimal strings; rewardCut and feeShare source scale is 1,000,000",
            "inflation": "per-round fraction; source scale is 1,000,000,000",
            "usd": "Indexed contemporaneous ETH/USD valuation, except explicitly labeled snapshot-price valuations.",
            "block_numbers": "capture block is Arbitrum L2; round start/end block fields are L1 numbers"},
        "definitions": {
            "fees": "Redeemed winning-ticket face values. Not all jobs, invoices, demand or unredeemed accruals; current settlement currency is ETH.",
            "mint": "LPT Mint events to the protocol Minter, excluding bridge mints. Gross issuance, not net supply change or money earned from fees.",
            "reward_cut": "Operator commission from pool rewards; delegators receive the remainder pro rata, including operator-address stake.",
            "fee_share": "Fraction of current node fee receipts paid to delegators, including operator-address stake.",
            "own_stake": "pendingStake(operator address) at the pinned block, restricted to its own pool; includes accrued rewards/commission. It does not identify total organizational ownership.",
            "delegations": "Positive indexed bond links to active pools; bondedAmount may omit compounding. These are addresses, not identified people or independent organizations.",
            "latest_completed_round": "Matched same-round fees, active stake, cuts and mint ceiling for one-round models. Its fee window differs from the 30 complete UTC days.",
            "actual_round_rewards": "Source rewardTokens=null is normalized to zero with reward_tokens_reported=false; the original value remains embedded.",
            "explorer_adjustment": "Two sender addresses excluded by Explorer chart policy from 2026-08-27. Preserve raw and adjusted values; this exclusion does not establish abuse.",
            "names": "ENS labels captured from an Explorer API without a historical block pin; display labels, not controller verification."},
        "current_state": {"active_orchestrators": len(operators), "protocol_active_stake_lpt": protocol["totalActiveStake"],
            "sum_live_pool_stake_lpt": number(live_stake), "global_lpt_supply_lpt": protocol["totalSupply"],
            "inflation_per_round_fraction": number(D(protocol["inflation"]) / D(10**9)),
            "unbonding_period_rounds": int(protocol["unbondingPeriod"]), "round_length_l1_blocks": int(protocol["roundLength"]),
            "current_round_mint_ceiling_lpt": protocol["currentRound"]["mintableTokens"],
            "current_round_actual_minted_lpt_at_capture": number(D(read("chain_checks")["checks"]["Minter.currentMintedTokens()"]["value"]) / D(10**18)),
            "treasury_reward_cut_rate_raw": read("chain_checks")["checks"]["BondingManager.treasuryRewardCutRate()"]["value"],
            "explorer_reported_delegators": int(protocol["delegatorsCount"]),
            "indexed_positive_delegation_links": len(delegations),
            "validator_population": None},
        "window_30d": {"days": 30, "redeemed_ticket_count": len(tickets), "inflation_mint_event_count": len(mint_events),
            "fees_eth_raw": number(raw_eth), "fees_usd_raw": number(raw_usd),
            "fees_eth_explorer_adjusted": number(raw_eth - excluded_eth),
            "fees_usd_explorer_adjusted": number(raw_usd - excluded_usd),
            "fees_usd_excluded": number(excluded_usd), "gross_inflation_minted_lpt": number(mint_30d),
            "gross_mint_usd_at_snapshot_price": number(mint_30d * D(price)),
            "excluded_sender_addresses": sorted(EXCLUDED),
            "fee_sender_count": len(sender_fees), "fee_recipient_count": len(recipient_fees)},
        "prices": {"lpt_usd_spot": price, "eth_usd_spot": read("prices")["ETH"]["response"]["data"]["amount"],
            "retrieved_utc": read("prices")["retrievedUTC"], "source": read("prices")["source"],
            "claim_price_forecast": None},
        "latest_completed_round": latest, "rounds": round_rows,
        "daily_fees": [{"date_utc": utc(row["date"]), "fees_eth_raw": row["volumeETH"],
                        "fees_usd_raw": row["volumeUSD"]} for row in days],
        "orchestrators": all_operators, "delegations": sorted(delegations, key=lambda x: x["delegator_address"]),
        "fee_senders": [{"address": address, "redeemed_ticket_count": len(events),
            "fees_eth": number(total(events, "faceValue")), "fees_usd": number(total(events, "faceValueUSD")),
            "explorer_chart_excluded": address in EXCLUDED} for address, events in sorted(sender_fees.items())],
        "fee_recipients": [{"address": address, "active_at_capture": address in active_addresses,
            "redeemed_ticket_count": len(events), "fees_eth_raw": number(total(events, "faceValue")),
            "fees_usd_raw": number(total(events, "faceValueUSD")),
            "fees_eth_explorer_adjusted": number(total([e for e in events if e["sender"]["id"] not in EXCLUDED], "faceValue")),
            "fees_usd_explorer_adjusted": number(total([e for e in events if e["sender"]["id"] not in EXCLUDED], "faceValueUSD"))}
            for address, events in sorted(recipient_fees.items())],
        "identity_context": [{"address": "0x4f4758f7167b18e1f5b3c1a7575e3eb584894dbc",
            "documented_role": "Livepeer Community Grants / Decentralized Community Node",
            "current_signing_key_controller": None,
            "sources": ["https://github.com/livepeer/grants", "https://forum.livepeer.org/t/transcoder-campaign-decentralized-community-node/203"],
            "stake_provenance": {"date_utc": "2024-01-30", "amount_lpt": "362532.59917200520352279",
                "recipient": "0xcfe1ed2d133fbb488929edc15eee5812f5dc8877",
                "transaction": "https://arbiscan.io/tx/0x5c12fdb2a1ff6f31f429fec967bac20074564ba7212bbd6039eb7ee4dfe84289",
                "meaning": "TransferBond and Rebond to the same node; provenance does not establish present common ownership."},
            "interpretation": "Retained operator receipts are not established personal profit; historical purpose is grants funding."}],
        "limitations": [
            "This is observed current-system data, not a litepaper deployment, forecast or evidence of self-dealing.",
            "Costs, validator scores, independent demand, quality, internal job value and beneficial wallet ownership are not measured.",
            "Protocol active stake and live pool stake differ because their accounting times differ; do not mix denominators.",
            "Explorer delegator count and indexed positive links are unreconciled; neither is a verified count of people.",
            "Individual delegator pending stakes were not read; never sum indexed bondedAmount as current pool capital.",
            "Existing stake-only issuance must not be labeled fee-linked. MFS, fee burn and validator/treasury shares belong to each model's declared paper version.",
            "Round 4364 crosses the 30-day UTC window end; rounds wholly inside that window are 4331–4363.",
            "Historical redeemed fee receipts do not measure all AI work or off-chain/invoiced activity.",
            "The 30-day receipts include one recipient inactive at capture; fee_recipients preserves it and network totals include its receipts.",
        ],
        "provenance": {"explorer": "https://explorer.livepeer.org", "subgraph_id": read("meta")["subgraphId"],
            "explorer_source_commit": "169ac65bdc4f34a67aa791ddc0a43148a56773d2",
            "subgraph_source_commit": "c41182c798219f7faf3f1f6036d07eb7eda64ad5",
            "operator_stake_rpc": stake["rpc"],
            "collection": "Embedded source responses and exact pinned GraphQL queries. Archive operator calls independently match capture block hash. ENS and spot prices have separate capture times.",
            "sources": sources},
    }
    snapshot["window_30d"]["fees_usd_to_recipients_inactive_at_capture"] = number(total(other_recipient_events, "faceValueUSD"))
    snapshot["integrity"] = {"algorithm": "sha256", "encoding": "UTF-8 JSON, sorted keys, compact separators, ensure_ascii=False",
                              "scope": "Entire document except integrity", "content_sha256": digest(snapshot)}
    return snapshot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--operator-stake", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ARTIFACT)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite a frozen snapshot; use a new output path/version.")
    snapshot = assemble(args.raw, args.operator_stake)
    args.output.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    print(snapshot["snapshot_id"], snapshot["integrity"]["content_sha256"])
