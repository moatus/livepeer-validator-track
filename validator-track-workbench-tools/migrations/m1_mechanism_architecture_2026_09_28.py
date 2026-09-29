"""Re-anchor the workbench on mechanisms, per the agent runbook (2026-09-28).

Governing document: /home/mav/repos/livepeer/validator-track-workbench-agent-runbook.md

- New record types: MX (mechanism family) and GT (critical question, the runbook's
  "candidate critical gate"; the workbench says "proposed" because the scope lint
  reserves the other word).
- Path follows the runbook: M1.1 mechanism architecture, M1.2 requirements and
  critical questions, M1.3 consequential cases, M1.4 current system and build map,
  M2.1 reconstruction, M2.2 tests, M2.3 findings and requirements. Orientation
  becomes a context page. The interim path is documented in View: Path history.
- Provenance restored: records first introduced by M1.1 (the baseline map, issue #6)
  go back to introduced_by M1.1; the interim "Orientation" label is removed.
- Stories and requires chains move from concepts (LP) to mechanisms (MX); open
  decisions gain a mechanisms field.
- Known runbook corrections: arithmetic is reproducible given defined inputs;
  aggregation is specified while score production is not; two design options are
  labelled as options; three procedural decisions lose an inherited judgment label.

Usage: python3 m1_mechanism_architecture_2026_09_28.py WIKI > mechanisms.json
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

VTW = Path(__file__).resolve().parents[1] / "vtw.py"
wiki = {t["title"]: t for t in json.loads(subprocess.check_output([sys.executable, str(VTW), "export", sys.argv[1]]))}
OUT: dict[str, dict] = {}
ISSUE = "https://github.com/moatus/livepeer-validator-track/issues/"
RUNBOOK = "/home/mav/repos/livepeer/validator-track-workbench-agent-runbook.md"


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


# ------------------------------------------------------------------ 1. restore provenance

for title, t in wiki.items():
    if title.startswith("$:/") or not t.get("record_type"):
        continue
    ch = {f: "M1.1" for f in ("introduced_by", "last_changed_by", "task") if t.get(f) == "Orientation"}
    if ch:
        put(title, **ch)

# ------------------------------------------------------------------ 2. schema: MX, GT, relations, vocabularies

put("$:/vtw/schema/MX", record_type="MX", name="Mechanism", plural="Mechanisms",
    text="One mechanism family: an end-to-end process that makes part of the litepaper architecture operate. Who acts, using what inputs, under what calculation or decision, to produce what outcome, for what purpose. A conceptual definition, not a contract or service boundary.",
    **{"id-pattern": r"^MX-\d{2}$", "required-tags": "Record MX",
       "display": "caption status provenance purpose operation depends_on concepts participants source_ref story_status related introduced_by last_changed_by",
       "required": "caption status provenance purpose operation concepts stage introduced_by",
       "vocab-status": "seed drafted reviewed", "vocab-provenance": "explicit required decomposition assumption option",
       "summary": "purpose", "needs-concepts": "yes"})
put("$:/vtw/template/MX", record_type="MX", stage="M1", status="seed", provenance="", caption="", purpose="", operation="",
    depends_on="", concepts="", participants="", source_ref="", story_status="", related="", requires="",
    introduced_by="", last_changed_by="", text="")

put("$:/vtw/schema/GT", record_type="GT", name="Critical question", plural="Critical questions",
    text="One proposed critical question (the runbook's gate): a point where a mechanism's success depends on something earlier steps have not established. Proposed until M2 assesses it under stated conditions. Default entry: the question, what would change the assessment, and the consequence if it resolves badly.",
    **{"id-pattern": r"^GT-\d{2}$", "required-tags": "Record GT",
       "display": "caption status provenance question would_change consequence mechanisms holds_if established control cases smallest_test decisions scenarios findings claims concepts participants related introduced_by last_changed_by",
       "required": "caption status provenance question would_change consequence mechanisms concepts stage introduced_by",
       "vocab-status": "proposed significant not-significant unresolved",
       "vocab-provenance": "explicit required decomposition assumption option",
       "summary": "question", "needs-concepts": "yes"})
put("$:/vtw/template/GT", record_type="GT", stage="M1", status="proposed", provenance="decomposition", caption="",
    question="", would_change="", consequence="", mechanisms="", holds_if="", established="", control="", cases="",
    smallest_test="", decisions="", scenarios="", findings="", claims="", concepts="", participants="", related="",
    introduced_by="", last_changed_by="", text="")

rel = cur("$:/vtw/relations")["text"]
for line in ("mechanisms: MX", "depends_on: MX"):
    if line not in rel:
        rel += "\n" + line
put("$:/vtw/relations", text=rel)

for rt in ("VD", "FR", "SC", "CL", "CN", "HQ", "CS"):
    s = cur(f"$:/vtw/schema/{rt}")
    disp = s["display"].split()
    if "mechanisms" not in disp:
        i = disp.index("concepts") if "concepts" in disp else len(disp)
        disp.insert(i, "mechanisms")
    put(f"$:/vtw/schema/{rt}", display=" ".join(disp))
    tpl = f"$:/vtw/template/{rt}"
    if tpl in wiki or tpl in OUT:
        put(tpl, mechanisms="")

put("$:/vtw/schema/CN", **{"vocab-status": "supported-by-text inference hypothesis superseded"})

fields = cur("$:/vtw/fields")["text"]
fields = fields.replace("record_type: LP, RL, VD, CL, FR, SC, EX, FX or CS. Also a tag.",
                        "record_type: LP, MX, GT, RL, VD, CL, FR, SC, EX, FX, CS, CN or HQ. Also a tag.")
fields = fields.replace("introduced_by: Task that created the record (Orientation, M1.1 ...). Records from the first pass were introduced by Orientation, formerly M1.1.",
                        "introduced_by: Task that created the record (M1.1 ...). Step identifiers had an interim meaning on 2026-09-28; see View: Path history. Never rewrite this field to tidy numbering.")
fields = fields.replace("consequence: What the decision changes.",
                        "consequence: VD: what the decision changes. GT: the consequence for the system if the question resolves badly.")
fields += "\n" + "\n".join([
    "mechanisms: MX IDs of the mechanisms the record concerns.",
    "depends_on: MX: mechanisms whose outputs this mechanism uses. Stored once, on the dependent; the reverse is derived.",
    "provenance: MX and GT: explicit (in the paper), required (to implement stated behaviour), decomposition (analytical), assumption (modelling) or option (possible design choice).",
    "purpose: MX: the intended benefit, in one sentence.",
    "operation: MX: who acts, using what inputs, under what calculation or decision, to produce what outcome.",
    "holds_if: GT (optional): what must hold for the intended transition to succeed.",
    "established: GT (optional): what earlier steps establish and what they do not.",
    "control: GT (optional): who controls inputs, acts, benefits, bears error costs or can withhold information.",
    "cases: GT (optional): the cooperative case and the market-pressure, strategic or lookalike case that tests it.",
    "smallest_test: GT (optional): the smallest test or evidence inquiry that could change the assessment.",
])
put("$:/vtw/fields", text=fields)

put("$:/vtw/provenance-plain", type="application/x-tiddler-dictionary",
    text="explicit: explicit in the paper\nrequired: required to implement stated behaviour\ndecomposition: analytical decomposition\nassumption: modelling assumption\noption: possible design option")

# ------------------------------------------------------------------ 3. procedures

proc = cur("$:/vtw/procedures")["text"]
proc = proc.replace('\\procedure vtw-buildlist(lp)\n<$transclude $variable="vtw-buildtable" filter="[tag[VD]!field:status[split]contains:concepts<lp>sort[title]]"/>\n\\end',
    '\\procedure vtw-buildlist(lp)\n<$transclude $variable="vtw-buildtable" filter="[tag[VD]!field:status[split]contains:concepts<lp>sort[title]]"/>\n\\end\n\n'
    '\\procedure vtw-mxbuild(mx)\n<$transclude $variable="vtw-buildtable" filter="[tag[VD]!field:status[split]contains:mechanisms<mx>sort[title]]"/>\n\\end')
if "vtw-mxbuild" not in proc:
    sys.exit("procedures: vtw-buildlist block not found")
proc += r"""
\procedure vtw-prov()
<%if [all[current]has[provenance]] %><span class="vtw-prov"><$text text={{{ [[$:/vtw/provenance-plain]getindex{!!provenance}] }}}/></span><%endif%>
\end

