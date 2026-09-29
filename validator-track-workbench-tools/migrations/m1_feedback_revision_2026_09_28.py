"""Revision after review feedback (2026-09-28, T3 thread 4bb19e96).

- Exact computation is not treated as sound incentives: every mechanism goes to M2.1.
- fix_by_rule (yes/no/unsure) is replaced by resolved_by (specification, evidence,
  incentives, policy), spec_settles, still_to_test and reviewed_by.
- M3 threshold: plausible completions compared on tradeoffs, not "any reasonable rule".
- Each mechanism shows its full chain (purpose to output), including what the paper specifies.
- Neutral, impersonal voice: no first person; "you" only in instructions and practitioner questions.
- Counts are described as properties of the inventory; review is not evidence;
  practitioner answers record whether they are observed or expected.

Usage: python3 m1_feedback_revision_2026_09_28.py WIKI > revision.json
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


# ------------------------------------------------------------------ 1. resolution fields on decisions

R = {  # resolved_by, spec_settles, still_to_test
    "VD-01": ("specification", "A registry specification: admission, advert format and updates.", "Nothing for the registry itself; whether listing leads to sales is VD-02."),
    "VD-02": ("specification evidence", "A discovery and routing specification.", "Whether new listings receive traffic in practice."),
    "VD-03": ("specification", "Settlement, attribution, reversal and accounting-period rules, and payment security with unlimited nodes.", "Settlement shows that a payment happened, not who funded it or why (VD-19)."),
    "VD-04": ("specification evidence", "Receipt and delivery-evidence requirements for each workload type.", "Whether receipts can be obtained for third-party API and private jobs, and what checking them costs."),
    "VD-05": ("specification incentives", "Windows, snapshots, eligible versus gross fees, zero totals and denominators.", "Whether the choice of window changes the payoff from self-payment or fee spikes."),
    "VD-06": ("specification incentives", "One node entitlement formula and the order of minimum, allocation and weighting.", "How each possible formula changes the payoff from self-payment and from stake concentration."),
    "VD-07": ("specification", "Score version, precision, absent submissions, challenged scores and order against MFS.", "The aggregation can be exact; the scores it aggregates remain judgments (VD-09)."),
    "VD-08": ("specification evidence", "Ranking population, snapshots, ties and vacancies.", "How concentrated the resulting set is, and whether stake rank says anything about independence (VD-29)."),
    "VD-09": ("specification evidence policy", "Criteria for each kind of dishonesty, a proof standard, a mapping from finding to score, and appeals.", "Whether available evidence can meet those criteria, especially for self-dealing, and at what error rate and cost."),
    "VD-10": ("specification evidence incentives", "Quorum, abstention, defaults, even-count medians and recusal.", "Whether validators have reason to take part and score carefully, and whether hidden common control distorts the median."),
    "VD-11": ("specification", "A claim deadline, a score snapshot per earning round, finality and late-claim treatment.", "Whether the chosen window is long enough for the evidence to arrive (VD-25)."),
    "VD-12": ("specification incentives policy", "Whether unassigned reward is never minted, held, burned or redistributed.", "Each option changes incentives; redistribution can make suppressing a rival profitable."),
    "VD-13": ("policy incentives", "A choice between removing and delaying bond transfers, with exposure across pending claims.", "How fast stake still moves toward productive nodes under each option."),
    "VD-14": ("policy incentives evidence", "A chosen schedule, price source, period alignment and zero-fee rule.", "Whether reported fees can enlarge the pool below the cap, and whether the price source resists manipulation."),
    "VD-15": ("policy incentives", "The split parameters.", "Whether operators, API relays in particular, stay viable, and how much of a self-payment the payer cannot recover."),
    "VD-16": ("specification", "One denominator for the fee-side cuts.", "Actual LPT burned against LPT minted, once execution exists."),
    "VD-17": ("specification incentives", "An equal or stake-weighted split, the meaning of post-BME mint, and any participation condition.", "Whether validator pay rewards careful scoring or only holding a seat."),
    "VD-18": ("specification evidence", "Pool, TWAP window, frequency, slippage and rollover rules.", "Manipulation and execution quality in the actual market."),
    "VD-19": ("policy evidence incentives", "A statement of what the reward is meant to buy and which distinctions eligibility must make.", "Whether any observable evidence separates self-funded real work from independent demand, and whether self-payment is profitable under each emissions concept."),
    "VD-21": ("specification policy", "A constitution separating policy changes from case decisions, with limits on replacing the score contract.", "Whether the separation holds when the same participants govern and score."),
    "VD-22": ("specification evidence", "Task terms and acceptable variation for each job type.", "Which properties can be checked without reproducing the same output, and at what cost."),
    "VD-23": ("evidence policy", "Promised-versus-delivered records and rules for attributing failures.", "Whether failures can be attributed without judging intent, and how often they are ambiguous."),
    "VD-24": ("policy incentives", "Either every agreed price counts, or a benchmark and a policy for fees above it.", "Whether high self-set prices raise reward under either option."),
    "VD-25": ("specification evidence incentives", "Sampling and trigger rules, coverage targets and reporting.", "Whether triggers catch adaptive behaviour, and what monitoring costs."),
    "VD-26": ("specification evidence", "Signature, provenance, retention and privacy requirements.", "Whether authenticated evidence is true and available, especially for private jobs."),
    "VD-27": ("specification incentives", "Rules that keep stake and pending claims under their original rounds.", "Whether a penalty deters an actor who can return with fresh capital under a new address."),
    "VD-28": ("policy evidence", "A funding and oversight arrangement with published deliverables and access rules.", "Whether validators relying on shared tooling still judge independently."),
    "VD-29": ("specification evidence", "Disclosure, recusal and assignment rules.", "Whether hidden common control can be detected at all."),
}
for vd, (rb, ss, st) in R.items():
    put(vd, resolved_by=rb, spec_settles=ss, still_to_test=st,
        fix_by_rule=None, fix_by_rule_by=None, fix_note=None)

for rt in ("VD", "FR"):
    s = wiki[f"$:/vtw/schema/{rt}"]
    new = ["resolved_by", "spec_settles", "still_to_test", "reviewed_by"]
    disp = [d for d in s["display"].split() if d not in ("fix_by_rule", "fix_by_rule_by", "fix_note") + tuple(new)]
    i = disp.index("status") + 1
    disp[i:i] = new
    put(f"$:/vtw/schema/{rt}", display=" ".join(disp), **{
        "vocab-fix_by_rule": None,
        "pattern-resolved_by": r"^(specification|evidence|incentives|policy)( (specification|evidence|incentives|policy))*$"})
    put(f"$:/vtw/template/{rt}", fix_by_rule=None, fix_by_rule_by=None, fix_note=None,
        resolved_by="", spec_settles="", still_to_test="", reviewed_by="")

hq = wiki["$:/vtw/schema/HQ"]
put("$:/vtw/schema/HQ", display=hq["display"].replace("answer answered_by", "answer answer_basis answered_by"),
    **{"vocab-answer_basis": "observed expected both"})
put("$:/vtw/template/HQ", answer_basis="")

# field dictionary: drop fix_*, add new, neutral wording
lines = [l for l in wiki["$:/vtw/fields"]["text"].splitlines() if l.split(":", 1)[0].strip() not in ("fix_by_rule", "fix_by_rule_by", "fix_note")]
text = "\n".join(lines)
text = text.replace("starting_point: Journey steps: what we knew or assumed going in, in prose.",
                    "starting_point: Journey steps: what was known or assumed going in, in prose.")
text = text.replace("ask: Questions for humans: the question, in the words you would use with the person.",
                    "ask: Questions for humans: the question, worded as it would be put to the person.")
text += "\n" + "\n".join([
    "resolved_by: What would resolve the piece: specification, evidence, incentives, policy (one or more). A piece resolved by specification alone says nothing against the paper.",
    "spec_settles: What a written specification would settle: the calculation or procedure.",
    "still_to_test: What remains after specification: information requirements, incentives, cost or effectiveness.",
    "reviewed_by: Blank while the classification is an agent proposal; the reviewer's name once a person has checked it. Review checks the classification; it is not evidence.",
    "requires: Concepts: the mechanism's chain from purpose to output, showing what the paper specifies and what is still to build or decide.",
    "answer_basis: Questions for humans: observed (seen in practice), expected (anticipated for a future system) or both.",
])
put("$:/vtw/fields", text=text)

put("$:/vtw/resolved-plain", type="application/x-tiddler-dictionary",
    text="specification: a specification\nevidence: better evidence\nincentives: incentive analysis\npolicy: a policy choice")

# ------------------------------------------------------------------ 2. procedures and styles

proc = cur("$:/vtw/procedures")["text"]
start = proc.index("\\procedure vtw-fix()")
end = proc.index("\\procedure vtw-buildlist(lp)")
proc = proc[:start] + r"""\procedure vtw-resolved()
<$list filter="[all[current]get[resolved_by]enlist-input[]]" variable="rb" join=" "><span class=`vtw-rb vtw-rb-$(rb)$`><$text text={{{ [[$:/vtw/resolved-plain]getindex<rb>] }}}/></span></$list>
<%if [all[current]has[resolved_by]] %><span class="vtw-idsmall">&#32;<%if [all[current]has[reviewed_by]] %>reviewed by&#32;<$text text={{!!reviewed_by}}/><%else%>agent proposal, not reviewed<%endif%></span><%endif%>
\end

