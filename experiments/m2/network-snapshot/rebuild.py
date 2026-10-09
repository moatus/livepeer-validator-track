"""Reconstruct the canonical dataset from its embedded sources, entirely offline."""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from build import assemble, digest
from read_snapshot import load_snapshot, DEFAULT_PATH


def rebuild(output):
    if output.exists():
        raise ValueError("Refusing to overwrite an existing artifact")
    if output.resolve() == DEFAULT_PATH.resolve():
        raise ValueError("Use a new output path")
    snapshot = load_snapshot()
    sources = snapshot["provenance"]["sources"]
    with TemporaryDirectory() as directory:
        raw = Path(directory)
        for name, source in sources.items():
            (raw / (name + ".json")).write_text(json.dumps(source["data"]))
        rebuilt = assemble(raw, raw / "operator_stake_rpc.json")
    # Original file byte hashes are recorded provenance. Embedded JSON preserves
    # data rather than original whitespace; its own hashes are independently checked.
    for name, source in sources.items():
        rebuilt["provenance"]["sources"][name]["original_file_sha256"] = source["original_file_sha256"]
    rebuilt.pop("integrity")
    actual = digest(rebuilt)
    if actual != snapshot["integrity"]["content_sha256"]:
        raise ValueError("Offline source reconstruction differs from the frozen input")
    rebuilt["integrity"] = snapshot["integrity"]
    output.write_text(json.dumps(rebuilt, indent=2, ensure_ascii=False) + "\n")
    print("PASS: independently reassembled from embedded sources:", actual)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    rebuild(parser.parse_args().output)