\procedure vtw-mxdeps()
<div class="vtw-mxdeps"><<vtw-prov>>
<%if [all[current]has[depends_on]] %>&#32;·&#32;''Depends on''&#32;<$list filter="[all[current]get[depends_on]enlist-input[]]" join=", "><$link><$text text={{!!caption}}/></$link></$list><%endif%>
<$let me=<<currentTiddler>>><%if [tag[MX]contains:depends_on<me>] %>&#32;·&#32;''Used by''&#32;<$list filter="[tag[MX]contains:depends_on<me>sort[title]]" join=", "><$link><$text text={{!!caption}}/></$link></$list><%endif%></$let>
</div>
\end

\procedure vtw-gates(mx)
<table class="vtw-grid vtw-build"><tbody>
<tr><th>Critical question</th><th>What would change the assessment</th><th>Consequence if it resolves badly</th></tr>
<$list filter="[tag[GT]contains:mechanisms<mx>sort[title]]" emptyMessage="<tr><td class='vtw-none'>None proposed yet.</td><td/><td/></tr>">
<tr><td><$link><$text text={{!!caption}}/></$link>&#32;<<vtw-status>><div class="vtw-readsum"><$transclude field="question" mode="inline"/></div></td>
<td><$transclude field="would_change" mode="inline"/></td>
<td><$transclude field="consequence" mode="inline"/></td></tr>
</$list>
</tbody></table>
\end