\procedure vtw-buildtable(filter)
<table class="vtw-grid vtw-build"><tbody>
<tr><th>What has to be decided or built</th><th>What it needs</th><th>What a specification would settle</th><th>What still needs testing</th></tr>
<$list filter=<<filter>> emptyMessage="<tr><td class='vtw-none'>Nothing here yet.</td><td/><td/><td/></tr>">
<tr>
<td><$link><$text text={{!!caption}}/></$link><div class="vtw-readsum"><$text text={{{ [all[current]get[question]else{!!statement}] }}}/></div><div class="vtw-rbline"><<vtw-resolved>></div></td>
<td><%if [all[current]has[classification]] %><$transclude $variable="vtw-kinds" cls={{!!classification}}/><%else%><span class="vtw-none">finding</span><%endif%></td>
<td><$transclude field="spec_settles" mode="inline"/></td>
<td><$transclude field="still_to_test" mode="inline"/></td>
</tr>
</$list>
</tbody></table>
\end

""" + proc[end:]
proc = proc.replace(
    """<div class="vtw-concl-b">''Who can answer:''&#32;<$text text={{!!ask_who}}/>.&#32;''Why it matters:''&#32;<$transclude field="why" mode="inline"/></div>""",
    """<div class="vtw-concl-b">''Who can answer:''&#32;<$text text={{!!ask_who}}/>.&#32;''Why it matters:''&#32;<$transclude field="why" mode="inline"/></div>""")
proc = proc.replace(
    """<%if [all[current]has[answer]] %><div class="vtw-concl-e">''Answer''<%if [all[current]has[answered_by]] %>&#32;(<$text text={{!!answered_by}}/>)<%endif%>:&#32;<$transclude field="answer" mode="inline"/></div>""",
    """<%if [all[current]has[answer]] %><div class="vtw-concl-e">''Answer''<%if [all[current]has[answered_by]] %>&#32;(<$text text={{!!answered_by}}/><%if [all[current]has[answer_basis]] %>,&#32;<$text text={{!!answer_basis}}/><%endif%>)<%endif%>:&#32;<$transclude field="answer" mode="inline"/></div>""")
put("$:/vtw/procedures", text=proc)

