"""Bounded, identifiable snapshot extracts for agents; standard library, offline.

The computer reads and verifies the JSON. Only the selected result enters the
agent's tool output. No vector database or second authoritative dataset is used.
"""
import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal
from read_snapshot import load_snapshot, canonical

DEFAULT_FIELDS = {
    "orchestrators": ["stake_rank_at_capture", "address", "ens_name_observed_unpinned",
        "live_pool_stake_lpt", "operator_address_stake_in_own_pool_lpt",
        "other_addresses_pool_stake_lpt", "operator_reward_cut_fraction", "delegator_fee_share_fraction"],
    "delegations": ["delegator_address", "orchestrator_address", "indexed_bonded_amount_lpt"],
    "pools": ["address", "stake_lpt", "stake_share", "fees_eth", "fee_share",
              "operator_reward_cut_fraction", "delegator_fee_share_fraction"],
}
TABLES = ("orchestrators", "delegations", "daily_fees", "fee_senders", "fee_recipients", "identity_context")
ROUND_KEYS = ("round_id", "start_utc", "end_utc_exclusive", "complete_at_capture",
              "wholly_in_30d_window", "active_stake_lpt", "fees_eth", "fees_usd_indexed",
              "scheduled_mint_ceiling_lpt", "actual_pool_rewards_lpt")


def pointer(value, path):
    """Resolve RFC 6901 JSON Pointer without evaluating code or loading files."""
    if path == "":
        return value
    if not path.startswith("/"):
        raise ValueError("JSON Pointer must start with / (catalog lists the paths)")
    for token in path[1:].split("/"):
        if re.search(r"~(?![01])", token):
            raise ValueError("Invalid JSON Pointer escape")
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", token):
                raise ValueError("Array index must be a nonnegative integer")
            value = value[int(token)]
        elif isinstance(value, dict):
            value = value[token]
        else:
            raise ValueError("JSON Pointer traverses a scalar")
    return value


def field_names(rows, requested, defaults=None):
    available = list(rows[0]) if rows and isinstance(rows[0], dict) else []
    if requested == "all":
        return available
    if requested:
        fields = [name.strip() for name in requested.split(",")]
    else:
        fields = defaults if defaults is not None else available
    if not fields and requested:
        raise ValueError("Choose at least one field")
    if len(fields) != len(set(fields)):
        raise ValueError("Duplicate fields")
    if rows and any(not isinstance(row, dict) for row in rows):
        raise ValueError("Field selection requires object rows")
    if rows and any(field not in available for field in fields):
        raise ValueError("Unknown fields; available: " + ", ".join(available))
    return fields


def resolve_operator(snapshot, selector):
    query = selector.lower().strip()
    ops = snapshot["orchestrators"]
    exact = [o for o in ops if o["address"].lower() == query or
             (o["ens_name_observed_unpinned"] or "").lower() == query]
    if exact:
        if len(exact) != 1:
            raise ValueError("Display name has multiple matches; use the complete address")
        return exact[0]["address"]
    if re.fullmatch(r"[0-9a-f]{4,40}", query):
        matches = [o for o in ops if o["address"][2:].endswith(query)]
    elif re.fullmatch(r"0x[0-9a-f]{4,39}", query):
        matches = [o for o in ops if o["address"].startswith(query)]
    else:
        raise ValueError("Use an exact address/ENS name, hexadecimal prefix, or unique suffix of at least four digits")
    if len(matches) != 1:
        raise ValueError(f"Operator selector has {len(matches)} matches; use the complete address")
    return matches[0]["address"]


def round_row(snapshot, requested):
    rid = requested if requested is not None else snapshot["capture"]["latest_completed_round_id"]
    for index, row in enumerate(snapshot["rounds"]):
        if row["round_id"] == rid:
            return index, row
    raise ValueError(f"Round {rid} is not in the snapshot")


def table(rows, paths, requested=None, defaults=None, offset=0, limit=10):
    if offset < 0 or not 1 <= limit <= 100:
        raise ValueError("Use offset >= 0 and limit between 1 and 100")
    fields = field_names(rows, requested, defaults)
    end = min(offset + limit, len(rows))
    selected = rows[offset:end]
    # Column names appear once; stable JSON Pointers identify each original row.
    items = [{"json_pointer": path, "values": [row[field] for field in fields]}
             for row, path in zip(selected, paths[offset:end])]
    return {"columns": fields, "rows": items,
            "page": {"total_matches": len(rows), "offset": offset, "returned": len(items),
                     "has_more": end < len(rows), "next_offset": end if end < len(rows) else None}}