\procedure vtw-mxmap()
<table class="vtw-grid vtw-mxmap"><tbody>
<tr><th>Mechanism</th><th>Purpose</th><th>Depends on</th><th>Open pieces</th><th>Critical questions</th></tr>
<$list filter="[tag[MX]sort[title]]">
<tr><td><$link><$text text={{!!caption}}/></$link><div class="vtw-idsmall"><$text text={{{ [[$:/vtw/provenance-plain]getindex{!!provenance}] }}}/>&#32;·&#32;<$text text={{!!status}}/></div></td>
<td><$transclude field="purpose" mode="inline"/></td>
<td><$list filter="[all[current]get[depends_on]enlist-input[]]" join=", " emptyMessage="—"><$link><$text text={{!!caption}}/></$link></$list></td>
<td><$count filter="[tag[VD]!field:status[split]contains:mechanisms<currentTiddler>]"/></td>
<td><$count filter="[tag[GT]contains:mechanisms<currentTiddler>]"/></td></tr>
</$list>
</tbody></table>
\end
"""
put("$:/vtw/procedures", text=proc)

css = cur("$:/vtw/styles")["text"]
css += "\n" + "\n".join([
    ".vtw-prov { display: inline-block; padding: 0 0.45em; border-radius: 0.6em; font-size: 0.8em; background: #e3eaef; }",
    ".vtw-mxdeps { font-size: 0.9em; color: #4b6272; margin: 0.2em 0 0.6em; }",
    "table.vtw-mxmap td:first-child { width: 22%; }",
    "table.vtw-mxmap td:nth-child(4), table.vtw-mxmap td:nth-child(5) { width: 8%; text-align: center; }",
    ".vtw-history td { font-size: 0.93em; }",
])
put("$:/vtw/styles", text=css)

# ------------------------------------------------------------------ 4. mechanism records


def dedupe(cell):
    ref = re.compile(r"(?<![\w-])([A-Za-z][^();,]*?) \(<<r ([A-Z]{2}-\d{2})>>\)")

    def sub(m):
        cap = (cur(m.group(2)) if (m.group(2) in OUT or m.group(2) in wiki) else {}).get("caption", "")
        return f"<<r {m.group(2)}>>" if m.group(1).strip().lower() == cap.strip().lower() else m.group(0)
    return ref.sub(sub, cell)


def chain(rows):
    body = "\n".join(f"<tr><td>{a}</td><td>{dedupe(b)}</td><td>{dedupe(c)}</td></tr>" for a, b, c in rows)
    return ('<table class="vtw-grid vtw-chain"><tbody>\n<tr><th>Step</th><th>What the paper specifies</th><th>Still to build or decide</th></tr>\n'
            + body + "\n</tbody></table>")


OPT = "<span class=\"vtw-prov\">possible design option</span>&#32;"

MX = {
    "MX-01": dict(caption="Operator registration and discovery", provenance="explicit", concepts="LP-03 LP-01",
        participants="operator customer", source_ref="SRC-LP20 L23-29, L53", depends_on="",
        purpose="Make service offerings available for customers and agents to find, without a bond or a node cap.",
        operation="An operator registers an address and advertises capabilities, regions and prices in an onchain registry. Customers and agents select among the listings.",
        chain=[("Purpose", "Anyone can offer services, with no bond and no node cap (<<r RL-07>>, <<r RL-09>>).", "—"),
               ("Inputs", "An address registers and advertises capabilities, regions and prices (<<r RL-08>>).", "Advert format and verification (<<r VD-01>>)."),
               ("Output", "A listing in the onchain registry that agents use for discovery.", "Discovery and routing (<<r VD-02>>)."),
               ("Supporting machinery", "Registry contract.", OPT + "Whether a penalty should follow an actor across addresses. Registration does not require it; it is one response to the concern in <<r VD-27>>.")]),
    "MX-02": dict(caption="Payment settlement and fee allocation", provenance="explicit", concepts="LP-10 LP-11",
        participants="customer operator", source_ref="SRC-LP20 L113, L119, L210", depends_on="",
        purpose="Record what each customer paid each node, in USDC at USD prices, and divide it between the node and the network.",
        operation="Customers pay in USDC. Each settled fee is attributed to a node; the node receives its cut and the network's share goes to the buyback.",
        chain=[("Purpose", "Price in USD, pay in USDC, and divide each fee between node and network (<<r RL-32>>, <<r RL-35>>).", "—"),
               ("Inputs", "Customer payments.", "Payment security with unlimited nodes (<<r RL-61>>)."),
               ("Calculation", "50% to the node, 50% to the network's buyback (<<r RL-33>>, <<r RL-34>>).", "Split viability (<<r VD-15>>)."),
               ("Output", "Settled fees attributed to nodes; the node's USDC receipt; the network share.", "Attribution, reversals and accounting periods (<<r VD-03>>)."),
               ("Supporting machinery", "Payment contracts and signers.", "—")]),
    "MX-03": dict(caption="Emissions determination", provenance="explicit", concepts="LP-12 LP-13",
        participants="governance", source_ref="SRC-LP20 L128-172, L231-233", depends_on="MX-02 MX-11",
        purpose="Set the amount of new LPT available for a period and divide it among nodes, validators and the treasury.",
        operation="Governance selects a schedule. Under the fee-linked concepts, reported fees and an LPT price set the period's mint, subject to a proposed cap. The mint is split 94/1/5.",
        chain=[("Purpose", "Predictable issuance that reaches equilibrium with the burn (<<r RL-46>>).", "—"),
               ("Inputs", "Network fees for concepts 1 and 2; participation for concept 3; an LPT price for USD targets.", "Price source (<<r VD-14>>, <<r RL-62>>)."),
               ("Calculation", "Three concepts (<<r RL-47>>, <<r RL-48>>, <<r RL-49>>). Concept 1: emissions a declining multiple of fees, with a proposed annual cap (<<r RL-50>>).", "Which concept, period alignment and a zero-fee rule (<<r VD-14>>)."),
               ("Output", "LPT minted per period: 94% nodes, 1% validators, 5% treasury (<<r RL-54>>, <<r RL-55>>, <<r RL-56>>).", "How the validator slice is divided (<<r VD-17>>)."),
               ("Supporting machinery", "Price oracle and mint contract.", "An oracle that resists manipulation (<<r VD-14>>).")]),
    "MX-04": dict(caption="Operator reward allocation", provenance="explicit", concepts="LP-04 LP-13",
        participants="operator delegator", source_ref="SRC-LP20 L55-63, L231", depends_on="MX-02 MX-03 MX-06 MX-08 MX-09",
        purpose="Tie each node's inflation reward to its share of fees, capped by its share of stake.",
        operation="Each round the protocol takes the smaller of a node's fee share and stake share, applies it to the node emission envelope, and scales it by the median honesty score.",
        chain=[("Purpose", "Tie inflation rewards to real work, limited by stake (<<r RL-03>>, <<r RL-11>>).", "—"),
               ("Inputs", "Node fee share and stake share of network totals; the median honesty score.", "Eligible fees, windows, snapshots and denominators (<<r VD-05>>)."),
               ("Calculation", "Smaller of fee share and stake share, times the node emission share, times the median score (<<r RL-10>>, <<r RL-24>>, <<r RL-54>>).", "One formula reconciling main text and appendix (<<r VD-06>>)."),
               ("Output", "The node's LPT reward for the round, claimable after seven rounds (<<r RL-30>>).", "What happens to unassigned reward (<<r VD-12>>)."),
               ("Supporting machinery", "Fee accounting, staking ledger, score contract, emissions mint.", "Payment attribution (<<r VD-03>>) and the mint schedule (<<r VD-14>>).")]),
    "MX-05": dict(caption="Evidence collection and investigation", provenance="explicit", concepts="LP-07 LP-14",
        participants="validator governance", source_ref="SRC-LP20 L86-88", depends_on="MX-02 MX-11",
        purpose="Gather the testing, monitoring and anomaly evidence that validators rely on.",
        operation="Publicly funded teams build testing frameworks, monitoring, dashboards and anomaly detection and publish evidence. Validators draw on it and on other surfaced criteria.",
        chain=[("Purpose", "Do the hard work behind judgments once, as a public good, rather than in every validator (<<r RL-26>>).", "Funding and oversight (<<r VD-28>>)."),
               ("Inputs", "Payment records, service observations and test results.", "Execution and delivery evidence (<<r VD-04>>); correctness criteria (<<r VD-22>>)."),
               ("Selection", "Anomalies are to be noticed within the seven-round window (<<r RL-30>>).", "Who gets investigated (<<r VD-25>>)."),
               ("Output", "Published evidence validators can use.", "Evidence standards, provenance and privacy (<<r VD-26>>).")]),
    "MX-06": dict(caption="Honesty assessment and reward adjustment", provenance="explicit", concepts="LP-07",
        participants="validator operator", source_ref="SRC-LP20 L86-88", depends_on="MX-05 MX-07",
        purpose="Deny inflation rewards for dishonest work: self-dealing, fee fabrication and incorrect results.",
        operation="Active validators consider evidence and submit a score from 0 to 1 for each node. The median scales the node's MFS reward, read at claim time.",
        chain=[("Purpose", "Deny rewards for dishonest work; not a service-quality grade (<<r RL-25>>).", "—"),
               ("Assessment", "Validators vote on published evidence or other surfaced criteria.", "Criteria and proof standard (<<r VD-09>>); outage versus dishonesty (<<r VD-23>>); correctness (<<r VD-22>>)."),
               ("Finding to score", "Each active validator scores each node from 0 to 1 (<<r RL-23>>).", "Mapping from a finding to a number (<<r VD-09>>). The finding-to-score stage is an analytical boundary; the paper does not specify that internal process."),
               ("Aggregation", "The median of active validators' scores (<<r RL-24>>).", "Quorum, abstention and recusal (<<r VD-10>>); independence (<<r VD-29>>)."),
               ("Consequence", "The median scales the MFS reward, read at claim time (<<r RL-31>>).", "Which score applies (<<r VD-07>>); authority over policy and cases (<<r VD-21>>).")]),
    "MX-07": dict(caption="Validator selection and compensation", provenance="explicit", concepts="LP-06 LP-13",
        participants="validator operator delegator", source_ref="SRC-LP20 L79-84, L221, L232", depends_on="MX-08 MX-03",
        purpose="Decide who may judge, make the judging set expensive to capture, and pay for the role.",
        operation="The top N nodes by total stake that opt in become active validators, N proposed at 33. They share the validator slice of new LPT.",
        chain=[("Purpose", "Put judging with the highest-staked nodes, making the set expensive to capture.", "—"),
               ("Inputs", "Total stake per node and opt-in registrations (<<r RL-19>>).", "Snapshots and ranking population (<<r VD-08>>)."),
               ("Selection", "Top N by stake among those who opt in; the next registered node fills a decline (<<r RL-20>>, <<r RL-21>>).", "Ties and vacancies (<<r VD-08>>)."),
               ("Output", "The active validator set and its share of new LPT (<<r RL-22>>, <<r RL-55>>).", "Equal or stake-weighted split, and any participation condition (<<r VD-17>>)."),
               ("Supporting machinery", "Registry, staking ledger, score contract.", "Independence and conflicts (<<r VD-29>>).")]),
    "MX-08": dict(caption="Delegation and stake movement", provenance="explicit", concepts="LP-05 LP-08",
        participants="delegator operator", source_ref="SRC-LP20 L65-77, L92-105", depends_on="",
        purpose="Let delegators back operators, raise reward ceilings and shape the validator set, with lockups that deter hit-and-run behaviour.",
        operation="Delegators bond LPT to nodes under operator-set cuts. Unbonding takes 21 rounds, and moving a bond between nodes is removed or delayed.",
        chain=[("Purpose", "Route stake toward productive, understaked nodes; stake also elects validators (<<r RL-16>>, <<r RL-17>>).", "—"),
               ("Inputs", "Delegators' choices; reward and fee cuts offered by operators (<<r RL-15>>).", "Information delegators need to choose well (<<r FR-15>>)."),
               ("Rule", "21-round unbonding for all stake behind a node (<<r RL-27>>); bond transfer removed or delayed (<<r RL-28>>, <<r RL-29>>).", "Which option (<<r VD-13>>)."),
               ("Output", "Stake per node, which sets reward ceilings and validator eligibility. Rewards can be reduced; principal is not slashed.", "—"),
               ("Supporting machinery", "Staking contract.", "Whether a penalty can follow the actor as well as the address (<<r VD-27>>).")]),
    "MX-09": dict(caption="Reward claiming and finality", provenance="explicit", concepts="LP-09 LP-07",
        participants="operator validator", source_ref="SRC-LP20 L107-109, L224", depends_on="MX-06",
        purpose="Delay claims so validators can react to anomalies before rewards are paid.",
        operation="Rewards for round n become claimable at n+7, using the median score current at the time of claiming.",
        chain=[("Purpose", "Give validators time to catch a single-round fee spike before rewards can be claimed.", "—"),
               ("Rule", "Rewards for round n become claimable at n+7 (<<r RL-30>>).", "Claim deadline and finality (<<r VD-11>>)."),
               ("Inputs", "Round counter; the median score at the time of claiming (<<r RL-31>>).", "Which median applies (<<r VD-07>>)."),
               ("Output", "A claimable reward at the then-current score.", OPT + "Whether to fix a score per earning round instead of reading it at claim time. That would change the paper's claim-time rule; its effects belong with <<r VD-11>>.")]),
    "MX-10": dict(caption="Buyback and burn", provenance="explicit", concepts="LP-11",
        participants="governance", source_ref="SRC-LP20 L117-125, L237-246", depends_on="MX-02",
        purpose="Convert the network's share of fees into purchased LPT and burn it.",
        operation="Accumulated network fees buy LPT from a DEX pool at intervals, within TWAP and slippage limits. All purchased LPT is burned.",
        chain=[("Purpose", "Tie LPT value to usage by buying and burning LPT (<<r RL-46>>).", "—"),
               ("Inputs", "The network's share of settled fees.", "—"),
               ("Calculation", "All purchased LPT is burned; rewards come from a separate mint (<<r RL-36>>, <<r RL-40>>).", "Denominators if the burn is ever below 100% (<<r VD-16>>)."),
               ("Supporting machinery", "DEX buyback with illustrative TWAP, frequency and slippage parameters (<<r RL-43>>, <<r RL-44>>, <<r RL-45>>).", "Execution design and price (<<r VD-18>>)."),
               ("Output", "LPT burned.", "Actual burn against actual mint, once execution exists (<<r VD-16>>).")]),
    "MX-11": dict(caption="Parameter and score-contract governance", provenance="explicit", concepts="LP-14 LP-02",
        participants="governance validator", source_ref="SRC-LP20 L37, L75, L90, L222", depends_on="",
        purpose="Keep parameters adjustable and the scoring mechanism replaceable.",
        operation="Stake-weighted governance adjusts the listed parameters and can point the score contract at another implementation.",
        chain=[("Purpose", "Leave room for governance to adjust the incentive model (<<r RL-05>>).", "—"),
               ("Decision", "Governance adjusts parameters and can swap the score contract address (<<r RL-57>>).", "Separation of policy from case decisions (<<r VD-21>>); the validator constitution (<<r RL-65>>)."),
               ("Output", "Parameter values and the active score contract.", "—")]),
}

# stories move from concepts to mechanisms
STORY_SRC = {"MX-04": ["LP-04"], "MX-06": ["LP-07"], "MX-07": ["LP-06"], "MX-09": ["LP-09"],
             "MX-03": ["LP-12"], "MX-02": ["LP-11"], "MX-08": ["LP-05", "LP-08"]}
STEP_FIX = [
    ("M1.2 checks what data a validator could actually hold; M1.3 lays out who is asked to judge whom; M2.1 asks what a validator gains or loses from each choice.",
     "M1.2 examines what evidence a validator could hold and who decides; M1.3 sets out the cases that matter; M2.1 reconstructs what a validator gains or loses from each choice."),
    ("M2.2 records, piece by piece, what would resolve each gap", "M2.3 records, piece by piece, what would resolve each gap"),
    ("that is a worked example for M2.1, not a finding yet", "that is a worked example for M2.2, not a finding yet"),
    ("M2.1 runs the numbers.", "M2.2 runs the numbers."),
    ("M1.3 maps who judges whom.", "M1.2 maps who decides, and on what evidence."),
    ("M2.1 runs each concept, clearly labelled, through the same small examples.", "M2.2 runs each concept, clearly labelled, through the same small examples."),
    ("M2.1 uses the split in every worked example.", "M2.2 uses the split in every worked example."),
    ("M2.1 compares the lockup cost with what could be extracted.", "M2.2 compares the lockup cost with what could be extracted."),
]
SEC = re.compile(r"<h3>([^<]+)</h3>\s*<p>(.*?)</p>", re.S)
HEAD = ('<div class="vtw-storynote">Mechanism story, drafted by an agent from the records below. Edit it freely, or '
        '<$link to="View: Contributor notes">leave a note</$link> where it is wrong.</div>')


def sections(lp):
    txt = cur(lp)["text"]
    for a, b in STEP_FIX:
        txt = txt.replace(a, b)
    return {h: p for h, p in SEC.findall(txt)}


def story(mx, parts):
    def para(key):
        return "</p>\n<p>".join(p for p in (s.get(key) for s in parts) if p)
    return f"""{HEAD}