css = cur("$:/vtw/styles")["text"].splitlines()
css = [l for l in css if not l.startswith(".vtw-fix") and not l.startswith("table.vtw-build td")]
css += [
    ".vtw-rb { display: inline-block; padding: 0 0.45em; border-radius: 0.6em; font-size: 0.8em; margin: 0.15em 0.25em 0 0; }",
    ".vtw-rb-specification { background: #dcefe4; }",
    ".vtw-rb-evidence { background: #fff1cc; }",
    ".vtw-rb-incentives { background: #fde2e1; }",
    ".vtw-rb-policy { background: #e8e1f5; }",
    "table.vtw-build td { font-size: 0.93em; }",
    "table.vtw-build td:first-child { width: 32%; }",
    "table.vtw-build td:nth-child(2) { width: 16%; }",
    "table.vtw-chain td:first-child { width: 17%; font-weight: 500; color: #4b6272; }",
    "table.vtw-chain td { font-size: 0.93em; }",
]
put("$:/vtw/styles", text="\n".join(css))

# ------------------------------------------------------------------ 3. mechanism chains (requires) and stories


import re

REF = re.compile(r"(?<![\w-])([A-Za-z][^();,]*?) \(<<r ([A-Z]{2}-\d{2})>>\)")


def dedupe(cell):
    """'Who gets investigated (<<r VD-25>>)' -> '<<r VD-25>>' when the phrase is the record's caption."""
    def sub(m):
        cap = (cur(m.group(2)) if m.group(2) in OUT or m.group(2) in wiki else {}).get("caption", "")
        return f"<<r {m.group(2)}>>" if m.group(1).strip().lower() == cap.strip().lower() else m.group(0)
    return REF.sub(sub, cell)


def chain(rows):
    body = "\n".join(f"<tr><td>{a}</td><td>{dedupe(b)}</td><td>{dedupe(c)}</td></tr>" for a, b, c in rows)
    return ('<table class="vtw-grid vtw-chain"><tbody>\n<tr><th>Step</th><th>What the paper specifies</th><th>Still to build or decide</th></tr>\n'
            + body + "\n</tbody></table>")


