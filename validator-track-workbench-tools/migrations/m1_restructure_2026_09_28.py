"""Restructure the workbench around five questions (2026-09-28).

Shane's reasoning chain becomes the spine: how the paper works (Orientation),
then M1.1 what can be computed, M1.2 where the data would come from, M1.3 who
is asked to judge what, M2.1 whether people would behave as hoped once rules
are written, M2.2 which problems a rule fixes and which it does not.

Adds: fix_by_rule on decisions, seven decisions from the 19 Sep mechanism map,
three M1.1 conclusions, mechanism stories (LP text), questions for humans (HQ),
contributor notes, plain-language labels. Renames the old M1.1 to Orientation
and folds the old M1.4 into M1.2. The pre-restructure file is kept as
validator-track-workbench-v1-2026-09-28.html.

Usage: python3 m1_restructure_2026_09_28.py WIKI > restructure.json
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

VTW = Path(__file__).resolve().parents[1] / "vtw.py"
MECHMAP = Path("/home/mav/repos/livepeer/litepaper-validator-mechanism-map.md")
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


def dict_set(title, entries):
    lines = wiki[title]["text"].splitlines()
    out, seen = [], set()
    for line in lines:
        k = line.split(":", 1)[0].strip() if ":" in line else None
        if k in entries:
            out.append(f"{k}: {entries[k]}")
            seen.add(k)
        else:
            out.append(line)
    out += [f"{k}: {v}" for k, v in entries.items() if k not in seen]
    put(title, text="\n".join(out))


ISSUE = "https://github.com/moatus/livepeer-validator-track/issues/"

# ------------------------------------------------------------------ 1. remap step numbers on existing records

STEP_MAP = {"M1.1": "Orientation"}
OWNER_MAP = {"M1.4": "M1.2", "M2": "M2.1"}
CARRIED = {
    "CN-01": "M1.3 M2.1",
    "CN-02": "M1.1 M2.1",
    "CN-03": "M1.1 M1.3",
    "CN-04": "M1.2",
    "CN-05": "M1.3 M2.1",
    "CN-06": "M1.1 M2.1",
}

for title, t in wiki.items():
    if title.startswith("$:/") or not t.get("record_type"):
        continue
    changes = {}
    for f in ("introduced_by", "last_changed_by", "task"):
        if t.get(f) in STEP_MAP:
            changes[f] = STEP_MAP[t[f]]
    if t.get("owner_milestone"):
        seen = []
        for v in t["owner_milestone"].split():
            v = OWNER_MAP.get(v, v)
            if v not in seen:
                seen.append(v)
        changes["owner_milestone"] = " ".join(seen)
    for f in ("follow_up", "design_question", "statement"):
        if t.get(f):
            v = t[f].replace("M1.4", "M1.2")
            v = re.sub(r"\bM2\b(?!\.)", "M2.1", v)
            if v != t[f]:
                changes[f] = v
    if title in CARRIED:
        changes["carried_to"] = CARRIED[title]
    if changes:
        put(title, **changes)

# LP-04 overview mentions "carried into M2"
if "LP-04" in wiki and "into M2." in wiki["LP-04"].get("overview", ""):
    put("LP-04", overview=wiki["LP-04"]["overview"].replace("carried into M2.", "carried into M1.2 and M2.1."))

# ------------------------------------------------------------------ 2. the path and its steps

put("$:/vtw/path", list="Orientation M1.1 M1.2 M1.3 M2.1 M2.2",
    text="The research path, in order. Each step starts from the conclusions carried into it.")

put("M1", caption="What the litepaper needs to exist",
    text="How the paper works, then three questions: what can be computed, where the data would come from, and who is asked to judge what. "
         "Missing detail is treated as something to build, never as a fault in the paper.")
put("M2", caption="Would it work once built?",
    question="If every missing rule were written, would people behave the way the paper hopes, and which problems would remain under any reasonable rule?",
    text="Two questions: how participants would behave under the written rules, and which problems a rule fixes and which it does not.")

old = wiki["M1.1"]
put("Orientation", tags="Task", stage="M1", caption="How the paper works",
    question="What is the litepaper trying to achieve, and how would money and rewards move if everyone cooperated?",
    starting_point=old["starting_point"],
    text=old["text"],
    issue=ISSUE + "6", issues="#6",
    planned_artifact=old.get("planned_artifact", ""),
    review_status=old.get("review_status", "Not submitted"))

M11_START = """The orientation gave us a clear picture of how the paper wants money and rewards to move, and a long list of rules it has not written yet. That list is not a criticism. A litepaper sets out an architecture; the rules come later. So this step does not ask what the paper forgot. It asks what ''kind'' of thing each missing piece is.

The kind matters because it decides how a disagreement would be settled. If a piece is arithmetic, anyone can check the answer. If it needs someone to look at the world, the answer is only as good as what they can see. If it needs someone to make a call, the answer can be argued with."""

ONLY_DG = "[tag[VD]!field:status[split]] :filter[get[classification]split[+]remove[D G]count[]match[0]]"
HAS_E = "[tag[VD]!field:status[split]] :filter[get[classification]split[+]match[E]]"
HAS_J = "[tag[VD]!field:status[split]] :filter[get[classification]split[+]match[J]]"
HAS_J_LP07 = "[tag[VD]!field:status[split]contains:concepts[LP-07]] :filter[get[classification]split[+]match[J]]"
ALL_VD = "[tag[VD]!field:status[split]]"
MECHS = "LP-03 LP-04 LP-05 LP-06 LP-07 LP-08 LP-09 LP-10 LP-11 LP-12 LP-13 LP-14"
NEW_VD = "VD-23 VD-24 VD-25 VD-26 VD-27 VD-28 VD-29"

M11_TEXT = f"""<div class="vtw-step">
<h3>Four kinds of missing piece</h3>
<p>Every open piece in the paper needs one or more of these:</p>
<ul>
<li>''A formula.'' Arithmetic over numbers the protocol already holds: stake balances, settled fees, round counters.</li>
<li>''Data from outside the protocol.'' Someone has to observe something the chain cannot see, such as whether a job was delivered.</li>
<li>''A judgment.'' Someone has to interpret incomplete evidence or intent, such as whether a payment was self-dealing.</li>
<li>''A policy choice.'' Governance picks a rule once. After that, the rule can usually be computed.</li>
</ul>
<p>AI media work adds one more consideration: many outputs legitimately vary between runs, so "correct" has to allow for that.</p>
<p>One piece can need several of these. The median of validator scores is a formula, but every score it takes in is a judgment.</p>
</div>

<div class="vtw-step">
<h3>Most of the money arithmetic can be written down</h3>
<p>The fee split, the burn, the emission shares, the MFS minimum, the median and the delay counters are all arithmetic (<<r RL-10>>, <<r RL-24>>, <<r RL-35>>, <<r RL-53>>). What they wait on is policy: measurement windows, what happens to reward that MFS leaves unassigned, when a round becomes final. None of that needs anyone to look at the world.</p>
<div class="vtw-data"><$count filter="{ONLY_DG}"/>&#32;of the&#32;<$count filter="{ALL_VD}"/>&#32;open pieces need nothing more than a formula and a policy choice:&#32;<$list filter="{ONLY_DG} +[sort[title]]" join=", "><$link><$text text={{{{!!caption}}}}/></$link></$list>.</div>
<div class="vtw-leadsto">Leads to: <<r CN-07>></div>
</div>

<div class="vtw-step">
<h3>The rest needs someone to look, or someone to decide</h3>
<p>The other pieces cannot be settled by arithmetic, however carefully it is written. Someone has to observe what happened, or interpret what it meant.</p>
<div class="vtw-data"><$count filter="{HAS_E}"/>&#32;open pieces need data from outside the protocol.&#32;<$count filter="{HAS_J}"/>&#32;need a judgment. The judgments:&#32;<$list filter="{HAS_J} +[sort[title]]" join=", "><$link><$text text={{{{!!caption}}}}/></$link></$list>.</div>
</div>

<div class="vtw-step">
<h3>The judgments gather around one mechanism</h3>
<p>Almost every piece that needs a judgment feeds the honesty score (<<r LP-07>>): what counts as dishonest, what evidence is enough, who scores whom, and when a score is final. The paper says so plainly. Being a validator is how a node protects its interests "in a network where reward eligibility is inherently subjective" (litepaper line 83).</p>
<p>These are also the adversarial pieces. Each one asks an operator to call out another operator, often a competitor.</p>
<div class="vtw-data"><$count filter="{HAS_J_LP07}"/>&#32;of the&#32;<$count filter="{HAS_J}"/>&#32;pieces that need a judgment concern the honesty score.</div>
<div class="vtw-leadsto">Leads to: <<r CN-08>></div>
</div>