<div class="vtw-story">
<<vtw-mxdeps>>
<h3>What the paper specifies</h3>
<p>{para("What the paper specifies")}</p>
<h3>How it works end to end</h3>
<$transclude field="requires" mode="block"/>
<h3>What it leaves to be built</h3>
<p>{para("What it leaves to be built")}</p>
<$transclude $variable="vtw-mxbuild" mx="{mx}"/>
<h3>Critical questions</h3>
<$transclude $variable="vtw-gates" mx="{mx}"/>
<h3>Working hypothesis and how it will be tested</h3>
<p>{para("Working hypothesis and how it will be tested")}</p>
<h3>Where it goes next</h3>
<p>{para("Where it goes next")}</p>
</div>"""


def bare(mx):
    return f"""<div class="vtw-storynote">No story drafted yet. The chain and tables below are drawn from the records.</div>

<div class="vtw-story">
<<vtw-mxdeps>>
<h3>How it works end to end</h3>
<$transclude field="requires" mode="block"/>
<h3>What it leaves to be built</h3>
<$transclude $variable="vtw-mxbuild" mx="{mx}"/>
<h3>Critical questions</h3>
<$transclude $variable="vtw-gates" mx="{mx}"/>
</div>"""


for mx, f in MX.items():
    rows = f.pop("chain")
    f = {k: v for k, v in f.items() if v != ""}
    srcs = STORY_SRC.get(mx)
    text = story(mx, [sections(lp) for lp in srcs]) if srcs else bare(mx)
    put(mx, tags="Record MX", record_type="MX", stage="M1", status="seed", introduced_by="M1.1", last_changed_by="M1.1",
        requires=chain(rows), text=text, story_status="agent draft" if srcs else "", **f)
    if not srcs:
        put(mx, story_status=None)

replace_in("MX-08", "text", [(
    "Whether and when stake can move between nodes (<<r VD-13>>), and what information delegators need to choose well (<<r FR-15>>).</p>\n<p>Which option for moving stake (<<r VD-13>>), and whether a penalty follows a person or only an address (<<r VD-27>>).",
    "Whether and when stake can move between nodes (<<r VD-13>>), what information delegators need to choose well (<<r FR-15>>), and whether a penalty follows a person or only an address (<<r VD-27>>).")])

for lp in ("LP-03", "LP-04", "LP-05", "LP-06", "LP-07", "LP-08", "LP-09", "LP-10", "LP-11", "LP-12", "LP-13", "LP-14"):
    put(lp, text="", requires=None, story_status=None)
put("$:/vtw/schema/LP", display=cur("$:/vtw/schema/LP")["display"].replace(" story_status", ""))

# ------------------------------------------------------------------ 5. decisions: mechanisms, reclassification

VDMX = {"VD-01": "MX-01", "VD-02": "MX-01", "VD-03": "MX-02", "VD-04": "MX-05", "VD-05": "MX-04", "VD-06": "MX-04",
        "VD-07": "MX-06 MX-09", "VD-08": "MX-07", "VD-09": "MX-06", "VD-10": "MX-06", "VD-11": "MX-09", "VD-12": "MX-04",
        "VD-13": "MX-08", "VD-14": "MX-03", "VD-15": "MX-02", "VD-16": "MX-10", "VD-17": "MX-07", "VD-18": "MX-10 MX-03",
        "VD-19": "MX-06 MX-04", "VD-20": "MX-01 MX-04 MX-07 MX-08", "VD-21": "MX-11 MX-06", "VD-22": "MX-05 MX-06",
        "VD-23": "MX-06", "VD-24": "MX-04 MX-06", "VD-25": "MX-05", "VD-26": "MX-05", "VD-27": "MX-08 MX-01",
        "VD-28": "MX-05 MX-11", "VD-29": "MX-07 MX-06"}
for vd, mx in VDMX.items():
    put(vd, mechanisms=mx)

RECLASS = "Reclassified 2026-09-28 from D+J+G to D+G: once written, the procedure is deterministic; the scores it carries are judgments (VD-09)."
for vd in ("VD-07", "VD-10", "VD-11"):
    t = cur(vd)
    assert t["classification"] == "D+J+G", vd
    note = (t.get("migration_note", "") + " " + RECLASS).strip()
    put(vd, classification="D+G", migration_note=note)

# ------------------------------------------------------------------ 6. critical questions (seeded from the runbook's worked examples)

GTS = {
    "GT-01": dict(caption="Does the evidence warrant an adverse finding?", mechanisms="MX-06 MX-05",
        question="Does the available evidence distinguish a defined violation from legitimate activity well enough to justify a reward consequence?",
        would_change="A defined observation set that separates self-dealing, fabrication or incorrect results from their legitimate lookalikes at acceptable error and cost would weaken the concern. Showing that key pairs share every available observation would strengthen it.",
        consequence="Adverse findings rest on weak evidence, or abuse goes unaddressed, and the honesty score cannot do the job the paper assigns it.",
        decisions="VD-09 VD-19 VD-22 VD-26", scenarios="SC-06 SC-07 SC-10 SC-11", concepts="LP-07", participants="validator operator"),
    "GT-02": dict(caption="Will validators produce defensible assessments?", mechanisms="MX-06 MX-07",
        question="Given overlapping operator roles, effort costs and possible responses by others, will validators investigate and act on defensible assessments?",
        would_change="Pay that rewards accurate review, visible reputational or delegation consequences for careless scoring, or evidence of careful scoring in comparable settings would weaken the concern. A reconstruction in which careful review costs more than it earns would strengthen it.",
        consequence="Scores drift toward uniform leniency or coordinated hostility, and the median no longer reflects evidence.",
        decisions="VD-10 VD-17 VD-29", scenarios="SC-09", concepts="LP-06 LP-07", participants="validator operator delegator"),
    "GT-03": dict(caption="Does more rewarded fee require the intended contribution?", mechanisms="MX-04 MX-03 MX-02",
        question="Does increasing the fee input that drives rewards require the contribution the network intends to reward, or is there a cheaper route, such as paying for one's own real jobs?",
        would_change="A worked example under the paper's parameters in which self-funded jobs cost more than the reward they add, across the emissions concepts, would weaken it. A positive margin under plausible assumptions would strengthen it.",
        consequence="Rewards can be bought, and preventing that falls to the honesty assessment (GT-01).",
        findings="FR-01 FR-19 FR-23", decisions="VD-05 VD-14 VD-15 VD-19", scenarios="SC-06 SC-07", concepts="LP-04 LP-12", participants="operator delegator"),
    "GT-04": dict(caption="Can delegators move stake to useful operators in time?", mechanisms="MX-08",
        question="Can enough delegators identify productive, understaked operators and move stake quickly enough for delegation to improve allocation?",
        would_change="Evidence of timely stake movement under comparable lockups, or information delegators can act on, would weaken it. Slow movement, or returns that reward reported activity regardless of usefulness, would strengthen it.",
        consequence="Reward ceilings stay with incumbents, or follow reported returns rather than useful work.",
        findings="FR-08 FR-15", decisions="VD-13", scenarios="SC-04 SC-08", concepts="LP-05 LP-08", participants="delegator operator"),
}
for gt, f in GTS.items():
    put(gt, tags="Record GT", record_type="GT", stage="M1", status="proposed", provenance="decomposition",
        introduced_by="M1.2", last_changed_by="M1.2", **f)
put("MX", caption="Mechanisms", text="<<vtw-type-index>>")
put("GT", caption="Critical questions", text="<<vtw-type-index>>")

# ------------------------------------------------------------------ 7. conclusions: move to M1.1, correct the two flagged overstatements

for cn in ("CN-01", "CN-02", "CN-03", "CN-04", "CN-05", "CN-06", "CN-07", "CN-08", "CN-09"):
    put(cn, task="M1.1")
put("CN-02", carried_to="M1.2 M2.1")
put("CN-03", carried_to="M1.2 M1.3")
put("CN-06", carried_to="M1.2 M2.1")
put("CN-07", caption="The reward arithmetic is reproducible given defined inputs", mechanisms="MX-02 MX-03 MX-04 MX-06 MX-09",
    statement="Once rules are chosen, anyone can reproduce the fee split, the MFS minimum, the emission shares, the median and the delay counters from the same inputs. Several of those inputs come from outside the protocol's own records: which fees count as settled and attributable, the LPT price that the USD-denominated emission options and the buyback need, the result of buyback execution, and the validators' scores. Being reproducible does not make a calculation sound; each still has to be checked for the behaviour it rewards.",
    basis="Nine open decisions need only a formula and a policy choice. The inputs named here sit in decisions that need outside data or a judgment (VD-03, VD-14, VD-18, VD-09). A fully specified fee-linked formula may still reward self-payment (FR-01).",
    decisions="VD-01 VD-06 VD-08 VD-12 VD-13 VD-15 VD-03 VD-14 VD-18", carried_to="M1.2 M2.1")
put("CN-08", caption="Score aggregation is specified; score production is not", mechanisms="MX-05 MX-06 MX-09",
    statement="The paper specifies how submitted scores become a reward: the median of 0-to-1 scores scales the MFS reward at claim time. It leaves open how a score is produced: what evidence is collected, what criteria define each kind of dishonesty, and how a finding becomes a number. Validators are also operators, so a lower score means one operator finding against another; whether that creates conflicts is a question for later steps.",
    basis="Aggregation and application are explicit (RL-23, RL-24, RL-31). The evidence, criteria and finding-to-score decisions are open (VD-09, VD-22, VD-23, VD-26). Procedures such as finality and abstention can be written as deterministic rules even though the scores they carry are judgments (VD-07, VD-10, VD-11).",
    provisions="RL-23 RL-24 RL-25 RL-31", decisions="VD-09 VD-22 VD-23 VD-26 VD-07 VD-10 VD-11", carried_to="M1.2 M1.3")
put("CN-09", carried_to="M1.2 M2.1 M2.3")

# ------------------------------------------------------------------ 8. path and steps

put("$:/vtw/path", list="M1.1 M1.2 M1.3 M1.4 M2.1 M2.2 M2.3")
put("M1", caption="Define the litepaper architecture",
    text="Name the mechanisms that make the litepaper's architecture operate, examine what each requires and where its critical questions lie, frame the cases that matter, and map what exists today. Missing detail is recorded as something to build, never as a fault in the paper.")
put("M2", caption="Reconstruct and test the litepaper's incentives",
    question="When the mechanisms are assembled under stated interpretations, do participants' combined incentives produce the intended behaviour, and what resolves each concern?",
    text="Reassemble the mechanisms into one system, test the consequential interactions and critical questions, and consolidate findings into requirements for M3.")

old_m11 = cur("M1.1")["text"]
put("Orientation", tags="Context", caption="Orientation: how the paper works",
    text='<p class="vtw-lede">A short orientation to the paper\'s intended cooperative flow. It is context for all four M1 steps; its conclusions are recorded with <$link to="M1.1">M1.1</$link>.</p>\n\n' + cur("Orientation")["text"])

ONLY_DG = "[tag[VD]!field:status[split]] :filter[get[classification]split[+]remove[D G]count[]match[0]]"
HAS_E = "[tag[VD]!field:status[split]] :filter[get[classification]split[+]match[E]]"
HAS_J = "[tag[VD]!field:status[split]] :filter[get[classification]split[+]match[J]]"
ALL_VD = "[tag[VD]!field:status[split]]"
NEW_VD = "VD-23 VD-24 VD-25 VD-26 VD-27 VD-28 VD-29"

put("M1.1", caption="How the architecture works, mechanism by mechanism", planned_artifact="deliverables/m1/litepaper-baseline-map.md",
    question="What mechanisms does the litepaper propose or require, what does each do, what does it depend on, and which of its operations can be reproduced from defined inputs?",
    starting_point="""The litepaper sets out an architecture and a vision. This step names the mechanisms that would make it operate: who acts, using what inputs, under what calculation or decision, to produce what outcome, and for what purpose. Specified parts are included alongside open ones, so the result is a build inventory for this stage rather than a list of omissions.