CHAINS = {
    "LP-03": [
        ("Purpose", "Anyone can offer services, with no bond and no node cap (<<r RL-07>>, <<r RL-09>>).", "—"),
        ("Inputs", "An address registers and advertises capabilities, regions and prices (<<r RL-08>>).", "Advert format and verification (<<r VD-01>>)."),
        ("Output", "A listing in the onchain registry that agents use for discovery.", "Discovery and routing (<<r VD-02>>)."),
        ("Supporting machinery", "Registry contract.", "Following an actor across addresses after a penalty (<<r VD-27>>)."),
    ],
    "LP-04": [
        ("Purpose", "Tie inflation rewards to real work, limited by stake (<<r RL-03>>, <<r RL-11>>).", "—"),
        ("Inputs", "Node fee share and stake share of network totals; the median honesty score.", "Eligible fees, windows, snapshots and denominators (<<r VD-05>>)."),
        ("Calculation", "Smaller of fee share and stake share, times the median score, times the node emission share (<<r RL-10>>, <<r RL-24>>, <<r RL-54>>).", "One formula reconciling main text and appendix (<<r VD-06>>)."),
        ("Output", "The node's LPT reward for the round, claimable after seven rounds (<<r RL-30>>).", "What happens to unassigned reward (<<r VD-12>>)."),
        ("Supporting machinery", "Fee accounting, staking ledger, score contract, emissions mint.", "Payment attribution (<<r VD-03>>) and the mint schedule (<<r VD-14>>)."),
    ],
    "LP-05": [
        ("Purpose", "Route stake toward productive, understaked nodes; stake also elects validators (<<r RL-16>>, <<r RL-17>>).", "—"),
        ("Inputs", "Delegators' choices; reward and fee cuts offered by operators (<<r RL-15>>).", "Information delegators need to choose well (<<r FR-15>>)."),
        ("Mechanics", "Bonding and cuts as today; stake raises the node's reward ceiling.", "—"),
        ("Output", "Stake per node, which sets reward ceilings and validator eligibility.", "—"),
        ("Supporting machinery", "Staking contract; 21-round unbonding (<<r RL-27>>).", "Whether and when stake can move between nodes (<<r VD-13>>)."),
    ],
    "LP-06": [
        ("Purpose", "Put judging with the highest-staked nodes, making the set expensive to capture.", "—"),
        ("Inputs", "Total stake per node and opt-in registrations (<<r RL-19>>).", "Snapshots and ranking population (<<r VD-08>>)."),
        ("Selection", "Top N by stake among those who opt in, N proposed at 33; the next registered node fills a decline (<<r RL-20>>, <<r RL-21>>).", "Ties and vacancies (<<r VD-08>>)."),
        ("Output", "The active validator set, which shares a validator slice of new LPT (<<r RL-22>>, <<r RL-55>>).", "Equal or stake-weighted split, and any participation condition (<<r VD-17>>)."),
        ("Supporting machinery", "Registry, staking ledger, score contract.", "Independence and conflicts (<<r VD-29>>)."),
    ],
    "LP-07": [
        ("Purpose", "Deny rewards for dishonest work: self-dealing, fee fabrication, incorrect results. Not a service-quality grade (<<r RL-25>>).", "—"),
        ("Evidence collection", "Testing, monitoring and anomaly detection funded as a public good (<<r RL-26>>).", "Who gets investigated (<<r VD-25>>), evidence standards (<<r VD-26>>), funding and oversight (<<r VD-28>>)."),
        ("Assessment", "Validators vote on published evidence or other surfaced criteria.", "Criteria and proof standard (<<r VD-09>>), outage versus dishonesty (<<r VD-23>>), correctness (<<r VD-22>>)."),
        ("Finding to score", "Each active validator scores each node from 0 to 1 (<<r RL-23>>).", "Mapping from a finding to a number (<<r VD-09>>)."),
        ("Aggregation", "The median of active validators' scores (<<r RL-24>>).", "Quorum, abstention and recusal (<<r VD-10>>); independence (<<r VD-29>>)."),
        ("Consequence", "The median scales the MFS reward, read at claim time (<<r RL-31>>).", "Finality and appeal (<<r VD-11>>, <<r VD-21>>)."),
    ],
    "LP-08": [
        ("Purpose", "Make capital lockup a real deterrent to hit-and-run behaviour.", "—"),
        ("Rule", "21-round unbonding for all stake behind a node (<<r RL-27>>); bond transfer removed or delayed (<<r RL-28>>, <<r RL-29>>).", "Which option (<<r VD-13>>)."),
        ("Output", "Stake locked for 21 rounds. Rewards can be reduced; principal is not slashed.", "—"),
        ("Supporting machinery", "Staking contract.", "Whether a penalty follows the actor or only the address (<<r VD-27>>)."),
    ],
    "LP-09": [
        ("Purpose", "Give validators time to catch a single-round fee spike before rewards can be claimed.", "—"),
        ("Rule", "Rewards for round n become claimable at n+7 (<<r RL-30>>).", "Claim deadline and finality (<<r VD-11>>)."),
        ("Inputs", "Round counter; the median score at the time of claiming (<<r RL-31>>).", "Which median applies (<<r VD-07>>)."),
        ("Output", "A claimable reward at the then-current score.", "A score snapshot per earning round (<<r VD-11>>)."),
        ("Supporting machinery", "Investigation within the window.", "Who gets investigated (<<r VD-25>>)."),
    ],
    "LP-10": [
        ("Purpose", "Price in USD and pay in USDC, removing ETH volatility from fees (<<r RL-32>>).", "—"),
        ("Inputs", "Customer payments.", "Payment security with unlimited nodes (<<r RL-61>>)."),
        ("Output", "Settled USDC fees attributed to nodes.", "Attribution, reversals and accounting periods (<<r VD-03>>)."),
    ],
    "LP-11": [
        ("Purpose", "Tie LPT value to usage by buying and burning LPT with part of each fee (<<r RL-46>>).", "—"),
        ("Inputs", "Settled USDC fees.", "Settlement and attribution (<<r VD-03>>)."),
        ("Calculation", "50% to the node, 50% buys LPT; all purchased LPT is burned (<<r RL-33>>, <<r RL-34>>, <<r RL-36>>).", "Split viability (<<r VD-15>>); denominators if the burn is ever below 100% (<<r VD-16>>)."),
        ("Output", "Node USDC receipt; LPT burned. Rewards come from a separate mint (<<r RL-40>>).", "—"),
        ("Supporting machinery", "DEX buyback with illustrative TWAP, frequency and slippage parameters (<<r RL-43>>, <<r RL-44>>, <<r RL-45>>).", "Execution design (<<r VD-18>>)."),
    ],
    "LP-12": [
        ("Purpose", "Predictable issuance that reaches equilibrium with the burn (<<r RL-46>>).", "—"),
        ("Inputs", "Network fees for concepts 1 and 2; participation for concept 3; an LPT price for USD targets.", "Price source (<<r VD-14>>, <<r RL-62>>)."),
        ("Calculation", "Three concepts (<<r RL-47>>, <<r RL-48>>, <<r RL-49>>). Concept 1: emissions a declining multiple of fees, halving every two years, with a proposed annual cap (<<r RL-50>>).", "Which concept, period alignment and a zero-fee rule (<<r VD-14>>)."),
        ("Output", "LPT minted per period, split among nodes, validators and treasury (<<r RL-53>>).", "—"),
        ("Supporting machinery", "Price oracle and mint contract.", "An oracle that resists manipulation (<<r VD-14>>)."),
    ],
    "LP-13": [
        ("Purpose", "Split each round's emissions among nodes, validators and the treasury (<<r RL-53>>).", "—"),
        ("Calculation", "94% nodes, 1% validators, 5% treasury (<<r RL-54>>, <<r RL-55>>, <<r RL-56>>).", "How the validator slice is divided (<<r VD-17>>)."),
        ("Output", "The node envelope used by MFS; validator and treasury envelopes.", "What happens to node reward MFS leaves unassigned (<<r VD-12>>)."),
    ],
    "LP-14": [
        ("Purpose", "Keep parameters adjustable and the scoring mechanism replaceable (<<r RL-05>>).", "—"),
        ("Decision", "Governance adjusts parameters and can swap the score contract address (<<r RL-57>>).", "Separation of policy from case decisions (<<r VD-21>>); the validator constitution (<<r RL-65>>)."),
        ("Output", "Parameter values and the active score contract.", "—"),
    ],
}

OLD_HEAD = ('<div class="vtw-storynote">Mechanism story, drafted by an agent from the records below. Edit it freely, or '
            '<$link to="View: Contributor notes">leave a note</$link> if you think it is wrong.</div>')
NEW_HEAD = ('<div class="vtw-storynote">Mechanism story, drafted by an agent from the records below. Edit it freely, or '
            '<$link to="View: Contributor notes">leave a note</$link> where it is wrong.</div>')

for lp, rows in CHAINS.items():
    put(lp, requires=chain(rows))
    t = cur(lp)
    if t.get("story_status"):
        pairs = [
            (OLD_HEAD, NEW_HEAD),
            ("<h3>What the paper gives us</h3>", "<h3>What the paper specifies</h3>"),
            ("<h3>What it leaves to be built</h3>", '<h3>How it works end to end</h3>\n<$transclude field="requires" mode="block"/>\n<h3>What it leaves to be built</h3>'),
            ("<h3>What we suspect, and how we will check</h3>", "<h3>Working hypothesis and how it will be tested</h3>"),
        ]
        replace_in(lp, "text", pairs)
    else:
        put(lp, text=f"""<div class="vtw-storynote">No story drafted yet. The chain below is drawn from the records.</div>

<div class="vtw-story">
<h3>How it works end to end</h3>
<$transclude field="requires" mode="block"/>
<h3>What it leaves to be built</h3>
<$transclude $variable="vtw-buildlist" lp="{lp}"/>
</div>""")

