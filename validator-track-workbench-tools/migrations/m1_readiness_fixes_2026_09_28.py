"""Readiness fixes found by a cold-read agent check (2026-09-28).

- CS (current-system components): source_version field, mechanisms required, concepts
  optional, change vocabulary aligned with the runbook (adds option).
- MX: current_system field, so a mechanism can record an explicit "none".
- Code sources: SRC-GOLP, SRC-CLEARINGHOUSE, SRC-PROTOCOL with commit or content hash.
- Stale M1.2 labels on the current-system map corrected to M1.4; field definitions for
  requires and story_status now name mechanisms.
- Voice: "paying yourself" removed from mechanism stories.
- M1.4 gains a live mechanism-coverage table.

Usage: python3 m1_readiness_fixes_2026_09_28.py WIKI > readiness.json
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
        k = k.replace("__", "-")
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


# CS schema
cs = cur("$:/vtw/schema/CS")
disp = cs["display"].split()
if "source_version" not in disp:
    disp.insert(disp.index("layer") + 1, "source_version")
put("$:/vtw/schema/CS", display=" ".join(disp),
    text="One contract, off-chain component or participant role in the current system, mapped to the mechanisms it serves (M1.4).",
    required="caption status layer change mechanisms source_ref stage introduced_by",
    **{"needs-concepts": "no", "vocab-change": "retain modify replace remove new option unknown"})
put("$:/vtw/template/CS", source_version="", mechanisms="", stage="M1")

# MX current_system
mx = cur("$:/vtw/schema/MX")
d = mx["display"].split()
if "current_system" not in d:
    d.insert(d.index("depends_on") + 1, "current_system")
put("$:/vtw/schema/MX", display=" ".join(d))
put("$:/vtw/template/MX", current_system="")

# field dictionary
lines = []
for line in cur("$:/vtw/fields")["text"].splitlines():
    key = line.split(":", 1)[0].strip()
    if key == "components":
        line = "components: CS IDs (M1.4)."
    elif key == "requires":
        line = "requires: Mechanisms: the chain from purpose to output, showing what the paper specifies and what is still to build or decide. Items are required to implement stated behaviour unless marked as a possible design option."
    elif key == "story_status":
        line = "story_status: Mechanisms: 'agent draft' once an agent has drafted the story in the text, 'edited' after a person has edited it. Absent means no story yet."
    elif key == "deployed_version":
        line = "deployed_version: Deployed version, address or release whose behaviour was actually checked (CS). Leave empty when only source code was read."
    elif key == "change":
        line = "change: Current system to litepaper: retain, modify, replace, remove, new, option or unknown (CS)."
    lines.append(line)
text = "\n".join(lines)
for k, v in (("source_version", "Commit or content hash of the source inspected (CS). Source behaviour, not deployed behaviour."),
             ("current_system", "Mechanisms: summary of the current-system counterpart, or 'none' with a reason (M1.4). Component records link here through their mechanisms field.")):
    if not any(l.startswith(k + ":") for l in lines):
        text += f"\n{k}: {v}"
put("$:/vtw/fields", text=text)

# code sources
put("SRC-GOLP", tags="Source", record_kind="source", caption="go-livepeer (local clone of github.com/livepeer/go-livepeer)",
    local_path="/home/mav/repos/livepeer/go-livepeer", commit="9e68815adf5e72b9c285f178bcdd25b42211efbb", commit_date="2026-04-02",
    text="Current-system source for M1.4. Locator format: SRC-GOLP followed by a repository path, optionally with :line, e.g. SRC-GOLP server/remote_signer.go:120. Source code shows what the software does, not what is deployed.")
put("SRC-CLEARINGHOUSE", tags="Source", record_kind="source", caption="clearinghouse (local clone of github.com/livepeer/clearinghouse)",
    local_path="/home/mav/repos/livepeer/clearinghouse", commit="ec3b2e2c9d1e1ff9a1dfd387235d9ebe63b995a1", commit_date="2026-07-07",
    text="Current-system source for M1.4. Locator format: SRC-CLEARINGHOUSE followed by a repository path. Whether and where it is deployed must be checked separately.")
put("SRC-PROTOCOL", tags="Source", record_kind="source", caption="Livepeer protocol contracts (local copy, not a git checkout)",
    local_path="/home/mav/repos/livepeer/smart contracts/protocol",
    sha256="f63257ab662c4979ecb2320a3eb2bce3da4c8b024ca43e84fb926fb493efb65c",
    text="Current-system source for M1.4. The local copy is not a git checkout; sha256 is taken over the sorted sha256 lines of every contracts/**/*.sol file. Locator format: SRC-PROTOCOL followed by a path, e.g. SRC-PROTOCOL contracts/bonding/BondingManager.sol. Record the deployed contract address and version separately when behaviour is checked on chain.")

# stale labels on the component view
put("View: Component impact", description="Current system to litepaper, by component and mechanism (M1.4)",
    text=cur("View: Component impact")["text"].replace("This is part of M1.2, which has not started.", "M1.4 has not started."))

# voice
replace_in("MX-03", "text", [("whether paying yourself can grow the whole reward pool", "whether a party paying its own node can grow the whole reward pool")])
replace_in("MX-04", "text", [("paying yourself may also grow the pool", "a party paying its own node may also grow the pool"),
                             ("Whether paying yourself for real work is profitable", "Whether paying one's own node for real work is profitable")])

# M1.4 wording and coverage table
put("M1.4", starting_point="""The mechanisms and their critical questions are defined in M1.1 and M1.2. This step maps them onto the current Livepeer system: versioned contracts, off-chain components such as payment tickets, the remote signer, gateways and orchestrators, and participant workflows. Each component is marked retain, modify, replace, remove, new, option or unknown, and linked to the mechanisms it serves.""",
    text="""<div class="vtw-step">
<h3>What this step will do</h3>
<p>Inspect the local current-system sources (<<r SRC-PROTOCOL>>, <<r SRC-GOLP>>, <<r SRC-CLEARINGHOUSE>>) and record one component per contract, off-chain component or participant role, with the source version inspected and the mechanisms it serves. Record a deployed version only when deployed behaviour was actually checked. Where a mechanism has no current counterpart, say so on the mechanism.</p>
<p>Earlier on 2026-09-28 this map was folded into the data step; it is restored here as its own task, matching issue #14.</p>
</div>

<div class="vtw-step">
<h3>Mechanism coverage</h3>
<table class="vtw-grid"><tbody>
<tr><th>Mechanism</th><th>Current components</th><th>Summary</th></tr>
<$list filter="[tag[MX]sort[title]]">
<tr><td><$link><$text text={{!!caption}}/></$link></td>
<td><$list filter="[tag[CS]contains:mechanisms<currentTiddler>sort[title]]" join=", " emptyMessage="—"><$link><$text text={{!!caption}}/></$link></$list></td>
<td><$transclude field="current_system" mode="inline"/></td></tr>
</$list>
</tbody></table>
<p>See also <<r "View: Component impact">>.</p>
</div>""")

conv = cur("Conventions")["text"]
anchor = "Records migrated from the unaccepted M1.1 drafts"
if anchor in conv and "SRC-GOLP" not in conv:
    conv = conv.replace(anchor, "Current-system sources are [[SRC-PROTOCOL]], [[SRC-GOLP]] and [[SRC-CLEARINGHOUSE]]; their locators are a repository path, optionally with :line. " + anchor, 1)
    put("Conventions", text=conv)

json.dump(list(OUT.values()), sys.stdout, indent=1, ensure_ascii=False)
print(f"{len(OUT)} tiddlers", file=sys.stderr)