The intended cooperative flow of money and rewards is summarized in the <<r Orientation>>. Its first-pass conclusions are recorded below with this step's own.""",
    text=f"""<div class="vtw-step">
<h3>The mechanisms</h3>
<p>Eleven mechanism families make the architecture operate. Each is a conceptual definition, not a contract or service boundary. All eleven are explicit in the paper, though the paper describes some in far more detail than others. Operator reward allocation sits at the centre: it uses the outputs of settlement, emissions, honesty assessment, delegation and claiming.</p>
<<vtw-mxmap>>
</div>

<div class="vtw-step">
<h3>Four kinds of requirement</h3>
<p>Every open piece in a mechanism needs one or more of these:</p>
<ul>
<li>''A formula.'' Arithmetic over numbers the protocol already holds: stake balances, settled fees, round counters.</li>
<li>''Data from outside the protocol.'' Someone has to observe something the chain cannot see, such as whether a job was delivered.</li>
<li>''A judgment.'' Someone has to interpret incomplete evidence or intent, such as whether a payment was self-dealing.</li>
<li>''A policy choice.'' Governance picks a rule once. After that, the rule can usually be computed.</li>
</ul>
<p>AI media work adds one more consideration: many outputs legitimately vary between runs, so "correct" has to allow for that. Variable output does not by itself make work unverifiable; some properties can be checked without reproducing the same result.</p>
<p>A procedure is not a judgment just because it carries one. The median of validator scores, the claim window and the abstention rule can all be exact once written, even though every score they carry is a judgment.</p>
</div>

<div class="vtw-step">
<h3>Each mechanism, end to end</h3>
<p>Each mechanism below runs from purpose to output, with what the paper specifies beside what is still to build or decide. Items in the last column are required to implement the stated behaviour unless marked as a possible design option. Under each chain, every open piece records what it needs, what a specification would settle, and what would still need testing. The classification is an agent's first proposal until someone reviews it.</p>
<$list filter="[tag[MX]sort[title]]" variable="mx">
<details class="vtw-details vtw-mech"><summary><$text text={{{{{{ [<mx>get[caption]] }}}}}}/>&#32;·&#32;<$count filter="[tag[VD]!field:status[split]contains:mechanisms<mx>]"/>&#32;open&#32;·&#32;<$count filter="[tag[VD]!field:status[split]contains:mechanisms<mx>contains:resolved_by[evidence]]"/>&#32;need evidence&#32;·&#32;<$count filter="[tag[VD]!field:status[split]contains:mechanisms<mx>contains:resolved_by[incentives]]"/>&#32;need incentive analysis</summary>
<$transclude tiddler=<<mx>> field="requires" mode="block"/>
<$transclude $variable="vtw-mxbuild" mx=<<mx>>/>
</details>
</$list>
</div>

<div class="vtw-step">
<h3>The reward arithmetic is reproducible given defined inputs</h3>
<p>The fee split, the MFS minimum, the emission shares, the median and the delay counters are all arithmetic (<<r RL-10>>, <<r RL-24>>, <<r RL-35>>, <<r RL-53>>). Once policy fixes measurement windows, the treatment of unassigned reward and finality, anyone can reproduce the results from the same inputs. Some of those inputs come from outside the protocol's own records: attributed fees, an LPT price, buyback execution and validator scores.</p>
<div class="vtw-data"><$count filter="{ONLY_DG}"/>&#32;of the&#32;<$count filter="{ALL_VD}"/>&#32;open pieces need nothing more than a formula and a policy choice:&#32;<$list filter="{ONLY_DG} +[sort[title]]" join=", "><$link><$text text={{{{!!caption}}}}/></$link></$list>.</div>
<div class="vtw-leadsto">Leads to: <<r CN-07>></div>
</div>

<div class="vtw-step">
<h3>Score aggregation is specified; score production is not</h3>
<p>The paper says how submitted scores become a reward. It leaves open how a score is produced: what evidence is gathered, what criteria define each kind of dishonesty, and how a finding becomes a number. The paper describes reward eligibility as "inherently subjective" (litepaper line 83). Validators are operators, so a lower score means one operator finding against another.</p>
<div class="vtw-data"><$count filter="{HAS_E}"/>&#32;open pieces need data from outside the protocol and&#32;<$count filter="{HAS_J}"/>&#32;need a judgment. Of the judgments,&#32;<$count filter="{HAS_J} :filter[get[mechanisms]enlist-input[]match[MX-06]]"/>&#32;belong to honesty assessment and&#32;<$count filter="{HAS_J} :filter[get[mechanisms]enlist-input[]match[MX-05]]"/>&#32;to evidence collection. Counts reflect how the inventory divides the paper into records, not how much of the design is subjective.</div>
<div class="vtw-leadsto">Leads to: <<r CN-08>></div>
</div>

<div class="vtw-step">
<h3>Seven pieces the first pass had not listed</h3>
<p>An earlier inventory (<<r SRC-MECHMAP>>) listed every place the paper needs outside evidence or a call. Checked against the records, seven had no record of their own and were added as open decisions.</p>
<div class="vtw-data"><$list filter="{NEW_VD}" join=" · "><$link><$text text={{{{!!caption}}}}/></$link></$list></div>
</div>

<div class="vtw-step">
<h3>Computable is not the same as sound</h3>
<p>Sorting pieces by what they need shows how a result would be reached. It does not show whether the result rewards the behaviour the network wants. A fully specified MFS formula under a fee-linked emissions rule computes exactly, and may still make it profitable for a party to pay its own node for real work (<<r FR-01>>, <<r FR-23>>). The reverse also holds: a mechanism that depends on judgment can work if its evidence, incentives, error costs and authority are adequate. Every mechanism therefore goes to M2, including those that need nothing more than a formula.</p>
<div class="vtw-leadsto">Leads to: <<r CN-09>></div>
</div>""")

