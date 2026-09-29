"""Review corrections from T3 thread 4bb19e96 (runbook review, 2026-09-28).

- Chain items no longer default to "required": each item in the build column carries a
  basis label; an unlabelled item is unreviewed.
- The eleven families: the paper describes their functions; the grouping and boundaries
  are an analytical decomposition. MX provenance records the function's basis.
- current_system allows three outcomes: counterpart found, none found within a stated
  scope, or unresolved.
- VD-11: a score fixed per earning round is a possible design option, not a requirement;
  the paper reads the median current at claim time.

Usage: python3 m1_review_fixes_2026_09_28.py WIKI > review.json
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

VTW = Path(__file__).resolve().parents[1] / "vtw.py"
wiki = {t["title"]: t for t in json.loads(subprocess.check_output([sys.executable, str(VTW), "export", sys.argv[1]]))}
OUT: dict[str, dict] = {}


def put(title, **fields):
    t = dict(OUT.get(title) or wiki.get(title, {"title": title}))
    for k in ("created", "modified", "modifier"):
        t.pop(k, None)
    for k, v in fields.items():
        if v is None:
            t.pop(k, None)
        else:
            t[k] = v.strip("\n") if isinstance(v, str) else v
    OUT[title] = t


def cur(title):
    return OUT.get(title) or wiki[title]


def replace_in(title, field, pairs):
    txt = cur(title)[field]
    for a, b in pairs:
        if a not in txt:
            sys.exit(f"{title}.{field}: expected text not found: {a[:70]!r}")
        txt = txt.replace(a, b)
    put(title, **{field: txt})


BASIS = ("Each item in the last column carries its basis: required to implement stated behaviour, "
         "analytical decomposition, modelling assumption or possible design option. An item without a "
         "label has not been reviewed yet; it is not presumed required.")

replace_in("M1.1", "text", [
    ("All eleven are explicit in the paper, though the paper describes some in far more detail than others.",
     "The paper describes the function of each, some in far more detail than others; grouping those functions "
     "into these eleven families, and drawing their boundaries, is an analytical decomposition that may be revised."),
    ("Items in the last column are required to implement the stated behaviour unless marked as a possible design option.",
     BASIS),
])

lines = []
for line in cur("$:/vtw/fields")["text"].splitlines():
    key = line.split(":", 1)[0].strip()
    if key == "requires":
        line = ("requires: Mechanisms: the chain from purpose to output, showing what the paper specifies and "
                "what is still to build or decide. " + BASIS.replace("the last column", "the build column"))
    elif key == "provenance":
        line = ("provenance: MX and GT: explicit (in the paper), required (to implement stated behaviour), "
                "decomposition (analytical), assumption (modelling) or option (possible design choice). On MX it "
                "records the basis of the family's function; the grouping into families is always analytical.")
    elif key == "current_system":
        line = ("current_system: Mechanisms (M1.4): the current-system counterpart with source and version; "
                "'none found' with the scope examined; or 'unresolved' with the remaining search or deployment "
                "question. Component records link here through their mechanisms field.")
    lines.append(line)
put("$:/vtw/fields", text="\n".join(lines))

replace_in("Conventions", "text", [
    ("An option is never presented as a requirement.",
     "An option is never presented as a requirement, and an unlabelled item is unreviewed, not required."),
])

replace_in("M1.4", "text", [
    ("Where a mechanism has no current counterpart, say so on the mechanism.",
     "Each mechanism records one of three outcomes: a counterpart with its source and version; none found within "
     "a stated scope; or unresolved, with the remaining search or deployment question."),
])

put("VD-11",
    evidence_needed="Rules for a claim deadline, finality and late claims, and whether a score is fixed per earning round or read at claim time.",
    residual_uncertainty="No claim deadline, finality or late-claim treatment is specified. The paper reads the median current at claim time; fixing a score per earning round is a possible design option, not a stated requirement.",
    spec_settles="A claim deadline, finality and late-claim treatment; whether to keep claim-time scoring or fix a score per earning round (a possible design option).")

json.dump(list(OUT.values()), sys.stdout, indent=1, ensure_ascii=False)
print(f"{len(OUT)} tiddlers", file=sys.stderr)