<div class="vtw-step">
<h3>Seven pieces the first pass had not listed</h3>
<p>An earlier inventory (<<r SRC-MECHMAP>>) listed every place the paper needs outside evidence or a call. Checked against the records, seven had no record of their own. They are added here as open decisions. Each one is a judgment or evidence question, and six of the seven concern the honesty score.</p>
<div class="vtw-data"><$list filter="{NEW_VD}" join=" · "><$link><$text text={{{{!!caption}}}}/></$link></$list></div>
</div>

<div class="vtw-step">
<h3>Mechanism by mechanism</h3>
<p>Open a mechanism to see what it still needs, and whether a written rule would settle each piece. That last column is an agent's first proposal. "Needs a human call" means the agent could not tell, and a person should decide (<<r "View: Questions for humans">>). The full story of each mechanism is on its own page (<<r "View: Mechanism stories">>).</p>
<$list filter="{MECHS}" variable="lp">
<details class="vtw-details vtw-mech"><summary><$text text={{{{{{ [<lp>get[caption]] }}}}}}/>&#32;·&#32;<$count filter="[tag[VD]!field:status[split]contains:concepts<lp>]"/>&#32;open&#32;·&#32;<$count filter="[tag[VD]!field:status[split]contains:concepts<lp>field:fix_by_rule[yes]]"/>&#32;settled by a rule&#32;·&#32;<$count filter="[tag[VD]!field:status[split]contains:concepts<lp>field:fix_by_rule[unsure]]"/>&#32;for a human call</summary>
<$transclude $variable="vtw-buildlist" lp=<<lp>>/>
</details>
</$list>
<div class="vtw-leadsto">Leads to: <<r CN-09>></div>
</div>"""

put("M1.1", tags="Task", stage="M1", caption="What can the protocol compute on its own?",
    question="For each mechanism in the paper, which parts could a contract work out from numbers it already holds, and which need something from outside: data, a judgment or a policy choice?",
    starting_point=M11_START, text=M11_TEXT,
    issue=ISSUE + "6", issues="#6",
    planned_artifact="deliverables/m1/determinism-map.md (proposed)", review_status="Not submitted")

E_OR_J = "[tag[VD]!field:status[split]] :filter[get[classification]split[+]remove[D G S]count[]!match[0]] +[sort[title]]"

put("M1.2", tags="Task", stage="M1", caption="Where would the data come from?",
    question="For each piece that needs outside data or a judgment, what information would settle it, who holds that information today, and could it be faked or hidden?",
    starting_point="""M1.1 sorted the missing pieces. Arithmetic and policy choices can be written down. The rest need someone to observe the world or make a call, and most of those calls are about the honesty score.

This step follows those pieces to their data. The question is not whether the paper specified a data source. It is whether the information exists anywhere, who could see it, and whether the person being judged could shape it.""",
    text=f"""<div class="vtw-step">
<h3>What this step will do</h3>
<p>For each piece below, write down in plain words: what information would settle it; who holds that information today; whether it could be faked, withheld or hidden; and what it would cost to collect. Current Livepeer components come in here: payment tickets, the remote signer, gateways and orchestrator logs. This step also carries the current-system map that was a separate task before.</p>
<p>The claims a job can raise are already separated (<<r "View: Claims matrix">>): paid, executed, correct, available, independently wanted, worth subsidizing. They are the spine of this step. An early reading, still to be tested, is that the first few can be observed with the right records and the last two may not be observable by anyone.</p>
</div>

<div class="vtw-step">
<h3>Pieces to follow to their data</h3>
<div class="vtw-data"><$transclude $variable="vtw-readlist" filter="{E_OR_J}"/></div>
</div>

<div class="vtw-step">
<h3>What only practitioners can tell us</h3>
<div class="vtw-data"><$transclude $variable="vtw-readlist" filter="[tag[HQ]field:step[M1.2]sort[title]]"/></div>
</div>""",
    issue=ISSUE + "7", issues="#7 #14 #9",
    planned_artifact="deliverables/m1/data-map.md (proposed)", review_status="Not submitted")

put("M1.3", tags="Task", stage="M1", caption="Who is asked to judge what?",
    question="For each judgment the paper relies on, who is asked to make it, about whom, holding what evidence, and what happens to them if they get it wrong either way?",
    starting_point="""M1.2 establishes which facts can be observed and which cannot. This step puts people back into the picture. A judgment made on good evidence by someone with no stake in the outcome is one thing. A judgment made on thin evidence, about a competitor, by someone whose own rewards depend on the same scores, is another.

This is where the first reading's worry gets tested: that the honesty score becomes a kind of court without a record, where operators judge each other on evidence neither side can show. If the data map finds good evidence for a judgment, the worry does not apply to it, and that result counts as much as any other.""",
    text="""<div class="vtw-step">
<h3>What this step will do</h3>
<p>For each judgment, name the judge, the judged, the evidence available to the judge, and the cost to each side of a wrong call in either direction: an honest operator scored down, or self-dealing let through. Note where the judge and the judged are competitors, and where a judge can be judged in return.</p>
<p>The scenario pairs are the test cases (<<r "View: Scenario pairs">>). Each pairs a legitimate case with an adversarial one that looks similar on the data. Where the pair can be told apart, say how. Where it cannot, say what the judge is left to go on.</p>
</div>

<div class="vtw-step">
<h3>Pairs to work through</h3>
<div class="vtw-data"><$list filter="[tag[SC]has[pair_with]field:sc_type[lookalike]sort[title]] [tag[SC]has[pair_with]field:sc_type[market-pressure]sort[title]]"><div><$link><$text text={{!!caption}}/></$link>&#32;beside&#32;<$list filter="[all[current]get[pair_with]]"><$link><$text text={{!!caption}}/></$link></$list></div></$list></div>
</div>

<div class="vtw-step">
<h3>What only practitioners can tell us</h3>
<div class="vtw-data"><$transclude $variable="vtw-readlist" filter="[tag[HQ]field:step[M1.3]sort[title]]"/></div>
</div>""",
    issue=ISSUE + "8", issues="#8",
    planned_artifact="deliverables/m1/judgment-map.md (proposed)", review_status="Not submitted")

put("M2.1", tags="Task", stage="M2", caption="Would people behave as the paper hopes?",
    question="If every missing rule were written under a stated reading, what would each participant rationally do, and does that match what the paper intends?",
    starting_point="""M1 hands over three things: what can be computed, what information exists, and which judgments are asked of whom. This step assumes the missing rules have been written, under a stated reading, and asks how people would actually behave.

That includes validators. The paper treats scoring as a duty that validators will carry out honestly. Here we ask what a validator gains or loses from scoring carefully, scoring everyone 1.0, or coordinating with others, and likewise for operators, delegators and anyone paying for jobs.""",
    text="""<div class="vtw-step">
<h3>What this step will do</h3>
<p>For each mechanism: who the players are, what moves they have, and what the mechanism pays them for each move. Write it in prose first; add a small worked example only where a number settles the question (<<r EX-01>>). Start with everyone cooperating, then ordinary market pressure, then deliberate exploitation. Stop when an example answers its question.</p>
</div>

<div class="vtw-step">
<h3>The paper's own reasons, to test first</h3>
<p>The paper explains why its defenses should work. These are the claims to check before anything else.</p>
<div class="vtw-data"><$transclude $variable="vtw-readlist" filter="FR-19 FR-20 FR-21 FR-22 FR-23 FR-01"/></div>
</div>

<div class="vtw-step">
<h3>What only practitioners can tell us</h3>
<div class="vtw-data"><$transclude $variable="vtw-readlist" filter="[tag[HQ]field:step[M2.1]sort[title]]"/></div>
</div>""",
    issue=ISSUE + "10", issues="#10",
    planned_artifact="deliverables/m2/incentive-analysis.md (proposed)", review_status="Not submitted")