def result(snapshot, selection, data, context=None):
    return {"snapshot_id": snapshot["snapshot_id"],
            "snapshot_sha256": snapshot["integrity"]["content_sha256"],
            "capture_block": snapshot["capture"]["block_number"],
            "selection": selection, "context": context or {},
            "selected_data_sha256": hashlib.sha256(canonical(data)).hexdigest(), "data": data}


def query(snapshot, args):
    command = args.command
    context = {}
    if command == "catalog":
        sections = []
        for name, value in snapshot.items():
            if name == "provenance":
                continue
            section = {"json_pointer": "/" + name, "kind": type(value).__name__}
            if isinstance(value, list):
                section["rows"] = len(value)
                if value and isinstance(value[0], dict):
                    section["fields"] = list(value[0])
            elif isinstance(value, dict):
                section["fields"] = list(value)
            sections.append(section)
        data = {"sections": sections, "sources": [{"name": name,
            "json_pointer": "/provenance/sources/" + name + "/data",
            "embedded_data_sha256": source["embedded_data_sha256"],
            "fields_or_rows": list(source["data"]) if isinstance(source["data"], dict) else len(source["data"])}
            for name, source in snapshot["provenance"]["sources"].items()],
            "default_row_limit": 10, "default_output_budget_bytes": 12000,
            "examples": ["summary", "operator 4dbc", "table orchestrators --top 10",
                         "round 4364", "pools --round 4364 --top 10",
                         "table delegations --operator 4dbc --limit 10",
                         "get /definitions/own_stake"]}
        selection = {"command": command}
    elif command == "summary":
        data = {"capture": snapshot["capture"], "current_state": snapshot["current_state"],
                "window_30d": snapshot["window_30d"], "prices": snapshot["prices"],
                "latest_completed_round": {key: snapshot["latest_completed_round"][key] for key in ROUND_KEYS}}
        selection = {"command": command, "json_pointers": ["/capture", "/current_state", "/window_30d",
                     "/prices", "/latest_completed_round"], "omitted": "row tables and raw evidence"}
        context = {"measurement_note": "Current ETH fees and LPT issuance are separate mechanisms. No proposed MFS/score/cost output is included."}
    elif command == "operator":
        address = resolve_operator(snapshot, args.selector)
        index, row = next((i, o) for i, o in enumerate(snapshot["orchestrators"]) if o["address"] == address)
        fields = field_names([row], args.fields)
        data = {key: row[key] for key in fields}
        selection = {"command": command, "operator_address": address, "json_pointer": f"/orchestrators/{index}", "fields": fields}
        context = {"definitions": {key: snapshot["definitions"][key] for key in ("own_stake", "reward_cut", "fee_share")},
                   "identity_context": [r for r in snapshot["identity_context"] if r["address"] == address]}
    elif command == "round":
        index, row = round_row(snapshot, args.round_id)
        fields = field_names([row], args.fields, list(ROUND_KEYS))
        data = {key: row[key] for key in fields}
        selection = {"command": command, "round_id": row["round_id"], "json_pointer": f"/rounds/{index}", "fields": fields}
        context = {"total_pool_count": len(row["pools"]), "definition": snapshot["definitions"]["latest_completed_round"]}
    elif command in ("table", "pools"):
        if command == "pools":
            index, row = round_row(snapshot, args.round_id)
            if not row["complete_at_capture"]:
                raise ValueError("Round is incomplete; use 'round' or 'get' to inspect current observations")
            rows = row["pools"]
            paths = [f"/rounds/{index}/pools/{i}" for i in range(len(rows))]
            defaults = DEFAULT_FIELDS["pools"]
            context = {key: row[key] for key in ROUND_KEYS}
            context["total_pool_count"] = len(rows)
            context["shares_are_not_renormalized_to_selected_rows"] = True
            selection = {"command": command, "round_id": row["round_id"]}
        else:
            rows = snapshot[args.section]
            paths = [f"/{args.section}/{i}" for i in range(len(rows))]
            defaults = DEFAULT_FIELDS.get(args.section)
            selection = {"command": command, "section": args.section}
            context = {"total_active_orchestrators_at_capture": snapshot["current_state"]["active_orchestrators"],
                       "total_live_pool_stake_lpt_at_capture": snapshot["current_state"]["sum_live_pool_stake_lpt"],
                       "fee_window_start_utc": snapshot["capture"]["fee_window_start_utc"],
                       "fee_window_end_utc_exclusive": snapshot["capture"]["fee_window_end_utc_exclusive"],
                       "network_fees_eth_30d_raw": snapshot["window_30d"]["fees_eth_raw"],
                       "network_fees_usd_30d_raw": snapshot["window_30d"]["fees_usd_raw"],
                       "network_fees_usd_30d_explorer_adjusted": snapshot["window_30d"]["fees_usd_explorer_adjusted"],
                       "latest_completed_round_id": snapshot["capture"]["latest_completed_round_id"]}
            if args.section in ("orchestrators", "delegations"):
                context["ownership_limit"] = snapshot["definitions"]["own_stake"]
                context["indexed_balance_limit"] = snapshot["definitions"]["delegations"]
        pairs = list(zip(rows, paths))
        if args.operator:
            address = resolve_operator(snapshot, args.operator)
            field = "orchestrator_address" if command == "table" and args.section == "delegations" else "address"
            if not rows or field not in rows[0]:
                raise ValueError("This table does not have an operator-address filter")
            pairs = [(r, p) for r, p in pairs if r[field] == address]
            selection["operator_address"] = address
        if args.top is not None:
            if not 1 <= args.top <= 100:
                raise ValueError("Use --top between 1 and 100")
            if command == "pools":
                pairs.sort(key=lambda pair: (-Decimal(pair[0]["stake_lpt"]), pair[0]["address"]))
            elif args.section != "orchestrators":
                raise ValueError("--top is only defined for orchestrators and round pools")
            pairs = pairs[:args.top]
            selection["top_by_stake"] = args.top
        rows, paths = [pair[0] for pair in pairs], [pair[1] for pair in pairs]
        data = table(rows, paths, args.fields, defaults, args.offset, args.limit)
        selection["fields"] = data["columns"]
    elif command == "get":
        value = pointer(snapshot, args.json_pointer)
        selection = {"command": command, "json_pointer": args.json_pointer}
        if isinstance(value, list):
            paths = [args.json_pointer + "/" + str(i) for i in range(len(value))]
            if value and not isinstance(value[0], dict):
                if args.fields:
                    raise ValueError("Field selection requires object rows")
                end = min(args.offset + args.limit, len(value))
                data = {"items": [{"json_pointer": paths[i], "value": value[i]} for i in range(args.offset, end)],
                        "page": {"total_matches": len(value), "offset": args.offset, "returned": max(0, end - args.offset),
                                 "has_more": end < len(value), "next_offset": end if end < len(value) else None}}
            else:
                data = table(value, paths, args.fields, offset=args.offset, limit=args.limit)
        elif isinstance(value, dict) and args.fields:
            fields = field_names([value], args.fields)
            data = {key: value[key] for key in fields}
            selection["fields"] = fields
        elif args.fields:
            raise ValueError("Field selection requires an object or table")
        else:
            data = value
    else:
        raise ValueError("Unknown query")
    return result(snapshot, selection, data, context)


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--max-bytes", type=int, default=12000, help="Output budget, default 12000 bytes; oversized results are refused")
    subs = root.add_subparsers(dest="command", required=True)
    subs.add_parser("catalog", help="Section paths, fields, counts and evidence sources; no data dump")
    subs.add_parser("summary", help="Measured totals and windows; no row tables or raw evidence")
    single = subs.add_parser("operator", help="One exact address, ENS name, unique hex prefix or suffix")
    single.add_argument("selector")
    single.add_argument("--fields", help="Comma-separated field names, or all")
    rnd = subs.add_parser("round", help="Round totals only by default")
    rnd.add_argument("round_id", type=int, nargs="?")
    rnd.add_argument("--fields", help="Comma-separated field names, or all")
    tab = subs.add_parser("table", help="Paginated normalized tables")
    tab.add_argument("section", choices=TABLES)
    pool = subs.add_parser("pools", help="Matched completed-round pools; retains whole-network denominators")
    pool.add_argument("--round", dest="round_id", type=int)
    for sub in (tab, pool):
        sub.add_argument("--operator")
        sub.add_argument("--top", type=int)
    get = subs.add_parser("get", help="Exact JSON Pointer for a field, row, definition or source evidence")
    get.add_argument("json_pointer")
    for sub in (tab, pool, get):
        sub.add_argument("--fields", help="Comma-separated field names, or all")
        sub.add_argument("--offset", type=int, default=0)
        sub.add_argument("--limit", type=int, default=10)
    return root


def main():
    args = parser().parse_args()
    try:
        if not 512 <= args.max_bytes <= 1000000:
            raise ValueError("Use --max-bytes between 512 and 1000000")
        if hasattr(args, "offset") and (args.offset < 0 or not 1 <= args.limit <= 100):
            raise ValueError("Use offset >= 0 and limit between 1 and 100")
        answer = query(load_snapshot(), args)
        encoded = canonical(answer)
        if len(encoded) > args.max_bytes:
            raise ValueError(f"Result would be {len(encoded)} bytes, over the {args.max_bytes}-byte budget. "
                             "Select fewer --fields, use --limit/--offset or a narrower JSON Pointer; "
                             "use the Python reader for bulk calculations.")
        sys.stdout.buffer.write(encoded + b"\n")
    except (ValueError, KeyError, IndexError, TypeError) as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