replace_in("LP-07", "text", [
    ("The worry is that the score becomes a court without a record. This is a hypothesis.",
     "The concern is that scoring becomes a court without a record. This is a hypothesis, and the evidence may narrow or reject it."),
    ("M2.2 decides, piece by piece, whether a written rule closes each gap or whether some would remain under any rule.",
     "M2.2 records, piece by piece, what would resolve each gap, and whether plausible completions of the paper leave any concern unresolved."),
])
replace_in("LP-04", "text", [
    ("The fee share is also where the non-computable question enters:",
     "This is the clearest case of an exact calculation that may still reward the wrong behaviour. The fee share is also where the non-computable question enters:"),
])

# ------------------------------------------------------------------ 4. steps

replace_in("Orientation", "starting_point", [
    ("We begin with nothing but the Livepeer 2.0 litepaper", "The starting point is the Livepeer 2.0 litepaper alone"),
    ("We treat every value as a proposal, not a decision.", "Every value is treated as a proposal, not a decision."),
])

put("M1.1", starting_point="""The orientation gave a clear picture of how the paper wants money and rewards to move, and a long list of rules it has not written yet. That list is not a criticism. A litepaper sets out an architecture; the rules come later. So this step does not ask what the paper omitted. It asks what each mechanism needs in order to work, and what ''kind'' of thing each missing piece is.

The kind matters because it decides how a disagreement would be settled. If a piece is arithmetic, anyone can check the answer. If it needs someone to look at the world, the answer is only as good as what they can see. If it needs someone to make a call, the answer can be argued with. None of this says whether the mechanism rewards the right behaviour; that question runs alongside and is taken up at the end of this step.""")

ONLY_DG = "[tag[VD]!field:status[split]] :filter[get[classification]split[+]remove[D G]count[]match[0]]"
HAS_E = "[tag[VD]!field:status[split]] :filter[get[classification]split[+]match[E]]"
HAS_J = "[tag[VD]!field:status[split]] :filter[get[classification]split[+]match[J]]"
HAS_J_LP07 = "[tag[VD]!field:status[split]contains:concepts[LP-07]] :filter[get[classification]split[+]match[J]]"
ALL_VD = "[tag[VD]!field:status[split]]"
MECHS = "LP-03 LP-04 LP-05 LP-06 LP-07 LP-08 LP-09 LP-10 LP-11 LP-12 LP-13 LP-14"
NEW_VD = "VD-23 VD-24 VD-25 VD-26 VD-27 VD-28 VD-29"

put("M1.1", text=f"""<div class="vtw-step">
<h3>Four kinds of requirement</h3>
<p>Every open piece in the paper needs one or more of these:</p>
<ul>
<li>''A formula.'' Arithmetic over numbers the protocol already holds: stake balances, settled fees, round counters.</li>
<li>''Data from outside the protocol.'' Someone has to observe something the chain cannot see, such as whether a job was delivered.</li>
<li>''A judgment.'' Someone has to interpret incomplete evidence or intent, such as whether a payment was self-dealing.</li>
<li>''A policy choice.'' Governance picks a rule once. After that, the rule can usually be computed.</li>
</ul>
<p>AI media work adds one more consideration: many outputs legitimately vary between runs, so "correct" has to allow for that. Variable output does not by itself make work unverifiable; some properties can be checked without reproducing the same result.</p>
<p>One piece can need several of these. The median of validator scores is a formula, but every score it takes in is a judgment.</p>
</div>

<div class="vtw-step">
<h3>Each mechanism, end to end</h3>
<p>Each mechanism below is laid out from purpose to output, showing what the paper already specifies next to what is still to build or decide. Under each chain, every open piece records what it needs, what a specification would settle, and what would still need testing afterwards. The classification in the last columns is an agent's first proposal until someone reviews it. The story of each mechanism is on its own page (<<r "View: Mechanism stories">>).</p>
<$list filter="{MECHS}" variable="lp">
<details class="vtw-details vtw-mech"><summary><$text text={{{{{{ [<lp>get[caption]] }}}}}}/>&#32;·&#32;<$count filter="[tag[VD]!field:status[split]contains:concepts<lp>]"/>&#32;open&#32;·&#32;<$count filter="[tag[VD]!field:status[split]contains:concepts<lp>contains:resolved_by[evidence]]"/>&#32;need evidence&#32;·&#32;<$count filter="[tag[VD]!field:status[split]contains:concepts<lp>contains:resolved_by[incentives]]"/>&#32;need incentive analysis</summary>
<$transclude tiddler=<<lp>> field="requires" mode="block"/>
<$transclude $variable="vtw-buildlist" lp=<<lp>>/>
</details>
</$list>
</div>

<div class="vtw-step">
<h3>Much of the money arithmetic can be written down</h3>
<p>The fee split, the burn, the emission shares, the MFS minimum, the median and the delay counters are all arithmetic (<<r RL-10>>, <<r RL-24>>, <<r RL-35>>, <<r RL-53>>). What they wait on is policy: measurement windows, what happens to reward that MFS leaves unassigned, when a round becomes final. None of that needs anyone to observe the world.</p>
<div class="vtw-data"><$count filter="{ONLY_DG}"/>&#32;of the&#32;<$count filter="{ALL_VD}"/>&#32;open pieces need nothing more than a formula and a policy choice:&#32;<$list filter="{ONLY_DG} +[sort[title]]" join=", "><$link><$text text={{{{!!caption}}}}/></$link></$list>.</div>
<div class="vtw-leadsto">Leads to: <<r CN-07>></div>
</div>

<div class="vtw-step">
<h3>The rest needs an observation or a judgment</h3>
<p>The other pieces cannot be settled by arithmetic, however carefully it is written. Someone has to observe what happened, or interpret what it meant.</p>
<div class="vtw-data"><$count filter="{HAS_E}"/>&#32;open pieces need data from outside the protocol.&#32;<$count filter="{HAS_J}"/>&#32;need a judgment. The judgments:&#32;<$list filter="{HAS_J} +[sort[title]]" join=", "><$link><$text text={{{{!!caption}}}}/></$link></$list>.</div>
</div>

<div class="vtw-step">
<h3>The judgments gather around one mechanism</h3>
<p>In this inventory, nearly every piece that needs a judgment feeds the honesty score (<<r LP-07>>): what counts as dishonest, what evidence is enough, who scores whom, and when a score is final. The paper describes reward eligibility as "inherently subjective" (litepaper line 83).</p>
<p>Many of these judgments are adversarial by design. Validators are operators, so lowering a score means one operator finding against another, sometimes a competitor.</p>
<div class="vtw-data"><$count filter="{HAS_J_LP07}"/>&#32;of the&#32;<$count filter="{HAS_J}"/>&#32;pieces that need a judgment concern the honesty score. Counts reflect how the inventory divides the paper into records, not how much of the design is subjective.</div>
<div class="vtw-leadsto">Leads to: <<r CN-08>></div>
</div>

<div class="vtw-step">
<h3>Seven pieces the first pass had not listed</h3>
<p>An earlier inventory (<<r SRC-MECHMAP>>) listed every place the paper needs outside evidence or a call. Checked against the records, seven had no record of their own. They are added here as open decisions. Each one is a judgment or evidence question, and six of the seven concern the honesty score.</p>
<div class="vtw-data"><$list filter="{NEW_VD}" join=" · "><$link><$text text={{{{!!caption}}}}/></$link></$list></div>
</div>

<div class="vtw-step">
<h3>Computable is not the same as sound</h3>
<p>Sorting pieces by what they need shows how a result would be reached. It does not show whether the result rewards the behaviour the network wants. A fully specified MFS formula under a fee-linked emissions rule computes exactly, and may still make it profitable for a party to pay its own node for real work (<<r FR-01>>, <<r FR-23>>). No uncertainty in the calculation is involved.</p>
<p>The reverse also holds: a mechanism that depends on judgment can work if its evidence, incentives, error costs and authority are adequate. For both reasons, every mechanism goes to M2.1, including those that need nothing more than a formula.</p>
<div class="vtw-leadsto">Leads to: <<r CN-09>></div>
</div>""")