put("M2.2", tags="Task", stage="M2", caption="Which problems would a rule fix?",
    question="For each open piece and each finding, would a written rule close it, or would the problem remain under any reasonable rule?",
    starting_point="""Every gap ends up in one of two places. If writing a rule would close it, it goes on the list of things to build, and it says nothing against the paper. If it would remain under any reasonable rule, it is a reason to consider changing the design, and it is carried forward with its evidence.

This page is the running register. Agents propose; people decide. Anything marked "needs a human call" is waiting for someone who knows the network to settle it.""",
    text=f"""<div class="vtw-step">
<h3>A written rule would settle these</h3>
<div class="vtw-data"><$transclude $variable="vtw-buildtable" filter="[tag[VD]field:fix_by_rule[yes]sort[title]] [tag[FR]field:fix_by_rule[yes]sort[title]]"/></div>
</div>

<div class="vtw-step">
<h3>Needs a human call</h3>
<div class="vtw-data"><$transclude $variable="vtw-buildtable" filter="[tag[VD]field:fix_by_rule[unsure]sort[title]] [tag[FR]field:fix_by_rule[unsure]sort[title]]"/></div>
</div>

<div class="vtw-step">
<h3>Would remain under any reasonable rule</h3>
<p>Only a person moves a piece here, with a one-line reason.</p>
<div class="vtw-data"><$transclude $variable="vtw-buildtable" filter="[tag[VD]field:fix_by_rule[no]sort[title]] [tag[FR]field:fix_by_rule[no]sort[title]]"/></div>
</div>""",
    issue=ISSUE + "15", issues="#15",
    planned_artifact="deliverables/m2/rule-or-redesign-register.md (proposed)", review_status="Not submitted")

put("M1.4", tags="[[Retired step]]",
    text="Folded into [[M1.2]] on 2026-09-28: the current-system map is now part of following each piece to its data. GitHub issue #14 is unchanged until its title is revisited.")

# ------------------------------------------------------------------ 3. fix_by_rule proposals on decisions

FIX = {
    "VD-01": ("yes", "A registry specification settles it."),
    "VD-02": ("unsure", "A discovery specification can be written; whether new listings actually receive traffic is market behaviour."),
    "VD-03": ("yes", "Settlement and attribution rules settle it. They do not show who funded the payment (see VD-19)."),
    "VD-04": ("unsure", "Receipts may suffice for some workloads; third-party API and private jobs may leave nothing a validator can check."),
    "VD-05": ("yes", "Windows, snapshots and denominators are a specification choice."),
    "VD-06": ("yes", "Choosing one formula settles it. Which formula is chosen changes incentives; that is for M2.1."),
    "VD-07": ("yes", "The procedure can be written. The scores it aggregates remain judgments."),
    "VD-08": ("yes", "Ranking, ties and vacancies are an election specification."),
    "VD-09": ("unsure", "Criteria can be written. Whether evidence exists to meet them, especially for self-dealing, is the open question."),
    "VD-10": ("unsure", "Quorum and abstention mechanics can be written; conflicts and hidden common control may not be settled by a rule."),
    "VD-11": ("yes", "A claim deadline and per-round finality can be written."),
    "VD-12": ("yes", "A budget rule settles it. Each option changes incentives differently; that is for M2.1."),
    "VD-13": ("yes", "A governance choice between the stated options."),
    "VD-14": ("unsure", "The schedule is a policy choice; an LPT price source that resists manipulation is an open engineering problem."),
    "VD-15": ("yes", "A parameter. Whether operators can live with it is an economic question for M2.1."),
    "VD-16": ("yes", "One denominator settles it."),
    "VD-17": ("yes", "A compensation rule settles it."),
    "VD-18": ("unsure", "Execution parameters can be written; market manipulation and slippage are not settled by writing them."),
    "VD-19": ("unsure", "Central question: whether any rule could supply evidence of independent demand or subsidy value."),
    "VD-21": ("yes", "A constitution can separate policy changes from case decisions."),
    "VD-22": ("unsure", "Task criteria can be written for deterministic jobs; outputs that vary by nature may resist them."),
    "VD-23": ("unsure", "Attributing a failure to intent rather than circumstance needs judgment unless consequences ignore intent."),
    "VD-24": ("unsure", "Either every agreed price counts, or someone needs a benchmark; both are choices with consequences."),
    "VD-25": ("yes", "Sampling and trigger rules can be written. Whether they catch adaptive behaviour is for M2.1."),
    "VD-26": ("unsure", "Provenance rules can be written; whether an authenticated claim is true is a separate matter."),
    "VD-27": ("unsure", "An address can be locked; a person with fresh capital and a new address cannot be identified by rule."),
    "VD-28": ("yes", "A funding and oversight arrangement is a governance choice."),
    "VD-29": ("unsure", "Disclosure and recusal can be required; hidden common control cannot be ruled out by rule."),
}

for vd in ("VD-%02d" % i for i in range(1, 23)):
    if vd in FIX:
        put(vd, fix_by_rule=FIX[vd][0], fix_by_rule_by="agent", fix_note=FIX[vd][1])

# ------------------------------------------------------------------ 4. source and seven new decisions

mm_sha = hashlib.sha256(MECHMAP.read_bytes()).hexdigest()
put("SRC-MECHMAP", tags="Source", record_kind="source",
    caption="Rules and judgment gates, 19 September working note",
    local_path=str(MECHMAP), sha256=mm_sha,
    text="Local exploratory analysis of the litepaper; not accepted and not public. Its inventory of evidence and judgment gates is used as a checklist in M1.1. Its suggested replacement mechanisms are not imported into these records.")

NEW = {
    "VD-23": dict(caption="Dishonesty or ordinary limitation",
        question="When a node fails or underperforms, was that dishonesty or an ordinary operational limitation?",
        classification="E+J",
        paper_says="Validators should not penalize legitimate performance limits such as regional coverage or model availability; the score targets dishonesty.",
        evidence_needed="Records of what was promised against what was delivered, and a rule for attributing failures to the node, the network or an upstream provider.",
        residual_uncertainty="Intent, fault attribution across upstream providers and reasonable excuses need judgment if they affect the score.",
        authority="Active validators under future criteria",
        consequence="Calling an outage dishonest penalizes honest work; the reverse lets deliberate non-delivery through.",
        concepts="LP-07", provisions="RL-25", claims="CL-02 CL-04", participants="operator validator",
        owner_milestone="M1.2 M1.3", source_ref="SRC-LP20 L86; SRC-MECHMAP gate 07", migrated_from="litepaper-validator-mechanism-map.md gate 07"),
    "VD-24": dict(caption="Inflated prices",
        question="Can a price or fee be too high to count toward rewards, and who decides?",
        classification="E+J+G",
        paper_says="Operators set their own USD prices; fee fabrication is named as dishonesty; nothing defines an inflated price.",
        evidence_needed="Either a rule that every agreed, settled price counts, or a benchmark and a policy for fees above it.",
        residual_uncertainty="A real payment at an agreed price can still be chosen to maximize reward; a fair-price test needs a benchmark or discretion.",
        authority="Governance sets policy; validators apply it",
        consequence="Decides whether high self-set prices raise a node's fee share.",
        concepts="LP-04 LP-07 LP-10", provisions="RL-10 RL-25 RL-32", claims="CL-09", participants="operator validator governance",
        owner_milestone="M1.2 M1.3", source_ref="SRC-LP20 L53, L86, L113; SRC-MECHMAP gate 08", migrated_from="litepaper-validator-mechanism-map.md gate 08"),
    "VD-25": dict(caption="Who gets investigated",
        question="How are nodes or rounds chosen for investigation?",
        classification="D+E+G",
        paper_says="Validators are to notice anomalies within the seven-round window; testing, monitoring and anomaly detection are to be funded as a public good.",
        evidence_needed="Sampling and trigger rules, coverage targets and reporting requirements.",
        residual_uncertainty="Reproducible triggers can still miss adaptive behaviour; coverage depends on funded monitoring.",
        authority="Governance sets procedure; tooling teams and validators apply it",
        consequence="Decides which behaviour is ever looked at before rewards are claimed.",
        concepts="LP-07 LP-09", provisions="RL-26 RL-30", participants="validator governance",
        owner_milestone="M1.2", source_ref="SRC-LP20 L88, L109; SRC-MECHMAP gate 09", migrated_from="litepaper-validator-mechanism-map.md gate 09"),
    "VD-26": dict(caption="Credible and available evidence",
        question="Which evidence is credible enough to act on, and will it be available when needed?",
        classification="E+J",
        paper_says="Validators vote on published evidence or other surfaced criteria.",
        evidence_needed="Requirements for signatures, provenance, timestamps, retention and reproducible checks, and rules for private jobs.",
        residual_uncertainty="Authenticating who made a claim is separate from whether it is true; private jobs and shared monitoring sources keep trust dependencies.",
        authority="Governance sets admissibility; validators weigh evidence",
        consequence="Decides what a score can rest on and what an accused operator can answer.",
        concepts="LP-07", provisions="RL-26", claims="CL-07", participants="validator operator customer",
        owner_milestone="M1.2", source_ref="SRC-LP20 L88; SRC-MECHMAP gate 10", migrated_from="litepaper-validator-mechanism-map.md gate 10"),
    "VD-27": dict(caption="Returning under a new identity",
        question="Can a penalized operator return under a new address?",
        classification="D+E+J",
        paper_says="The 21-round lockup is meant to stop malicious nodes quickly unbonding and registering again under different identities; registration is open with no bond.",
        evidence_needed="Rules that keep old stake and pending claims under their original rounds; any identity or ownership evidence.",
        residual_uncertainty="Locking an address does not stop a person; fresh capital under a new address is unaffected.",
        authority="Staking contract enforces locks; validators judge links between identities",
        consequence="Decides whether a penalty follows the actor or only the address.",
        concepts="LP-08 LP-03", provisions="RL-07 RL-27", participants="operator delegator validator",
        owner_milestone="M1.2 M2.1", source_ref="SRC-LP20 L53, L99; SRC-MECHMAP gate 16", migrated_from="litepaper-validator-mechanism-map.md gate 16"),
    "VD-28": dict(caption="Who funds and oversees evidence tooling",
        question="Who funds, builds and oversees the shared testing and monitoring validators rely on?",
        classification="G+J",
        paper_says="The hard work behind judgments should be funded as a public good, done by small groups of applied research engineers.",
        evidence_needed="A funding and oversight arrangement with published deliverables, access rules and evidence formats.",
        residual_uncertainty="Many validators relying on one investigation source are not independent fact-finders.",
        authority="Governance and treasury",
        consequence="Decides whose evidence validators see and how independent their judgments can be.",
        concepts="LP-07 LP-14", provisions="RL-26", participants="validator governance",
        owner_milestone="M1.3", source_ref="SRC-LP20 L88; SRC-MECHMAP gate 20", migrated_from="litepaper-validator-mechanism-map.md gate 20"),
    "VD-29": dict(caption="Independence of validators",
        question="Are active validators independent of each other and of the nodes they score?",
        classification="E+J",
        paper_says="Operators and validators are the same set of participants; stake rank makes takeover of the set expensive.",
        evidence_needed="Disclosed keys and relationships, recusal and assignment rules, and any evidence of common control.",
        residual_uncertainty="Hidden common control, side payments and shared commercial interests remain possible.",
        authority="Governance sets disclosure rules; validators and delegators assess",
        consequence="Decides whether a median of scores reflects independent views.",
        concepts="LP-06 LP-07", provisions="RL-18 RL-19", claims="CL-07", participants="validator operator delegator",
        owner_milestone="M1.3", source_ref="SRC-LP20 L49, L73; SRC-MECHMAP gates 13-14", migrated_from="litepaper-validator-mechanism-map.md gates 13-14"),
}
for vd, f in NEW.items():
    put(vd, tags="Record VD", record_type="VD", stage="M1", status="open",
        introduced_by="M1.1", last_changed_by="M1.1",
        specification_status="Necessary missing detail",
        fix_by_rule=FIX[vd][0], fix_by_rule_by="agent", fix_note=FIX[vd][1], **f)