put("M1.2", caption="What each mechanism depends on, and its critical questions",
    question="Applying the calculation, observation, inference, authority, incentive and social lenses to each mechanism in turn, where does its success depend on something not yet established?",
    starting_point="""M1.1 names the mechanisms, their chains and their open pieces, and separates reproducible operations from the inputs and decisions they rely on. This step examines each mechanism through a fixed sequence of lenses: what can be calculated, what can be observed and by whom, what those observations actually establish, who decides, what each participant is rewarded for, and how errors and disagreement affect people.

Where a mechanism's success depends on something earlier steps have not established, the step names a critical question. A critical question starts as proposed. It is not a finding that the mechanism fails; M2 assesses it under stated conditions.""",
    text="""<div class="vtw-step">
<h3>What this step will do</h3>
<p>For each mechanism, work through the lenses in order and record the result on the mechanism's page. For observation and inference, write down what information would settle each open piece, who holds it today, what it can establish as distinct from what it records, whether it could be faked, withheld or hidden, and what it costs. For authority, name who decides and whether the decider has a stake in the outcome. Current Livepeer components come in wherever they show what can be observed; the full current-system map is M1.4.</p>
<p>The claims a job can raise are already separated (<<r "View: Claims matrix">>): paid, executed, correct, available, independently wanted, worth subsidizing. A working hypothesis, tested in this step, is that the first few can be observed with the right records and the last two may not be observable by anyone.</p>
</div>

<div class="vtw-step">
<h3>Proposed critical questions so far</h3>
<p>Four are seeded from the runbook's worked examples. Each names the question, what would change the assessment, and the consequence if it resolves badly.</p>
<div class="vtw-data"><$transclude $variable="vtw-readlist" filter="[tag[GT]sort[title]]"/></div>
</div>

<div class="vtw-step">
<h3>Pieces to follow to their data</h3>
<div class="vtw-data"><$transclude $variable="vtw-readlist" filter="[tag[VD]!field:status[split]] :filter[get[classification]split[+]remove[D G S]count[]!match[0]] +[sort[title]]"/></div>
</div>

<div class="vtw-step">
<h3>What practitioner experience can add</h3>
<div class="vtw-data"><$transclude $variable="vtw-readlist" filter="[tag[HQ]field:step[M1.2]sort[title]]"/></div>
</div>""",
    issue=ISSUE + "7", issues="#7 #9", planned_artifact="deliverables/m1/claim-evidence-decision-note.md")