replace_in("M1.2", "question", [("what information would settle it, who holds that information today, and could it be faked or hidden?",
    "what information would settle it, who holds that information today, what that information can actually establish, and could it be faked or hidden?")])
replace_in("M1.2", "text", [
    ("write down in plain words: what information would settle it; who holds that information today; whether it could be faked, withheld or hidden; and what it would cost to collect.",
     "write down in plain words: what information would settle it; who holds that information today; what the observations can actually establish, as distinct from what they record; whether they could be faked, withheld or hidden; and what they would cost to collect."),
    ("An early reading, still to be tested, is that the first few can be observed with the right records and the last two may not be observable by anyone.",
     "A working hypothesis, tested in this step, is that the first few can be observed with the right records and the last two may not be observable by anyone."),
    ("<h3>What only practitioners can tell us</h3>", "<h3>What practitioner experience can add</h3>"),
])
put("M1.3", starting_point="""M1.2 establishes which facts can be observed and what they can establish. This step puts participants back into the picture. A judgment made on good evidence by someone with no stake in the outcome is one thing. A judgment made on thin evidence, about a competitor, by someone whose own rewards depend on the same scores, is another.

This step tests the first concern stated on the Home page: that some reward decisions ask operators to find against one another on evidence that cannot reliably distinguish abuse from legitimate activity. Where the data map finds adequate evidence for a judgment, the concern does not apply to it, and that result carries the same weight as any other.""")
replace_in("M1.3", "text", [("<h3>What only practitioners can tell us</h3>", "<h3>What practitioner experience can add</h3>")])

put("M2.1", starting_point="""M1 hands over three things: what can be computed, what information exists, and which judgments are asked of whom. This step assumes the missing rules have been written, under a stated reading, and asks how participants would actually behave.

This applies to every mechanism, including those that need nothing more than a formula, because a fully specified rule can still reward the wrong behaviour. It also applies to validators. The paper treats scoring as a duty that validators will carry out honestly. This step asks what a validator gains or loses from scoring carefully, scoring everyone 1.0, or coordinating with others, and likewise for operators, delegators and anyone paying for jobs.""")
replace_in("M2.1", "text", [("<h3>What only practitioners can tell us</h3>", "<h3>What practitioner experience can add</h3>")])

put("M2.2", caption="What would resolve each concern?",
    question="For each open piece and finding, what would resolve it: a specification, better evidence, a change in incentives or a policy choice? Which concerns do plausible completions of the paper leave unresolved?",
    starting_point="""Every open piece and finding is classified by what would resolve it. A piece that a specification alone resolves goes on the list of things to build and says nothing against the paper. A piece that needs evidence or incentive analysis is investigated. A piece that needs a policy choice is put to the people and processes that make that choice, with its tradeoffs laid out.

A concern is carried forward to M3 only when plausible completions of the paper, compared on their tradeoffs, leave it unresolved. That does not require showing that every conceivable rule fails. It requires showing, with evidence, why the plausible ones fall short.

Classifications start as agent proposals. Review confirms or changes a classification; it does not replace the evidence behind it.""",
    text="""<div class="vtw-step">
<h3>A specification alone would resolve these</h3>
<div class="vtw-data"><$transclude $variable="vtw-buildtable" filter="[tag[VD]field:resolved_by[specification]sort[title]] [tag[FR]field:resolved_by[specification]sort[title]]"/></div>
</div>

<div class="vtw-step">
<h3>Need better evidence</h3>
<div class="vtw-data"><$transclude $variable="vtw-buildtable" filter="[tag[VD]contains:resolved_by[evidence]sort[title]] [tag[FR]contains:resolved_by[evidence]sort[title]]"/></div>
</div>

<div class="vtw-step">
<h3>Need incentive analysis</h3>
<p>These may be fully specifiable and still reward the wrong behaviour. Each goes through M2.1.</p>
<div class="vtw-data"><$transclude $variable="vtw-buildtable" filter="[tag[VD]contains:resolved_by[incentives]sort[title]] [tag[FR]contains:resolved_by[incentives]sort[title]]"/></div>
</div>

<div class="vtw-step">
<h3>Need a policy choice</h3>
<p>These depend on what the network wants. The research lays out the tradeoffs; the decision belongs to the people and processes that set policy.</p>
<div class="vtw-data"><$transclude $variable="vtw-buildtable" filter="[tag[VD]contains:resolved_by[policy]sort[title]] [tag[FR]contains:resolved_by[policy]sort[title]]"/></div>
</div>""")