# ------------------------------------------------------------------ 5. M1.1 conclusions

CN = {
    "CN-07": dict(caption="Most of the money arithmetic can be written down today", status="inference",
        statement="The fee split, the burn, the emission shares, the MFS minimum, the median and the delay counters are arithmetic. They wait on policy choices, such as measurement windows, what happens to unassigned reward and when a round is final, but not on information from outside the protocol.",
        basis="Six of the open decisions need only a formula and a policy choice. They can be specified and then tested with small worked examples without anyone judging anyone.",
        carried_to="M2.1", decisions="VD-01 VD-06 VD-08 VD-12 VD-13 VD-15", provisions="RL-10 RL-24 RL-35 RL-53",
        concepts="LP-04 LP-11 LP-13", participants="operator governance"),
    "CN-08": dict(caption="What cannot be computed gathers around the honesty score", status="inference",
        statement="Almost every piece that needs a judgment feeds the honesty score: what counts as dishonest, what evidence is enough, who scores whom and when a score is final. These are also the adversarial pieces: each asks one operator to call out another, often a competitor.",
        basis="Every decision labelled as needing a judgment lists the honesty score among its concepts, except returning under a new identity (VD-27), which follows a penalty. The paper itself calls reward eligibility inherently subjective (line 83).",
        carried_to="M1.2 M1.3", decisions="VD-09 VD-10 VD-19 VD-22 VD-23 VD-26 VD-29", provisions="RL-23 RL-24 RL-25",
        concepts="LP-07 LP-06", participants="validator operator"),
    "CN-09": dict(caption="Some gaps wait for a rule, others wait for information", status="inference",
        statement="A gap that needs only a formula and a policy choice closes once someone writes the rule. A gap that needs outside data or a judgment does not: the rule can say who looks and how, but not what they will see. Whether that information exists is the next question.",
        basis="In the agent's first pass, every piece that needs only a formula and a policy choice is marked as settled by a rule. Most pieces that need a judgment are marked for a human call; the exceptions are procedures, such as when a score becomes final, that can be written even though what they carry is a judgment. The split is a proposal until people confirm it in M2.2.",
        carried_to="M1.2 M2.2", decisions="VD-05 VD-11 VD-04 VD-09 VD-19", concepts="LP-07 LP-04",
        participants="validator governance"),
}
for cn, f in CN.items():
    put(cn, tags="Record CN", record_type="CN", stage="M1", task="M1.1", introduced_by="M1.1", last_changed_by="M1.1", **f)

# ------------------------------------------------------------------ 6. mechanism stories (LP text)

STORY_HEAD = '<div class="vtw-storynote">Mechanism story, drafted by an agent from the records below. Edit it freely, or <$link to="View: Contributor notes">leave a note</$link> if you think it is wrong.</div>'


def story(lp, gives, leaves, suspect, nxt):
    return f"""{STORY_HEAD}

<div class="vtw-story">
<h3>What the paper gives us</h3>
<p>{gives}</p>
<h3>What it leaves to be built</h3>
<p>{leaves}</p>
<$transclude $variable="vtw-buildlist" lp="{lp}"/>
<h3>What we suspect, and how we will check</h3>
<p>{suspect}</p>
<h3>Where it goes next</h3>
<p>{nxt}</p>
</div>"""