put("M1.3", caption="Which cases matter most",
    question="For each critical question, which cooperative, market-pressure, strategic and legitimate-lookalike cases could change a recommendation, and what would weaken each concern?",
    starting_point="""M1.2 names the critical questions and what each depends on. This step supplies and prioritizes the cases that test them. A case pairs a situation with its legitimate lookalike where one exists, names who acts and what they can see, and says what outcome would support, narrow or reject the concern.

The first concern stated on the Home page is tested here in concrete form: whether some reward decisions ask operators to find against one another on evidence that cannot reliably distinguish abuse from legitimate activity. Where M1.2 finds adequate evidence for a judgment, the concern does not apply to it, and that result carries the same weight as any other.""",
    text="""<div class="vtw-step">
<h3>What this step will do</h3>
<p>For each critical question, supply a cooperative case first, then ordinary market pressure, then selected strategic behaviour, and pair suspicious activity with its legitimate lookalike. Rank the cases by whether their outcome could change a recommendation, and state what would weaken each concern. Profit-seeking by itself is not misconduct.</p>
<p>The existing scenario pairs are the starting material (<<r "View: Scenario pairs">>).</p>
</div>

<div class="vtw-step">
<h3>Pairs to work through</h3>
<div class="vtw-data"><$list filter="[tag[SC]has[pair_with]field:sc_type[lookalike]sort[title]] [tag[SC]has[pair_with]field:sc_type[market-pressure]sort[title]]"><div><$link><$text text={{!!caption}}/></$link>&#32;beside&#32;<$list filter="[all[current]get[pair_with]]"><$link><$text text={{!!caption}}/></$link></$list></div></$list></div>
</div>

<div class="vtw-step">
<h3>What practitioner experience can add</h3>
<div class="vtw-data"><$transclude $variable="vtw-readlist" filter="[tag[HQ]field:step[M1.3]sort[title]]"/></div>
</div>""",
    issue=ISSUE + "8", issues="#8", planned_artifact="deliverables/m1/initial-threat-scenarios.md")

put("M1.4", tags="Task", caption="What exists today, and what would need to be built",
    question="For each mechanism, which current contracts, off-chain components and participant workflows can be reused, which must change, what is new, and what is unknown?",
    starting_point="""The mechanisms and their critical questions are defined in M1.1 and M1.2. This step maps them onto the current Livepeer system: versioned contracts, off-chain components such as payment tickets, the remote signer and gateways, and participant workflows. Each item is marked as reuse, modify, new, option or unknown, and linked to the mechanisms it serves.""",
    text="""<div class="vtw-step">
<h3>What this step will do</h3>
<p>Inspect the local current-system sources and record one component record per contract, off-chain component or participant role, with the deployed version inspected and the mechanisms it serves. Distinguish what the source code does from demonstrated deployed behaviour. Separate reuse, modification, new machinery, design options and unknowns.</p>
<p>Earlier on 2026-09-28 this map was folded into the data step; it is restored here as its own task, matching issue #14.</p>
</div>

<div class="vtw-step">
<h3>Components recorded so far</h3>
<div class="vtw-data"><$transclude $variable="vtw-readlist" filter="[tag[CS]sort[title]]"/> See also <<r "View: Component impact">>.</div>
</div>""",
    issue=ISSUE + "14", issues="#14", planned_artifact="deliverables/m1/current-to-litepaper-impact-map.md", review_status="Not submitted")

put("M2.1", caption="How the mechanisms behave together",
    question="When the mechanisms are assembled under explicit interpretations of the open rules, do the choices and exposures participants face produce the behaviour the paper intends?",
    starting_point="""M1 hands over the mechanisms, their critical questions, the cases that matter and what exists today. This step puts the mechanisms back together. The unit of analysis is a participant or coalition acting across mechanisms over time, not an isolated calculation.

It starts from the paper's own intended relationships, such as useful paid work leading to fee-linked reward, delegation toward productive operators and better service, and states the condition each link needs to hold. It then reconstructs what customers, operators, delegators, validators and governance would actually choose under stated rules, including validators themselves. Every mechanism is examined, including those that need nothing more than a formula.""",
    text="""<div class="vtw-step">
<h3>What this step will do</h3>
<p>For each consequential scenario: the players and what they control, the choices open to them, what each can observe or hide, the rules and their stated interpretations, the combined gains and costs without double-counting internal transfers, the timing, and the feedback into later rounds. Compare each intended relationship with the reconstructed behaviour, and say whether it is supported, conditional, contradicted or unresolved under the stated conditions.</p>
<p>A profitable deviation under fixed assumptions is not automatically an equilibrium, a dominant strategy or evidence of prevalence. Stronger terms need analysis that supports them.</p>
</div>

<div class="vtw-step">
<h3>The paper's own reasons, to reconstruct first</h3>
<div class="vtw-data"><$transclude $variable="vtw-readlist" filter="FR-19 FR-20 FR-21 FR-22 FR-23 FR-01"/></div>
</div>

<div class="vtw-step">
<h3>What practitioner experience can add</h3>
<div class="vtw-data"><$transclude $variable="vtw-readlist" filter="[tag[HQ]field:step[M2.1]sort[title]]"/></div>
</div>""",
    issue=ISSUE + "10", issues="#10", planned_artifact="deliverables/m2/litepaper-incentive-examples.md")

m22_register = cur("M2.2")
put("M2.3", tags="Task", stage="M2", caption="What would resolve each concern?",
    question=m22_register["question"], starting_point=m22_register["starting_point"], text=m22_register["text"],
    issue=ISSUE + "15", issues="#15", planned_artifact="deliverables/m2/findings-and-requirements.md", review_status="Not submitted")
put("M2.2", caption="Testing the critical questions",
    question="Under stated conditions, what do bounded economic examples and focused evidence inquiries show about each consequential interaction and critical question?",
    starting_point="""M2.1 identifies the interactions that could change a recommendation. This step tests them with small, reproducible examples and focused evidence inquiries, examining individual decisions, information limits, social and operational costs, and system feedback together. A small example that answers its question is enough.""",
    text="""<div class="vtw-step">
<h3>What this step will do</h3>
<p>Run bounded economic examples and evidence inquiries for the critical questions M2.1 ranks as consequential, with explicit interpretations and variants only where they could change the result. Record counterevidence and limits beside each result.</p>
<p>Until later on 2026-09-28 this identifier held the register of what would resolve each concern. That register is now <<r M2.3>>; see <<r "View: Path history">>.</p>
</div>

<div class="vtw-step">
<h3>Critical questions to test</h3>
<div class="vtw-data"><$transclude $variable="vtw-readlist" filter="[tag[GT]sort[title]]"/></div>
</div>

<div class="vtw-step">
<h3>Existing models</h3>
<div class="vtw-data"><$transclude $variable="vtw-readlist" filter="[tag[EX]sort[title]]"/></div>
</div>""",
    issues="#10 #9", issue=ISSUE + "9", planned_artifact="deliverables/m2/focused-evidence-assessment.md")

for hq, step in (("HQ-04", "M1.2"), ("HQ-08", "M1.2"), ("HQ-06", "M2.2")):
    put(hq, step=step)

# ------------------------------------------------------------------ 9. pages

put("View: Path history", tags="View", caption="Path history", description="How step identifiers were used over time, and where each now points",
    text="""<p class="vtw-lede">Step identifiers are stable references in record provenance. Their meaning changed twice on 2026-09-28. Records keep the identifier that was current when they were created; this page says what it meant then.</p>
<table class="vtw-grid vtw-history"><tbody>
<tr><th>Identifier</th><th>Seed (first build)</th><th>Interim path (restructure and review revision)</th><th>Current, per the runbook</th><th>GitHub issue</th></tr>
<tr><td>M1.1</td><td>Understand what the litepaper does (baseline map)</td><td>What can the protocol compute on its own? The baseline walk-through moved to the Orientation page.</td><td>How the architecture works, mechanism by mechanism. The baseline walk-through is again recorded here; the Orientation page is context.</td><td>#6</td></tr>
<tr><td>M1.2</td><td>What reward eligibility needs to establish</td><td>Where would the data come from? (absorbed the current-system map)</td><td>What each mechanism depends on, and its critical questions</td><td>#7, #9</td></tr>
<tr><td>M1.3</td><td>Adversarial scenarios and lookalikes</td><td>Who is asked to judge what?</td><td>Which cases matter most</td><td>#8</td></tr>
<tr><td>M1.4</td><td>Current system to litepaper map</td><td>Retired; folded into M1.2</td><td>What exists today, and what would need to be built</td><td>#14</td></tr>
<tr><td>M2 / M2.1</td><td>M2 as a single stage</td><td>M2.1: would people behave as the paper hopes?</td><td>How the mechanisms behave together</td><td>#10</td></tr>
<tr><td>M2.2</td><td>—</td><td>Register of what would resolve each concern</td><td>Testing the critical questions; the register moved to M2.3</td><td>#10, #9</td></tr>
<tr><td>M2.3</td><td>—</td><td>—</td><td>What would resolve each concern?</td><td>#15</td></tr>
</tbody></table>
<p>Records introduced during the interim path with ''introduced by'' M1.1 (the seven decisions from the earlier inventory, conclusions CN-07 to CN-09 and the questions for humans) were created by the interim "what can the protocol compute" step, whose work now sits across M1.1 and M1.2. Records restored from the interim label "Orientation" to M1.1 were created by the seed baseline map.</p>
<p>GitHub issue titles are unchanged. The mapping above is a local crosswalk until reporting records are reconciled with authorization.</p>""")