# ------------------------------------------------------------------ 5. conclusions

put("CN-07", caption="Much of the money arithmetic can be written down today",
    statement="The fee split, the burn, the emission shares, the MFS minimum, the median and the delay counters are arithmetic. They wait on policy choices, such as measurement windows, what happens to unassigned reward and when a round is final, but not on information from outside the protocol. Being computable does not make them sound: each still has to be checked for the behaviour it rewards.",
    basis="Six of the open decisions need only a formula and a policy choice, so they can be specified and then tested with small worked examples. A fully specified fee-linked formula may still reward self-payment (FR-01), so specification alone is not the test.",
    findings="FR-01")
put("CN-08",
    statement="In this inventory, nearly every piece that needs a judgment feeds the honesty score: what counts as dishonest, what evidence is enough, who scores whom and when a score is final. Many of these judgments are adversarial by design, because validators are operators and lowering a score means one operator finding against another.",
    basis="Of the decisions that need a judgment, all but one (VD-27, returning under a new identity) list the honesty score among their concepts. The count reflects how the inventory is divided into records. The paper itself describes reward eligibility as inherently subjective (line 83).")
put("CN-09", caption="Specifying a rule settles how a result is reached, not whether it works",
    statement="A written rule settles how a result is computed or how a procedure runs. It does not supply information nobody can observe, and it does not show that the result rewards the intended behaviour. Each open piece therefore records what a specification would settle and what would still need testing: evidence, incentives, cost or effectiveness.",
    basis="The first, unreviewed classification finds pieces that a specification alone resolves, pieces that also need evidence, and pieces whose incentives need testing even when fully specified, such as the fee split and the treatment of unassigned reward (VD-15, VD-12).",
    carried_to="M1.2 M2.1 M2.2", decisions="VD-05 VD-12 VD-15 VD-09 VD-19")

# ------------------------------------------------------------------ 6. pages