STORIES = {
    "LP-07": story("LP-07",
        "Each active validator scores every node from 0 to 1, and the median scales the node's reward (<<r RL-23>>, <<r RL-24>>). The target is dishonesty: self-dealing, fabricated fees, incorrect results. Service quality is explicitly not the target (<<r RL-25>>). The tooling behind the judgments is to be funded as a public good (<<r RL-26>>). The paper is candid that eligibility is \"inherently subjective\", and says validators opt in partly so they can push back if others try to zero their rewards.",
        "What counts as each kind of dishonesty, what evidence is enough, how a finding becomes a number, who may score whom, what happens when validators abstain, when a score is final, and how an operator appeals. The validator constitution is one of the paper's own open questions (<<r RL-65>>).",
        "The median is simple arithmetic. Everything feeding it is judgment, and most of that judgment is adversarial: to lower a score, one operator has to call out another, usually a competitor, on evidence that may be thin. Self-dealing is the hardest case. A job paid for by the node's own affiliate can look exactly like one paid for by a stranger (<<r SC-06>> beside <<r SC-07>>). If that holds, a validator must choose between accusing on little data and staying silent. Either choice has a cost: an honest operator who feels wrongly accused, or self-dealing that goes through. The worry is that the score becomes a court without a record. This is a hypothesis. M1.2 checks what data a validator could actually hold; M1.3 lays out who is asked to judge whom; M2.1 asks what a validator gains or loses from each choice.",
        "M2.2 decides, piece by piece, whether a written rule closes each gap or whether some would remain under any rule."),
    "LP-04": story("LP-04",
        "A node's share of new LPT is the smaller of its share of network fees and its share of stake (<<r RL-10>>), scaled by the median honesty score. Fees themselves are never capped (<<r RL-11>>). The paper's reasoning: a low-stake node gains little by paying itself, because stake caps the reward. When fee and stake shares line up, the whole node budget is paid (<<r EX-01.F1>>).",
        "Measurement windows and denominators (<<r VD-05>>). The appendix describes node rewards differently from the main text (<<r VD-06>>). Nothing says where reward goes when fee and stake shares diverge (<<r VD-12>>): in one worked example, 752 of 940 LPT has no stated destination (<<r EX-01.F2>>). All of this is arithmetic waiting on policy choices.",
        "The stake cap limits a node's share of the pool. Under a fee-linked emissions schedule, paying yourself may also grow the pool (<<r FR-01>>, <<r FR-23>>). A party with enough stake, including stake it delegates to itself, is not limited by the cap (<<r FR-19>>). Whether paying yourself for real work is profitable depends on the emissions rule, the fee split and the value of LPT; that is a worked example for M2.1, not a finding yet. The fee share is also where the non-computable question enters: MFS cannot see whether a fee came from independent demand (<<r CN-04>>).",
        "M1.2 asks whether any data could tell independent demand from self-payment. M2.1 runs the numbers."),
    "LP-06": story("LP-06",
        "The top N nodes by stake, proposed at 33, may opt in as validators (<<r RL-19>>, <<r RL-20>>). Operators and validators are the same set (<<r RL-18>>). Stake makes takeover of the set expensive. Validators share a small slice of new LPT (<<r RL-22>>).",
        "How ranking, ties and vacancies work (<<r VD-08>>), how the validator slice is divided (<<r VD-17>>), whether validators are independent of each other and of the nodes they score (<<r VD-29>>), and whether pay depends on participation (<<r RL-63>>).",
        "Seat selection is arithmetic. What stake cannot show is independence: the largest operators are each other's competitors, and they score each other and everyone else. As written, pay does not depend on how carefully a validator scores. If accuracy is not paid and accusation carries a cost, scoring everyone 1.0 may be the comfortable choice. Coordinated scoring against a competitor is the opposite risk (<<r SC-09>>). Both are hypotheses for M2.1.",
        "M1.3 maps who judges whom. M2.1 works through what a validator gains or loses from each way of scoring."),
    "LP-05": story("LP-05",
        "Delegators bond to nodes as they do today. The stake behind a node sets its reward ceiling, and the paper expects active delegators to move stake toward busy, understaked nodes (<<r RL-15>>, <<r RL-16>>). Stake also decides who can validate.",
        "Whether and when stake can move between nodes (<<r VD-13>>), and what information delegators need to choose well (<<r FR-15>>).",
        "Delegation is meant to be the correcting force: stake flows to productive nodes. The 21-round lockup slows that (<<r FR-08>>). Delegators learn about a node's honesty mainly through scores, which may come without an explanation, and they share the loss when a node's score falls. How fast delegators really move, and what they would need to see, are questions for people who delegate (<<r HQ-01>>, <<r HQ-09>>).",
        "M1.2 asks what delegators can observe. M2.1 asks whether stake actually moves the way the paper expects."),
    "LP-09": story("LP-09",
        "Rewards for a round become claimable seven rounds later, using the median score at the time of claiming (<<r RL-30>>, <<r RL-31>>). The delay answers the paper's most concrete attack: spike fees in one round and cash out before anyone notices (<<r SC-16>>). It replaces a ramp-up period for new nodes (<<r RL-60>>).",
        "When a round's result becomes final (<<r VD-11>>), which median applies (<<r VD-07>>), and who gets investigated within the window (<<r VD-25>>).",
        "A delay buys time; it does not supply evidence. A spike that was genuinely paid for real work looks the same after seven rounds as it did on the first. Because the score is read at claim time, the same round can also pay differently depending on when it is claimed (<<r SC-14>> beside <<r SC-15>>). Seven rounds is enough only if someone can tell a fabricated spike from a real one (<<r FR-21>>, <<r HQ-03>>).",
        "M1.2 asks what a validator could see within the window. M2.1 tests whether the delay changes anyone's payoff or only their timing."),
    "LP-12": story("LP-12",
        "The emissions section is an idea draft with three concepts (<<r RL-47>>, <<r RL-48>>, <<r RL-49>>). The first is worked through in detail: emissions start at 32 times fees and halve every two years, with a proposed annual cap (<<r RL-50>>).",
        "Which schedule, the LPT price source, and how periods line up (<<r VD-14>>). The price oracle is one of the paper's own open questions (<<r RL-62>>).",
        "This mechanism decides whether paying yourself can grow the whole reward pool. Under the first concept, below the cap, each dollar of reported fees raises total emissions. The paper's own analysis notes that the cap stops the pool growing but not a node taking a bigger share of it (<<r FR-23>>). Choosing a schedule is a policy choice, not a judgment, but it changes how much weight the honesty score has to carry.",
        "M2.1 runs each concept, clearly labelled, through the same small examples."),
    "LP-11": story("LP-11",
        "Half of each USDC fee goes to the node and half buys LPT, all of which is burned (<<r RL-33>>, <<r RL-34>>, <<r RL-36>>). Rewards come from a separate mint (<<r RL-40>>). The design of the buyback itself is left for later research (<<r RL-41>>).",
        "Split viability (<<r VD-15>>), the accounting if the burn is ever below 100% (<<r VD-16>>), and buyback price and timing (<<r VD-18>>).",
        "This is mostly arithmetic and market engineering; nobody has to judge anybody. Two economic questions remain: whether a 50% cut leaves room for API relays (<<r FR-07>>, <<r HQ-06>>), and whether burn equal to mint in dollars means equal in LPT (<<r FR-25>>). The burned half is also the part of a self-payment the payer cannot get back, which makes it the cost side of the self-dealing arithmetic.",
        "M2.1 uses the split in every worked example."),
    "LP-08": story("LP-08",
        "Unbonding for all stake behind a node rises to 21 rounds (<<r RL-27>>). Moving stake between nodes is either removed or delayed by the same period, and the paper says this trade-off is not settled (<<r RL-28>>, <<r RL-29>>, <<r RL-64>>).",
        "Which option for moving stake (<<r VD-13>>), and whether a penalty follows a person or only an address (<<r VD-27>>).",
        "The lockup is a liquidity cost, not a confiscation: the paper cuts rewards and does not take principal. It deters hit-and-run identities only if what could be extracted is worth less than the cost of waiting (<<r FR-22>>). A locked address is also not a stopped person: fresh capital under a new address is unaffected.",
        "M2.1 compares the lockup cost with what could be extracted."),
}
for lp, text in STORIES.items():
    put(lp, text=text, story_status="agent draft")

# ------------------------------------------------------------------ 7. questions for humans (HQ)

put("$:/vtw/schema/HQ", record_type="HQ", name="Question for humans", plural="Questions for humans",
    text="One question that only someone who runs, delegates to, validates or builds on the network can answer well. Answers are evidence and are cited like any other record.",
    **{"id-pattern": r"^HQ-\d{2}$", "required-tags": "Record HQ",
       "display": "caption status ask ask_who why answer answered_by step concepts decisions scenarios findings participants related introduced_by last_changed_by",
       "required": "caption status ask concepts stage introduced_by",
       "vocab-status": "open answered", "summary": "ask", "needs-concepts": "yes"})
put("$:/vtw/template/HQ", record_type="HQ", stage="M1", status="open", caption="", ask="", ask_who="", why="",
    answer="", answered_by="", step="", concepts="", decisions="", scenarios="", findings="", participants="",
    related="", introduced_by="", last_changed_by="", text="")
put("HQ", caption="Questions for humans", text="<<vtw-type-index>>")

