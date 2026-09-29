"""Second readiness pass (2026-09-28): component view matches the CS design, the
SRC-PROTOCOL hash recipe is stated exactly, source_ref covers code locators.

Usage: python3 m1_readiness_fixes2_2026_09_28.py WIKI > readiness2.json
"""
import json, subprocess, sys
from pathlib import Path

VTW = Path(__file__).resolve().parents[1] / "vtw.py"
wiki = {t["title"]: t for t in json.loads(subprocess.check_output([sys.executable, str(VTW), "export", sys.argv[1]]))}
OUT = []

def put(title, **f):
    t = dict(wiki[title])
    for k in ("created", "modified", "modifier"):
        t.pop(k, None)
    t.update(f)
    OUT.append(t)

view = wiki["View: Component impact"]["text"]
for a, b in (
    ("Record the deployed version inspected.", "Record the source version inspected; record a deployed version only when deployed behaviour was checked."),
    ("<tr><th>ID</th><th>Component</th><th>Deployed version</th><th>Change</th><th>Concepts</th><th>Impact</th><th>Unknowns</th></tr>",
     "<tr><th>ID</th><th>Component</th><th>Source version</th><th>Deployed version</th><th>Change</th><th>Mechanisms</th><th>Impact</th><th>Unknowns</th></tr>"),
    ("<td><$text text={{!!deployed_version}}/></td><td><$text text={{!!change}}/></td>\n<td><$list filter=\"[all[current]get[concepts]enlist-input[]]\" join=\" \"><$link/></$list></td>",
     "<td><$text text={{!!source_version}}/></td><td><$text text={{!!deployed_version}}/></td><td><$text text={{!!change}}/></td>\n<td><$list filter=\"[all[current]get[mechanisms]enlist-input[]]\" join=\", \"><$link><$text text={{!!caption}}/></$link></$list></td>"),
):
    if a not in view:
        sys.exit(f"view: not found {a[:60]!r}")
    view = view.replace(a, b)
put("View: Component impact", text=view)

src = wiki["SRC-PROTOCOL"]["text"]
old = "sha256 is taken over the sorted sha256 lines of every contracts/**/*.sol file."
if old not in src:
    sys.exit("SRC-PROTOCOL text not found")
put("SRC-PROTOCOL", text=src.replace(old, "sha256 is reproduced from the protocol directory with: find contracts -name \"*.sol\" -type f | sort | xargs sha256sum | sha256sum (the checksum lines, in path order)."))

lines = []
for line in wiki["$:/vtw/fields"]["text"].splitlines():
    if line.startswith("source_ref:"):
        line = "source_ref: Explicit locator: source ID then a locator. Litepaper: line ranges, e.g. SRC-LP20 L55-63, L220. Code: a repository path, optionally with :line, e.g. SRC-GOLP server/remote_signer.go:120. Several sources are separated by ';'."
    lines.append(line)
put("$:/vtw/fields", text="\n".join(lines))

json.dump(OUT, sys.stdout, indent=1, ensure_ascii=False)