put("Home", text=r"""<div class="vtw-home">
<p class="vtw-lede">This workbench follows one line of inquiry into the Livepeer 2.0 litepaper, from a first reading to evidence. It is written so that people who run nodes, delegate, validate or build on Livepeer can follow the reasoning, check it and contribute to it.</p>

<h2>The concerns under test</h2>
<p>Some of the litepaper is arithmetic: split a fee, compare two shares, take a median, count rounds. Given the same inputs, anyone can reproduce the result.</p>
<p>Other parts cannot be computed. They need an observation of the world or a judgment. Many of those judgments are adversarial by design. Validators are themselves operators, and the paper asks them to identify self-dealing, fabricated fees and incorrect results among other operators, some of them competitors.</p>
<p>''The first concern'' is that some reward decisions may require competing operators to judge one another using evidence that cannot reliably distinguish abuse from legitimate activity. Where that holds, acting on weak evidence risks penalizing honest operators, and declining to act lets abuse through. Both outcomes carry a cost in trust between participants.</p>
<p>''The second concern'' is that exact computation does not guarantee sound incentives. A fully specified, fee-linked reward could make it profitable for a party to pay its own node for real work, with no uncertainty anywhere in the calculation.</p>
<p>The path tests where these concerns apply, where clearer rules or better evidence resolve them, and what the remaining decisions cost. The evidence may support, narrow or reject either concern. Two rules keep the inquiry fair to the paper:</p>
<ul class="vtw-rules">
<li>''Missing detail is not an argument.'' A litepaper sets out an architecture. An unwritten rule is recorded as something to build, not as a fault in the paper.</li>
<li>''Each concern is classified by what would resolve it:'' a specification, better evidence, a change in incentives or a policy choice. A concern is carried forward as a reason to change the design only when plausible completions of the paper, compared on their tradeoffs, leave it unresolved.</li>
</ul>

<h2>How to take part</h2>
<ul class="vtw-rules">
<li>''Read a mechanism story.''&#32;Each one follows a single mechanism from purpose to open questions:&#32;<$link to="View: Mechanism stories">Mechanism stories</$link>. Corrections are welcome.</li>
<li>''Answer a question that needs practitioner experience.''&#32;<$link to="View: Questions for humans">Questions for humans</$link>&#32;(<$count filter="[tag[HQ]field:status[open]]"/>&#32;open).</li>
<li>''Leave a note about anything.''&#32;<$link to="View: Contributor notes">Contributor notes</$link>. No knowledge of the record system is needed; an agent files notes into records and links back to them.</li>
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
<p><$count filter="[tag[VD]!field:status[split]]"/>&#32;open pieces are recorded. In the first, unreviewed classification,&#32;<$count filter="[tag[VD]field:resolved_by[specification]]"/>&#32;can be resolved by a specification alone,&#32;<$count filter="[tag[VD]contains:resolved_by[evidence]]"/>&#32;need better evidence,&#32;<$count filter="[tag[VD]contains:resolved_by[incentives]]"/>&#32;need incentive analysis and&#32;<$count filter="[tag[VD]contains:resolved_by[policy]]"/>&#32;involve a policy choice. A piece can fall under more than one. The counts describe how this inventory divides the paper into records; they do not measure how much of the design is sound (<$link to="M2.2">register</$link>).</p>
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

put("View: Questions for humans", description="Questions that need practitioner experience, and policy choices",
    text=r"""<p class="vtw-lede">Some things in this research cannot be settled by reading the paper or the code. They need experience from people who run nodes, delegate, operate gateways, validate or build apps. Answers are cited as evidence, with their context.</p>
<p>To answer, press ''Answer this'', fill in ''answer'' and ''answered by'', set ''answer basis'' to observed (seen in practice), expected (anticipated for a future system) or both, and set ''status'' to answered. A <$link to="View: Contributor notes">note</$link> works too.</p>
<h2>Questions for people who run the network</h2>
<$list filter="[tag[HQ]field:status[open]sort[title]]" emptyMessage="<p class='vtw-none'>No open questions.</p>"><<vtw-hqcard>></$list>
<h2>Policy choices</h2>
<p>These pieces depend on what the network wants, so evidence alone cannot settle them. The research lays out the tradeoffs; the decision belongs to the people and processes that set policy.</p>
<$transclude $variable="vtw-buildtable" filter="[tag[VD]contains:resolved_by[policy]sort[title]]"/>
<h2>Reviewing classifications</h2>
<p>An agent classified every open piece by what would resolve it. Anyone who knows an area can review a classification: confirm or change ''resolved by'', ''spec settles'' and ''still to test'', and add a name in ''reviewed by''. A review checks the classification. It is not evidence for or against a concern; pieces that need evidence are investigated.</p>
<p><$count filter="[tag[VD]has[resolved_by]!has[reviewed_by]]"/>&#32;classifications have not been reviewed yet. The full list is in the&#32;<$link to="M2.2">register</$link>.</p>
<h2>Answered</h2>
<$list filter="[tag[HQ]field:status[answered]sort[title]]" emptyMessage="<p class='vtw-none'>None yet.</p>"><<vtw-hqcard>></$list>""")

replace_in("View: Mechanism stories", "text", [
    ("One page per mechanism, told end to end: what the paper gives us, what it leaves to be built, what we suspect, and where it goes next. Agents draft them from the records; people edit them. If a story is wrong, fix it or leave a note.",
     "One page per mechanism, told end to end: what the paper specifies, how the mechanism works from purpose to output, what it leaves to be built, the working hypothesis and how it will be tested, and where it goes next. Agents draft the stories from the records; people edit them. Corrections can be made directly or left as a note."),
    ('&#32;open pieces ·&#32;<$count filter="[tag[VD]!field:status[split]contains:concepts<currentTiddler>field:fix_by_rule[unsure]]"/>&#32;for a human call ·',
     '&#32;open pieces ·&#32;<$count filter="[tag[VD]!field:status[split]contains:concepts<currentTiddler>contains:resolved_by[evidence]]"/>&#32;need evidence ·'),
])

replace_in("$:/vtw/ui/SideBarViews", "text", [
    ('(<$count filter="[tag[HQ]field:status[open]] [tag[VD]field:fix_by_rule[unsure]]"/>)', '(<$count filter="[tag[HQ]field:status[open]]"/>)'),
])
replace_in("$:/vtw/ui/RecordRollup", "text", [
    ('label="What we concluded"', 'label="Conclusions"'),
    ('label="What we assume, infer or suspect"', 'label="Assumptions, inferences and hypotheses"'),
])

conv = cur("Conventions")["text"]
a = conv.index("<h2>How the path is organized</h2>")
b = conv.index("<h2>Record types</h2>")
conv = conv[:a] + r"""<h2>How the path is organized</h2>
<p>The path follows one chain of reasoning: how the paper works; what each mechanism needs and what the protocol can compute on its own; where the data for the rest would come from and what it can establish; who is asked to judge what; how participants would behave once the rules were written; and what would resolve each concern. Each step is written as prose for people, with records as its evidence, and ends in conclusions the next step starts from.</p>
<ul>
<li>''Missing detail is not a finding.'' A missing rule becomes something to build. Record it as an open decision, never as a fault in the paper.</li>
<li>''Computable is not the same as sound.'' A fully specified rule can still reward the wrong behaviour, so every mechanism is examined for incentives, including pure arithmetic.</li>
<li>''What would resolve it.'' Every open decision, and in M2 every finding, carries ''resolved_by'' (specification, evidence, incentives, policy), ''spec_settles'' and ''still_to_test''. Agents propose; a person who reviews the classification adds their name in ''reviewed_by''. Review checks the classification; evidence comes from investigation.</li>
<li>''The bar for change.'' A concern is carried to M3 only when plausible completions of the paper, compared on their tradeoffs, leave it unresolved.</li>
<li>''One mechanism, one story.'' Each mechanism's page carries a chain from purpose to output (''requires'') and a story that follows it through every step. Agents keep them in step with the records; people edit them.</li>
<li>''Plain words for people.'' The labels D, E, J, G and S stay in record fields. Anything a person reads says "a formula", "data from outside the protocol", "a judgment", "a policy choice" or "outputs that vary by nature".</li>
<li>''Counts describe the inventory.'' A count of records says how the paper has been divided into records, not how much of the design is sound or subjective.</li>
<li>''People can contribute without the schema.'' Contributor notes (tag Note) are free text; an agent files each one into records and lists them in ''filed_as''. Questions for humans (HQ) collect what only practitioners can answer; answers record whether they are observed or expected.</li>
</ul>

""" + conv[b:]
conv = conv.replace("<h2>Writing rules</h2>\n<ul>\n",
    "<h2>Writing rules</h2>\n<ul>\n<li>Write in a neutral, impersonal voice. No first person (I, we, our, us) and no named author in the narrative. Address the reader as \"you\" only in instructions and in questions put to practitioners.</li>\n", 1)
if "neutral, impersonal voice" not in conv:
    sys.exit("Conventions: writing rules list not found")
put("Conventions", text=conv)

json.dump(list(OUT.values()), sys.stdout, indent=1, ensure_ascii=False)
print(f"{len(OUT)} tiddlers", file=sys.stderr)