HQS = {
    "HQ-01": dict(caption="How fast does stake really move?", step="M2.1", ask_who="Delegators",
        ask="When a node you back underperforms, or a better one appears, how quickly do you actually move your stake? What would a 21-round wait change for you?",
        why="The paper relies on stake flowing toward productive, understaked nodes. The lockup slows that.",
        concepts="LP-05 LP-08", findings="FR-08 FR-15", participants="delegator"),
    "HQ-02": dict(caption="Do you already pay for your own jobs?", step="M1.2", ask_who="Node operators and app builders who run their own nodes",
        ask="Do you send your own traffic through your own node today, for testing, warm-up or an internal product? Roughly how much, and could you show it was internal if asked?",
        why="Related-party work is legitimate, but on payment data it can look exactly like reward farming.",
        concepts="LP-04 LP-07", scenarios="SC-06 SC-07", decisions="VD-19", participants="operator customer"),
    "HQ-03": dict(caption="What does a real fee spike look like?", step="M1.3", ask_who="Node and gateway operators",
        ask="What causes a genuine jump in your fees, such as a launch, a viral app or a batch job? How would you show validators it was real within seven rounds?",
        why="The seven-round delay assumes validators can tell a fabricated spike from a real one.",
        concepts="LP-09 LP-07", scenarios="SC-16", findings="FR-21", participants="operator"),
    "HQ-04": dict(caption="What would you look at before scoring a competitor down?", step="M1.3", ask_who="Operators who would be in the top-staked set",
        ask="If you were an active validator, what would you look at before scoring another node below 1.0? What would make you unwilling to do it?",
        why="The honesty score depends on validators making calls about competitors on evidence that is not yet defined.",
        concepts="LP-07 LP-06", decisions="VD-09 VD-29", participants="validator operator"),
    "HQ-05": dict(caption="What does your gateway know about who paid?", step="M1.2", ask_who="Gateway and signer operators",
        ask="What does your gateway or remote signer record about who paid for a job, and what can it not see?",
        why="Funding relationships are the evidence a self-dealing judgment would need.",
        concepts="LP-10 LP-07", decisions="VD-19 VD-03", participants="operator customer"),
    "HQ-06": dict(caption="Could an API relay live with a 50% cut?", step="M2.1", ask_who="Operators relaying third-party APIs",
        ask="What share of your price goes to the upstream provider, and could you absorb a 50% network fee by raising prices?",
        why="The proposed split may leave little or no margin for pass-through businesses.",
        concepts="LP-11 LP-01", findings="FR-07", decisions="VD-15", participants="operator"),
    "HQ-07": dict(caption="What job evidence would customers share?", step="M1.2", ask_who="App builders and customers",
        ask="Would you accept sharing job evidence, such as receipts or output hashes, so validators can check work? What would you refuse to share?",
        why="Validators can only judge what they can see, and customers decide what they will expose.",
        concepts="LP-07", decisions="VD-26 VD-04", participants="customer"),
    "HQ-08": dict(caption="Whose fault is a failed job?", step="M1.3", ask_who="Node operators",
        ask="When a job fails, how often is the cause yours, the network's or an upstream provider's? Could you prove which?",
        why="The paper separates dishonesty from ordinary limitations, but someone has to tell them apart.",
        concepts="LP-07", decisions="VD-23", participants="operator"),
    "HQ-09": dict(caption="Would you back a node scored 0.5 without explanation?", step="M1.3", ask_who="Delegators",
        ask="Would you keep delegating to a node that validators scored 0.5 with no public explanation? What would you need to see?",
        why="Delegators share the loss when a score falls, and scores may not come with reasons.",
        concepts="LP-05 LP-07", decisions="VD-09", participants="delegator"),
}
for hq, f in HQS.items():
    put(hq, tags="Record HQ", record_type="HQ", stage="M1", status="open",
        introduced_by="M1.1", last_changed_by="M1.1", **f)

# ------------------------------------------------------------------ 8. contributor notes

put("$:/vtw/template/Note", author="", about="", filed_as="", text="")

# ------------------------------------------------------------------ 9. schema, fields, labels

for rt in ("VD", "FR"):
    s = wiki[f"$:/vtw/schema/{rt}"]
    fix = ["fix_by_rule", "fix_by_rule_by", "fix_note"]
    disp = [d for d in s["display"].split() if d not in fix]
    i = disp.index("status") + 1
    disp[i:i] = fix
    put(f"$:/vtw/schema/{rt}", display=" ".join(disp), **{"vocab-fix_by_rule": "yes no unsure"})
    tpl = f"$:/vtw/template/{rt}"
    put(tpl, fix_by_rule="", fix_by_rule_by="", fix_note="")

put("$:/vtw/schema/CS", text=wiki["$:/vtw/schema/CS"]["text"].replace("(M1.4)", "(M1.2)"))
put("$:/vtw/schema/LP", display=wiki["$:/vtw/schema/LP"]["display"] + " story_status")

dict_set("$:/vtw/fields", {
    "introduced_by": "Task that created the record (Orientation, M1.1 ...). Records from the first pass were introduced by Orientation, formerly M1.1.",
    "components": "CS IDs (M1.2).",
    "owner_milestone": "Steps or milestones expected to carry the question (M1.2, M1.3, M2.1, M2.2, M3).",
    "fix_by_rule": "Would a written rule close this gap? yes: a rule settles it (and says nothing against the paper). no: it would remain under any reasonable rule. unsure: needs a human call. Blank: not assessed.",
    "fix_by_rule_by": "Who set fix_by_rule: 'agent' for a proposal, or a person's name once someone has decided.",
    "fix_note": "One line explaining the fix_by_rule value.",
    "story_status": "Concepts: 'agent draft' or 'edited' for the mechanism story in the text.",
    "issues": "Tasks: GitHub issue numbers this step reports under. Issue titles are not changed by the workbench.",
    "ask": "Questions for humans: the question, in the words you would use with the person.",
    "ask_who": "Questions for humans: who can answer it well.",
    "why": "Questions for humans: why the answer matters to the research.",
    "answer": "Questions for humans: the answer, with who gave it and when.",
    "answered_by": "Questions for humans: who answered.",
    "step": "Questions for humans: the path step that needs the answer.",
    "author": "Contributor notes: who wrote the note.",
    "about": "Contributor notes: concept IDs (LP-..) or anything else the note concerns.",
    "filed_as": "Contributor notes: record IDs an agent created or changed from this note.",
})

put("$:/vtw/labels-plain", type="application/x-tiddler-dictionary",
    text="D: a formula\nE: data from outside the protocol\nJ: a judgment\nG: a policy choice\nS: allowance for outputs that vary by nature")

# ------------------------------------------------------------------ 10. procedures and styles (dedupe + additions)

proc = wiki["$:/vtw/procedures"]["text"]
parts = proc.split("\\function vtw.reader()")
if len(parts) > 2:  # keep the head and the last (corrected) copy of the repeated block
    proc = parts[0] + "\\function vtw.reader()" + parts[-1].rstrip() + "\n"
proc += r"""
\procedure vtw-kinds(cls)
<$list filter="[<cls>split[+]]" variable="l" join=", "><$text text={{{ [[$:/vtw/labels-plain]getindex<l>] }}}/></$list>
\end

\procedure vtw-fix()
<%if [all[current]field:fix_by_rule[yes]] %><span class="vtw-fix vtw-fix-yes">yes</span>
<%elseif [all[current]field:fix_by_rule[no]] %><span class="vtw-fix vtw-fix-no">no</span>
<%elseif [all[current]field:fix_by_rule[unsure]] %><span class="vtw-fix vtw-fix-unsure">needs a human call</span>
<%else%><span class="vtw-none">not assessed</span>
<%endif%>
<%if [all[current]field:fix_by_rule_by[agent]] %><span class="vtw-idsmall">&#32;agent proposal</span><%elseif [all[current]has[fix_by_rule_by]] %><span class="vtw-idsmall">&#32;decided by&#32;<$text text={{!!fix_by_rule_by}}/></span><%endif%>
<%if [all[current]has[fix_note]] %><div class="vtw-readsum"><$transclude field="fix_note" mode="inline"/></div><%endif%>
\end

\procedure vtw-buildtable(filter)
<table class="vtw-grid vtw-build"><tbody>
<tr><th>What has to be decided or built</th><th>What it needs</th><th>Would a written rule settle it?</th></tr>
<$list filter=<<filter>> emptyMessage="<tr><td class='vtw-none'>Nothing here yet.</td><td/><td/></tr>">
<tr>
<td><$link><$text text={{!!caption}}/></$link><div class="vtw-readsum"><$text text={{{ [all[current]get[question]else{!!statement}] }}}/></div></td>
<td><%if [all[current]has[classification]] %><$transclude $variable="vtw-kinds" cls={{!!classification}}/><%else%><span class="vtw-none">finding</span><%endif%></td>
<td><<vtw-fix>></td>
</tr>
</$list>
</tbody></table>
\end

\procedure vtw-buildlist(lp)
<$transclude $variable="vtw-buildtable" filter="[tag[VD]!field:status[split]contains:concepts<lp>sort[title]]"/>
\end

\procedure vtw-hqcard()
<div class="vtw-hq">
<div class="vtw-concl-h"><$link><$text text={{!!caption}}/></$link>&#32;<<vtw-status>></div>
<div class="vtw-concl-s"><$transclude field="ask" mode="inline"/></div>
<div class="vtw-concl-b">''Who can answer:''&#32;<$text text={{!!ask_who}}/>.&#32;''Why it matters:''&#32;<$transclude field="why" mode="inline"/></div>
<%if [all[current]has[answer]] %><div class="vtw-concl-e">''Answer''<%if [all[current]has[answered_by]] %>&#32;(<$text text={{!!answered_by}}/>)<%endif%>:&#32;<$transclude field="answer" mode="inline"/></div>
<%else%><div class="vtw-concl-e">No answer yet.&#32;<$button class="vtw-new" message="tm-edit-tiddler" param=<<currentTiddler>>>Answer this</$button></div>
<%endif%>
</div>
\end

\procedure vtw-new-note()
<$button class="vtw-new" tooltip="Start a new contributor note">
<$action-sendmessage $message="tm-new-tiddler" $param="$:/vtw/template/Note" title="Note: untitled" tags="Note"/>
Write a note
</$button>
\end
"""
put("$:/vtw/procedures", text=proc)

