"""Supplement the existing capture with operator-address stake at its exact block.

Read-only, public archive RPC; no API key, current-state fallback or dependency.
This does not measure all wallets controlled by an operator organization.
"""
import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

RPC = "https://arbitrum-one.public.blastapi.io"


def rpc(method, params):
    request = Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1,
        "method": method, "params": params}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "M2-network-snapshot/1"})
    for attempt in range(4):
        try:
            with urlopen(request, timeout=35) as response:
                data = json.load(response)
            if "error" in data:
                raise RuntimeError(data["error"])
            return data["result"]
        except Exception:
            if attempt == 3:
                raise
            time.sleep(attempt + 1)


def collect(raw, output):
    load = lambda name: json.loads((raw / (name + ".json")).read_text())
    meta = load("meta")
    pin = meta["_meta"]["block"]
    header = rpc("eth_getBlockByNumber", [hex(pin["number"]), False])
    if header["hash"] != pin["hash"]:
        raise ValueError("Archive block hash differs from the frozen capture")
    contract = load("explorer_contracts")["BondingManager"]["address"]
    round_id = int(load("protocol")["protocol"]["currentRound"]["id"])

    def read(operator):
        address = operator["id"]
        encoded_address = address[2:].rjust(64, "0")
        # Ethereum ABI selectors for these documented BondingManager signatures.
        call_data = {
            "pendingStake(address,uint256)": "0x9d0b2c7a" + encoded_address + format(round_id, "064x"),
            "getDelegator(address)": "0xa64ad595" + encoded_address,
        }
        calls = {signature: rpc("eth_call", [{"to": contract, "data": data}, hex(pin["number"])])
                 for signature, data in call_data.items()}
        return {"address": address, "calls": calls}

    operators = load("orchestrators")["transcoders"]
    with ThreadPoolExecutor(max_workers=4) as executor:
        rows = list(executor.map(read, operators))
    output.write_text(json.dumps({"retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "rpc": RPC, "contract": contract, "block_number": pin["number"],
        "block_hash": header["hash"], "round_id": round_id, "operators": rows}, indent=2) + "\n")
    print(f"Saved {len(rows)} operator-address stake reads at block {pin['number']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    collect(args.raw, args.output)