replace_in("View: Mechanism stories", "text", [(cur("View: Mechanism stories")["text"], """<p class="vtw-lede">Each mechanism is told end to end on its own page: what the paper specifies, how it works from purpose to output, what it depends on, what it leaves to be built, its critical questions, the working hypothesis and where it goes next. Agents draft the pages from the records; people edit them. Corrections can be made directly or left as a note.</p>
<<vtw-mxmap>>
<h3>Stories drafted</h3>
<$transclude $variable="vtw-readlist" filter="[tag[MX]has[story_status]sort[title]]"/>
<h3>Not drafted yet</h3>
<$transclude $variable="vtw-readlist" filter="[tag[MX]!has[story_status]sort[title]]"/>""")])
put("View: Mechanism stories", caption="Mechanisms", description="The mechanism map, and each mechanism told end to end")

replace_in("Home", "text", [
    ("<li>''Read a mechanism story.''&#32;Each one follows a single mechanism from purpose to open questions:&#32;<$link to=\"View: Mechanism stories\">Mechanism stories</$link>. Corrections are welcome.</li>",
     "<li>''Read a mechanism.''&#32;Each page follows one part of the system from its purpose to its open and critical questions:&#32;<$link to=\"View: Mechanism stories\">Mechanisms</$link>. Corrections are welcome.</li>"),
    ("(<$link to=\"M2.2\">register</$link>)", "(<$link to=\"M2.3\">register</$link>)"),
    ("<p><$link to=\"Conventions\">Conventions</$link>&#32;·&#32;<$link to=\"About this wiki\">About this wiki</$link>",
     "<p>''Agents: read the runbook before contributing''&#32;(<code>" + RUNBOOK + "</code>).</p>\n<p><$link to=\"Conventions\">Conventions</$link>&#32;·&#32;<$link to=\"About this wiki\">About this wiki</$link>&#32;·&#32;<$link to=\"View: Path history\">Path history</$link>&#32;·&#32;<$link to=\"Orientation\">Orientation</$link>"),
])
replace_in("View: Questions for humans", "text", [("<$link to=\"M2.2\">register</$link>", "<$link to=\"M2.3\">register</$link>")])

replace_in("$:/vtw/ui/SideBarViews", "text", [
    ('<div><$link to="View: Mechanism stories">Mechanism stories</$link></div>', '<div><$link to="View: Mechanism stories">Mechanisms</$link></div>'),
    ('filter="CN LP RL VD CL FR SC EX CS HQ"', 'filter="MX GT CN LP RL VD CL FR SC EX CS HQ"'),
])
replace_in("$:/vtw/ui/JourneyBottom", "text", [('filter="CN LP RL VD CL FR SC EX FX CS HQ"', 'filter="MX GT CN LP RL VD CL FR SC EX FX CS HQ"')])
replace_in("$:/vtw/ui/RecordRollup", "text", [
    ('filter="CN RL VD CL SC FR EX FX CS HQ"', 'filter="MX GT CN RL VD CL SC FR EX FX CS HQ"'),
    ('<$transclude $variable="vtw-section" label="Conclusions" filter="[tag[CN]contains:concepts<id>sort[title]]"/>',
     '<$transclude $variable="vtw-section" label="Mechanisms that serve this concept" filter="[tag[MX]contains:concepts<id>sort[title]]"/>\n<$transclude $variable="vtw-section" label="Conclusions" filter="[tag[CN]contains:concepts<id>sort[title]]"/>'),
    ("[<id>get[experiments]enlist-input[]] [<id>get[related]enlist-input[]]\"/>",
     "[<id>get[experiments]enlist-input[]] [<id>get[mechanisms]enlist-input[]] [<id>get[depends_on]enlist-input[]] [<id>get[related]enlist-input[]]\"/>"),
    ("search:provisions,conflicting_provisions,decisions,claims,findings,scenarios,pair_with,experiments,components,related:regexp<rx>",
     "search:provisions,conflicting_provisions,decisions,claims,findings,scenarios,pair_with,experiments,components,mechanisms,depends_on,related:regexp<rx>"),
])

conv = cur("Conventions")["text"]
a = conv.index("<h2>How the path is organized</h2>")
b = conv.index("<ul>", a)
conv = conv[:a] + f"""<h2>Governing document</h2>
<p>The agent runbook governs research method, stage boundaries and the editing workflow: <code>{RUNBOOK}</code>. Agents read it before contributing. This page defines the record system; where the two differ on method, the runbook wins.</p>

<h2>How the path is organized</h2>
<p>Mechanisms are the organizing unit. The path makes successive passes over the same mechanisms: M1.1 names them and their chains; M1.2 applies the calculation, observation, inference, authority, incentive and social lenses and names critical questions; M1.3 frames the cases that matter; M1.4 maps what exists today; M2.1 reassembles the mechanisms into one system; M2.2 tests the critical questions; M2.3 records what would resolve each concern. Each step is written as prose for people, with records as its evidence, and ends in conclusions the next step starts from. Identifier history is on <$link to="View: Path history">Path history</$link>.</p>
""" + conv[b:]
conv = conv.replace("<li>''One mechanism, one story.'' Each mechanism's page carries a chain from purpose to output (''requires'') and a story that follows it through every step. Agents keep them in step with the records; people edit them.</li>",
    "<li>''One mechanism, one story.'' Each mechanism (MX) carries a chain from purpose to output (''requires'') and a story that follows it through every step. Concepts (LP) link to the mechanisms that serve them. Agents keep stories in step with the records; people edit them.</li>\n<li>''Critical questions.'' A GT record is a proposed critical question: the question, what would change the assessment, and the consequence if it resolves badly. The optional fields hold the fuller analysis once M2 promotes it. In workbench text, say \"proposed\", not the word the scope check reserves.</li>\n<li>''Provenance.'' Mechanisms, chain items and critical questions state whether they are explicit in the paper, required to implement stated behaviour, analytical decomposition, a modelling assumption or a possible design option. An option is never presented as a requirement.</li>")
if "Critical questions.''" not in conv:
    sys.exit("Conventions: story bullet not found")
put("Conventions", text=conv)

about = cur("About this wiki")["text"]
if "agent-runbook" not in about:
    about += f"\n* Governing document for agents: `{RUNBOOK}`. Read it before contributing.\n* Backup before the 2026-09-28 mechanism migration: `/home/mav/repos/livepeer/validator-track-workbench-tools/backups/validator-track-workbench.20260928-before-mechanism-migration.html`."
put("About this wiki", text=about)

dash = cur("View: Milestone dashboard")["text"]
dash = dash.replace("The workbench path was restructured on 2026-09-28; GitHub issue titles still use the earlier task names until they are revisited.",
                    "The workbench path follows the agent runbook; GitHub issue titles still use the earlier task names. Identifier history is on Path history.")
put("View: Milestone dashboard", text=dash)

json.dump(list(OUT.values()), sys.stdout, indent=1, ensure_ascii=False)
print(f"{len(OUT)} tiddlers", file=sys.stderr)