css_seen, css_out = set(), []
for line in wiki["$:/vtw/styles"]["text"].splitlines():
    if line.strip() and line in css_seen:
        continue
    css_seen.add(line)
    css_out.append(line)
css_out += [
    ".vtw-fix { display: inline-block; padding: 0 0.45em; border-radius: 0.6em; font-size: 0.85em; }",
    ".vtw-fix-yes { background: #dcefe4; }",
    ".vtw-fix-no { background: #fde2e1; }",
    ".vtw-fix-unsure { background: #fff1cc; }",
    "table.vtw-build td:first-child { width: 45%; }",
    "table.vtw-build td:nth-child(2) { width: 25%; font-size: 0.92em; }",
    "details.vtw-mech { border-bottom: 1px solid #e3eaef; padding: 0.3em 0; }",
    "details.vtw-mech > summary { font-size: 1em; color: #23343f; }",
    ".vtw-storynote { font-size: 0.85em; color: #6b7f8c; font-style: italic; margin-bottom: 0.4em; }",
    ".vtw-story h3 { font-size: 1.05em; margin: 1em 0 0.3em; color: #2f6f8f; }",
    ".vtw-story p { line-height: 1.5; }",
    ".vtw-hq { border: 1px solid #e6d9b8; border-left: 4px solid #d9a400; padding: 0.5em 0.8em; margin: 0.6em 0; background: #fffdf6; }",
    ".vtw-home h2 { margin-top: 1.3em; }",
    ".vtw-rules li { margin: 0.4em 0; }",
]
put("$:/vtw/styles", text="\n".join(css_out))

# ------------------------------------------------------------------ 11. templates that list record types

for title in ("$:/vtw/ui/JourneyBottom", "$:/vtw/ui/RecordRollup", "$:/vtw/ui/SideBarViews"):
    txt = wiki[title]["text"]
    txt = txt.replace('filter="CN LP RL VD CL FR SC EX FX CS"', 'filter="CN LP RL VD CL FR SC EX FX CS HQ"')
    txt = txt.replace('filter="CN RL VD CL SC FR EX FX CS"', 'filter="CN RL VD CL SC FR EX FX CS HQ"')
    txt = txt.replace('filter="CN LP RL VD CL FR SC EX CS"', 'filter="CN LP RL VD CL FR SC EX CS HQ"')
    if title == "$:/vtw/ui/RecordRollup":
        txt = txt.replace(
            '<$transclude $variable="vtw-section" label="Models" filter="[tag[EX]contains:concepts<id>sort[title]]"/>',
            '<$transclude $variable="vtw-section" label="Models" filter="[tag[EX]contains:concepts<id>sort[title]]"/>\n'
            '<$transclude $variable="vtw-section" label="Questions for people who run this" filter="[tag[HQ]contains:concepts<id>sort[title]]"/>\n'
            '<$transclude $variable="vtw-section" label="Notes from contributors" filter="[tag[Note]contains:about<id>sort[title]]"/>')
    if title == "$:/vtw/ui/SideBarViews":
        txt = txt.replace('<div><$link to="Home">Start here</$link></div>',
            '<div><$link to="Home">Start here</$link></div>\n'
            '<div><$link to="View: Mechanism stories">Mechanism stories</$link></div>\n'
            '<div><$link to="View: Questions for humans">Questions for humans</$link>&#32;<span class="vtw-count">(<$count filter="[tag[HQ]field:status[open]] [tag[VD]field:fix_by_rule[unsure]]"/>)</span></div>\n'
            '<div><$link to="View: Contributor notes">Contributor notes</$link>&#32;<span class="vtw-count">(<$count filter="[tag[Note]]"/>)</span></div>')
        txt = txt.replace('<$list filter="[[Conventions]] [tag[View]sort[title]]">',
            '<$list filter="[[Conventions]] [tag[View]sort[title]] -[[View: Mechanism stories]] -[[View: Questions for humans]] -[[View: Contributor notes]]">')
    put(title, text=txt)

# ------------------------------------------------------------------ 12. views

put("View: Mechanism stories", tags="View", description="Each mechanism told end to end, from the paper to the open questions",
    text=r"""<p class="vtw-lede">One page per mechanism, told end to end: what the paper gives us, what it leaves to be built, what we suspect, and where it goes next. Agents draft them from the records; people edit them. If a story is wrong, fix it or leave a note.</p>
<ul class="vtw-read">
<$list filter="[tag[LP]has[story_status]sort[title]]">
<li><$link><$text text={{!!caption}}/></$link>&#32;<span class="vtw-idsmall"><$text text={{!!story_status}}/></span>
<div class="vtw-readsum"><$transclude field="in_paper" mode="inline"/></div>
<div class="vtw-idsmall"><$count filter="[tag[VD]!field:status[split]contains:concepts<currentTiddler>]"/>&#32;open pieces ·&#32;<$count filter="[tag[VD]!field:status[split]contains:concepts<currentTiddler>field:fix_by_rule[unsure]]"/>&#32;for a human call ·&#32;<$count filter="[tag[HQ]contains:concepts<currentTiddler>]"/>&#32;questions for humans</div></li>
</$list>
</ul>
<h3>Not drafted yet</h3>
<$transclude $variable="vtw-readlist" filter="[tag[LP]!has[story_status]field:kind[mechanism]sort[title]] [tag[LP]!has[story_status]field:kind[parameter-set]sort[title]]"/>""")

put("View: Questions for humans", tags="View", description="Questions only practitioners can answer, and calls an agent could not make",
    text=r"""<p class="vtw-lede">Some things in this research cannot be settled by reading the paper or the code. They need someone who runs a node, delegates, operates a gateway, validates or builds an app. If that is you, your answer is evidence, and it will be cited like any other source.</p>
<p>To answer, press ''Answer this'', fill in ''answer'' and ''answered by'', and set ''status'' to answered. If you would rather just write, <$link to="View: Contributor notes">leave a note</$link>.</p>
<h2>Questions for people who run this</h2>
<$list filter="[tag[HQ]field:status[open]sort[title]]" emptyMessage="<p class='vtw-none'>No open questions.</p>"><<vtw-hqcard>></$list>
<h2>Calls an agent could not make</h2>
<p>An agent sorted every open piece by whether a written rule would settle it. Where it could not tell, it asked for a human call. Open a piece, decide, and set ''fix by rule'' to yes or no with a one-line ''fix note''. Put your name in ''fix by rule by''.</p>
<$transclude $variable="vtw-buildtable" filter="[tag[VD]field:fix_by_rule[unsure]sort[title]] [tag[FR]field:fix_by_rule[unsure]sort[title]]"/>
<h2>Answered</h2>
<$list filter="[tag[HQ]field:status[answered]sort[title]]" emptyMessage="<p class='vtw-none'>None yet.</p>"><<vtw-hqcard>></$list>""")

put("View: Contributor notes", tags="View", description="Free-form notes from anyone; an agent files them into records",
    text=r"""<p class="vtw-lede">You do not need to know the record system to contribute. Write what you noticed, what you disagree with, or what you know from running the network. An agent reads each note, files it into the records it affects, and lists them in the note's ''filed as'' field so you can see where it went.</p>
<p><<vtw-new-note>>&#32;Give it a title that says the point. In ''about'', you can list the mechanisms it concerns (for example LP-07), but you do not have to.</p>
<h2>Waiting to be filed</h2>
<$list filter="[tag[Note]!has[filed_as]sort[modified]]" emptyMessage="<p class='vtw-none'>No notes waiting.</p>">
<div class="vtw-concl"><div class="vtw-concl-h"><$link><$text text=<<currentTiddler>>/></$link></div>
<div class="vtw-concl-b"><$text text={{{ [all[current]get[author]else[anonymous]] }}}/>&#32;·&#32;<$view field="modified" format="date" template="DD MMM YYYY"/></div>
<div class="vtw-concl-s"><$transclude mode="block"/></div></div>
</$list>
<h2>Filed</h2>
<$list filter="[tag[Note]has[filed_as]sort[title]]" emptyMessage="<p class='vtw-none'>None yet.</p>">
<div><$link><$text text=<<currentTiddler>>/></$link>&#32;<span class="vtw-idsmall">filed as&#32;<$text text={{!!filed_as}}/></span></div>
</$list>""")

dash = wiki["View: Milestone dashboard"]["text"]
dash = dash.replace('<$list filter="[tag[Task]sort[title]]">', '<$list filter="[enlist{$:/vtw/path!!list}] [tag[Task]sort[title]]">')
dash = dash.replace('<td><a href={{!!issue}} target="_blank" rel="noopener noreferrer">issue</a></td>',
    '<td><$transclude field="question" mode="inline"/><div class="vtw-idsmall">reports under&#32;<a href={{!!issue}} target="_blank" rel="noopener noreferrer"><$text text={{{ [all[current]get[issues]else[issue]] }}}/></a></div></td>')
