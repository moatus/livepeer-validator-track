"""Render a readable view from the sole authoritative JSON snapshot (no network)."""
import argparse
import json
from pathlib import Path
from read_snapshot import load_snapshot, DEFAULT_PATH

HERE = Path(__file__).resolve().parent


def build(output):
    snapshot = load_snapshot()
    fields = ["snapshot_id", "integrity", "capture", "current_state", "window_30d", "prices",
              "definitions", "limitations", "orchestrators", "delegations", "identity_context"]
    data = {key: snapshot[key] for key in fields}
    latest = snapshot["latest_completed_round"]
    data["latest_round_summary"] = {k: v for k, v in latest.items() if k != "pools"}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    template = (HERE / "view-template.html").read_text()
    output.write_text(template.replace("/* SNAPSHOT_DATA */", "const SNAPSHOT=" + payload + ";"))
    print(f"Wrote {output.name} from {DEFAULT_PATH.name}; input {snapshot['integrity']['content_sha256']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "snapshot-view.html")
    build(parser.parse_args().output)