dash = dash.replace("<p>Review status belongs to the task, never to a record. Only Shane sets Accepted.</p>",
    "<p>Review status belongs to the task, never to a record. Only Shane sets Accepted. The workbench path was restructured on 2026-09-28; GitHub issue titles still use the earlier task names until they are revisited.</p>")
put("View: Milestone dashboard", text=dash)

put("View: Component impact", description="Current system to litepaper, by component and system area (M1.2)",
    text=wiki["View: Component impact"]["text"].replace("M1.4 has not started.", "This is part of M1.2, which has not started."))

put("VD-13", concepts="LP-08 LP-05")
for title, t in list(wiki.items()) + [(k, v) for k, v in OUT.items()]:
    if "View" in (t.get("tags") or "").split() and title.startswith("View: "):
        put(title, caption=title.removeprefix("View: "))

# ------------------------------------------------------------------ 13. Home, Conventions, About

put("Home", text=r"""<div class="vtw-home">
<p class="vtw-lede">This workbench follows one line of thought about the Livepeer 2.0 litepaper, from a first reading to evidence. It is written so that anyone who runs a node, delegates, validates or builds on Livepeer can follow it and push back.</p>

<h2>Where this started</h2>
<p>Some of the litepaper is plainly arithmetic: split a fee, compare two shares, take a median, count rounds. Anyone can check arithmetic.</p>
<p>Other parts cannot be computed. Someone has to look at the world, or make a call. Most of those parts are adversarial. The paper asks validators to catch self-dealing, fabricated fees and incorrect results. That means one operator calling out another, often a competitor, usually with very little data to go on.</p>
<p>That raises a hard social question. Do you call someone out on thin evidence? If you do and you are wrong, an honest operator has been publicly accused. If you don't, self-dealing goes through. Either way, the network ends up running something like a court to prevent self-dealing, without the records a court would need.</p>
<p>That is a first impression, not a finding. The path below tests it one question at a time, with data. Two rules keep it fair to the paper:</p>
<ul class="vtw-rules">
<li>''Missing detail is not an argument.'' A litepaper sets out an architecture. When it leaves a rule unwritten, we ask what would need to be built, not whether the paper failed.</li>
<li>''Only problems that survive a written rule count.'' If writing the rule would fix it, it goes on the list of things to build. If it would remain under any reasonable rule, it is carried forward with its evidence.</li>
</ul>

<h2>How to take part</h2>
<ul class="vtw-rules">
<li>''Read a mechanism story.''&#32;Each one follows a single mechanism from the paper to its open questions:&#32;<$link to="View: Mechanism stories">Mechanism stories</$link>. If one is wrong, say so.</li>
<li>''Answer a question only practitioners can.''&#32;<$link to="View: Questions for humans">Questions for humans</$link>&#32;(<$count filter="[tag[HQ]field:status[open]]"/>&#32;open, plus&#32;<$count filter="[tag[VD]field:fix_by_rule[unsure]]"/>&#32;calls an agent could not make).</li>
<li>''Leave a note about anything.''&#32;<$link to="View: Contributor notes">Contributor notes</$link>. You do not need to know the record system; an agent files notes and links back to them.</li>
</ul>

<h2>The path</h2>
<ol class="vtw-pathlist">
<$list filter="[enlist{$:/vtw/path!!list}]">
<li><$link><strong><$text text={{!!caption}}/></strong></$link>&#32;<span class="vtw-idsmall"><$text text=<<currentTiddler>>/></span>
<div class="vtw-readsum"><$transclude field="question" mode="inline"/></div>
<div class="vtw-idsmall">
<%if [tag[CN]field:task<currentTiddler>] %><$count filter="[tag[CN]field:task<currentTiddler>]"/>&#32;draft conclusions<%elseif [all[current]get[text]!is[blank]] %>outlined, not started<%else%>not started<%endif%>
<%if [tag[CN]contains:carried_to<currentTiddler>] %>&#32;·&#32;conclusions carried in:&#32;<$count filter="[tag[CN]contains:carried_to<currentTiddler>]"/><%endif%>
</div></li>
</$list>
</ol>

<h2>Where things stand</h2>
<p><$count filter="[tag[VD]!field:status[split]]"/>&#32;open pieces are recorded. An agent's first pass says a written rule would settle&#32;<$count filter="[tag[VD]field:fix_by_rule[yes]]"/>&#32;of them; <$count filter="[tag[VD]field:fix_by_rule[unsure]]"/>&#32;need a human call; people have marked&#32;<$count filter="[tag[VD]field:fix_by_rule[no]]"/>&#32;as surviving any reasonable rule (<$link to="M2.2">register</$link>).</p>
<p class="vtw-lede">Draft conclusions, not yet reviewed:</p>
<$transclude $variable="vtw-readlist" filter="[tag[CN]sort[title]]"/>

<h2>Other ways in</h2>
<ul>
<li>''How money moves:''&#32;<$link to="View: Cooperative flow">Cooperative flow</$link></li>
<li>''Find a rule, number or decision:''&#32;<$link to="View: Record finder">Record finder</$link>&#32;·&#32;<$link to="View: Parameter sheet">Parameter sheet</$link>&#32;·&#32;<$link to="View: Open decisions">Open decisions</$link></li>
</ul>
<details class="vtw-details"><summary>For editors and agents</summary>
<p><$link to="Conventions">Conventions</$link>&#32;·&#32;<$link to="About this wiki">About this wiki</$link>&#32;·&#32;<$link to="SRC-LP20">Source: litepaper snapshot</$link></p>
<$list filter="[tag[View]sort[title]]"><div><$link/> <span class="vtw-refcap"><$text text={{!!description}}/></span></div></$list>
</details>
</div>""")

conv = wiki["Conventions"]["text"]
conv = conv.replace("grounded in [[SRC-LP20]] and, for M1.4, current-system evidence.",
                    "grounded in [[SRC-LP20]] and, from M1.2 on, current-system evidence.")
old_scope_start = conv.index("<h2>Scope during M1 and M2</h2>")
old_scope_end = conv.index("<h2>Record types</h2>")
conv = conv[:old_scope_start] + r"""<h2>Scope during M1 and M2</h2>
<p>Records explain and test the litepaper. They label assumptions and hypotheses, and establish gaps through findings. They do not describe successor mechanisms or compare against one. Record types and fields for M3 are added when M3 starts. The ID prefix EL is reserved and has no records. Preserve counterevidence in ''would_change''.</p>

<h2>How the path is organized</h2>
<p>The path follows one chain of reasoning: how the paper works; what the protocol can compute on its own; where the data for the rest would come from; who is asked to judge what; how people would behave once the rules were written; and which problems a written rule would fix. Each step is written as prose for people, with records as its evidence, and ends in conclusions the next step starts from.</p>
<ul>
<li>''Missing detail is not a finding.'' A missing rule becomes something to build. Record it as an open decision, never as a fault in the paper.</li>
<li>''Rule or not.'' Every open decision, and in M2 every finding, carries ''fix_by_rule'': yes, no or unsure. Agents may propose yes or unsure and set ''fix_by_rule_by'' to agent. Only a person sets no, or confirms a proposal by putting their name in ''fix_by_rule_by''.</li>
<li>''One mechanism, one story.'' Each mechanism's page carries a story in its text that follows it through every step. Agents keep it in step with the records; people edit it.</li>
<li>''Plain words for people.'' The labels D, E, J, G and S stay in record fields. Anything a person reads says "a formula", "data from outside the protocol", "a judgment", "a policy choice" or "outputs that vary by nature".</li>
<li>''People can contribute without the schema.'' Contributor notes (tag Note) are free text. An agent files each one into records and lists them in ''filed_as''. Questions for humans (HQ) collect what only practitioners can answer; answers are evidence.</li>
</ul>

""" + conv[old_scope_end:]
put("Conventions", text=conv.replace("\\whitespace trim\n", "", 1))

about = wiki["About this wiki"]["text"]
if "v1-2026-09-28" not in about:
    about += "\n* Reference copy before the 2026-09-28 restructure: `/home/mav/repos/livepeer/validator-track-workbench-v1-2026-09-28.html`. It is kept for comparison and is not edited."
put("About this wiki", text=about)

json.dump(list(OUT.values()), sys.stdout, indent=1, ensure_ascii=False)
print(f"{len(OUT)} tiddlers", file=sys.stderr)
