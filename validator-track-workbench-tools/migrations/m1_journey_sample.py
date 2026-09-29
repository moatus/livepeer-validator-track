"""Sample: research-path (journey) layer and reader view.

Adds conclusion records (CN), the milestone path, journey templates, a reader/
editor toggle, a reader layout for records, a new Home, the M1.1 journey and
an LP-04 overview. Reads the current wiki so edits to existing tiddlers keep
their other fields. Usage: python3 m1_journey_sample.py WIKI > sample.json
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

VTW = Path(__file__).resolve().parents[1] / "vtw.py"
wiki = {t["title"]: t for t in json.loads(subprocess.check_output([sys.executable, str(VTW), "export", sys.argv[1]]))}
OUT = []


def put(title, **fields):
    t = dict(wiki.get(title, {"title": title}))
    for k in ("created", "modified", "modifier"):
        t.pop(k, None)
    for k, v in fields.items():
        k = k.replace("__", "-")
        if v is None:
            t.pop(k, None)
        else:
            t[k] = v.strip("\n") if isinstance(v, str) else v
    OUT.append(t)


def dict_add(title, entries):
    lines = wiki[title]["text"].splitlines()
    keys = {l.split(":", 1)[0].strip() for l in lines if ":" in l}
    lines += [f"{k}: {v}" for k, v in entries.items() if k not in keys]
    put(title, text="\n".join(lines))


# ------------------------------------------------------------------ schema and vocabulary

put("$:/vtw/schema/CN", text="One conclusion a milestone step reaches, in plain language, with the records it rests on and the steps it is carried to.",
    record_type="CN", name="Conclusion", plural="Conclusions", id__pattern=r"^CN-\d{2}$", required__tags="Record CN",
    display="caption status statement basis task carried_to provisions decisions claims findings scenarios experiments concepts participants related introduced_by last_changed_by",
    required="caption status statement basis task carried_to concepts stage introduced_by",
    vocab__status="supported-by-text inference hypothesis", summary="statement", needs__concepts="yes", tags="")
put("CN", text="<<vtw-type-index>>", caption="Conclusions")
put("$:/vtw/path", text="The research path, in order. Each step starts from the conclusions carried into it.", list="M1.1 M1.2 M1.3 M1.4 M2")
put("$:/config/vtw/mode", text="reader")
dict_add("$:/vtw/fields", {
    "overview": "Plain-language summary for readers: what it does, why it matters, what is open. Concepts only.",
    "starting_point": "Journey steps: what we knew or assumed going in, in prose.",
    "basis": "Conclusions: why the evidence supports the statement, in two or three sentences.",
    "task": "Conclusions: the path step that reached it.",
    "carried_to": "Conclusions: later path steps that take it as their starting point.",
})

# ------------------------------------------------------------------ procedures (reader layer)

procs = wiki["$:/vtw/procedures"]["text"] + r'''

\function vtw.reader() [[$:/config/vtw/mode]get[text]else[reader]match[reader]]

\procedure r(id)
<$link to=<<id>> tooltip=<<id>>><$text text={{{ [<id>get[caption]else<id>] }}}/></$link>
\end

\procedure vtw-mode-toggle()
<$let m={{{ [[$:/config/vtw/mode]get[text]else[reader]] }}}>
<$button class="vtw-toggle" set="$:/config/vtw/mode" setTo={{{ [<m>match[reader]then[editor]else[reader]] }}} tooltip="Reader view hides record fields and IDs; editor view shows everything">
<%if [<m>match[reader]] %>Reader view · show record details<%else%>Editor view · switch to reader<%endif%>
</$button>
</$let>
\end

\procedure vtw-readlist(filter)
<ul class="vtw-read">
<$list filter=<<filter>>>
<li><$link><$text text={{{ [all[current]get[caption]else<currentTiddler>] }}}/></$link>
&#32;<span class="vtw-idsmall"><$text text=<<currentTiddler>>/><%if [all[current]has[status]] %>&#32;·&#32;<$text text={{!!status}}/><%endif%></span>
<$let sf={{{ [[$:/vtw/schema/]addsuffix{!!record_type}get[summary]] }}}><%if [all[current]get<sf>!is[blank]] %><div class="vtw-readsum"><$transclude field=<<sf>> mode="inline"/></div><%endif%></$let>
</li>
</$list>
</ul>
\end

\procedure vtw-section(label, filter)
<%if [subfilter<filter>] %>
<div class="vtw-rsec"><h3><$text text=<<label>>/></h3><$transclude $variable="vtw-readlist" filter=<<filter>>/></div>
<%endif%>
\end

\procedure vtw-fieldtable()
<table class="vtw-fields"><tbody>
<$list filter="[<schema>get[display]enlist-input[]] -caption -status" variable="f">
<%if [all[current]get<f>!is[blank]] %>
<tr>
<th title={{{ [[$:/vtw/fields]getindex<f>] }}}><$text text={{{ [<f>search-replace:g[_],[ ]] }}}/></th>
<td>
<%if [[$:/vtw/relations]indexes[]match<f>] %><$transclude $variable="vtw-refs" field=<<f>>/>
<%else%><$transclude field=<<f>> mode="inline"/>
<%endif%>
</td>
</tr>
<%endif%>
</$list>
</tbody></table>
\end

\procedure vtw-conclusion-card()
<div class="vtw-concl">
<div class="vtw-concl-h"><$link><$text text={{!!caption}}/></$link>&#32;<span class=`vtw-status vtw-st-${[{!!status}]}$`><$text text={{!!status}}/></span></div>
<div class="vtw-concl-s"><$transclude field="statement" mode="inline"/></div>
<div class="vtw-concl-b">''Why:''&#32;<$transclude field="basis" mode="inline"/></div>
<div class="vtw-concl-e">''Rests on:''&#32;<$list filter="[all[current]get[findings]enlist-input[]] [all[current]get[decisions]enlist-input[]] [all[current]get[experiments]enlist-input[]] [all[current]get[claims]enlist-input[]] [all[current]get[provisions]enlist-input[]] [all[current]get[scenarios]enlist-input[]]" variable="e" join=" · "><$transclude $variable="r" id=<<e>>/></$list></div>
</div>
\end
'''
put("$:/vtw/procedures", text=procs)

# ------------------------------------------------------------------ record templates (reader and editor)

put("$:/vtw/ui/RecordHeader", text=r'''
\whitespace trim
<%if [all[current]has[record_type]] -[all[current]prefix[$:/]] %>
<$let schema={{{ [[$:/vtw/schema/]addsuffix{!!record_type}] }}}>
<div class="vtw-header">
<div class="vtw-kicker"><$link to={{!!record_type}}><$text text={{{ [<schema>get[name]] }}}/></$link>&#32;·&#32;<$text text={{!!stage}}/>&#32;<<vtw-status>></div>
<div class="vtw-title"><$text text={{!!caption}}/></div>
<%if [function[vtw.reader]] %>
<%if [all[current]has[overview]] %>
<div class="vtw-overview"><$transclude field="overview" mode="block"/></div>
<%if [all[current]has[in_paper]] %><div class="vtw-inpaper">''In the paper''&#32;(<$text text={{!!source_ref}}/>):&#32;<$transclude field="in_paper" mode="inline"/></div><%endif%>
<%else%>
<div class="vtw-overview"><$transclude field={{{ [<schema>get[summary]] }}} mode="inline"/></div>
<%if [all[current]has[basis]] %><div class="vtw-inpaper">''Why:''&#32;<$transclude field="basis" mode="inline"/></div><%endif%>
<%endif%>
<details class="vtw-details"><summary>Record details</summary><<vtw-fieldtable>></details>
<%else%>
<<vtw-fieldtable>>
<%endif%>
</div>
</$let>
<%endif%>
''')

put("$:/vtw/ui/RecordRollup", text=r'''
\whitespace trim
<%if [all[current]has[record_type]] -[all[current]prefix[$:/]] %>
<$let id=<<currentTiddler>>>
<%if [function[vtw.reader]] %>
<%if [all[current]tag[LP]] %>
<$transclude $variable="vtw-section" label="What we concluded" filter="[tag[CN]contains:concepts<id>sort[title]]"/>
<$transclude $variable="vtw-section" label="What the paper says" filter="[tag[RL]contains:concepts<id>sort[title]]"/>
<$transclude $variable="vtw-section" label="Worked numbers" filter="[tag[FX]contains:concepts<id>sort[title]]"/>
<$transclude $variable="vtw-section" label="What the paper leaves open" filter="[tag[VD]field:status[open]contains:concepts<id>sort[title]]"/>
<$transclude $variable="vtw-section" label="What would have to be established" filter="[tag[CL]contains:concepts<id>sort[title]]"/>
<$transclude $variable="vtw-section" label="What we assume, infer or suspect" filter="[tag[FR]contains:concepts<id>sort[title]]"/>
<$transclude $variable="vtw-section" label="Cases to tell apart" filter="[tag[SC]contains:concepts<id>sort[title]]"/>
<$transclude $variable="vtw-section" label="Models" filter="[tag[EX]contains:concepts<id>sort[title]]"/>
<%else%>
<$transclude $variable="vtw-section" label="Concepts" filter="[<id>get[concepts]enlist-input[]]"/>
<$transclude $variable="vtw-section" label="Rests on" filter="[<id>get[provisions]enlist-input[]] [<id>get[conflicting_provisions]enlist-input[]] [<id>get[decisions]enlist-input[]] [<id>get[claims]enlist-input[]] [<id>get[findings]enlist-input[]] [<id>get[scenarios]enlist-input[]] [<id>get[pair_with]enlist-input[]] [<id>get[experiments]enlist-input[]] [<id>get[related]enlist-input[]]"/>
<$let rx={{{ [<id>escaperegexp[]addprefix[(^|\s)]addsuffix[(\s|$)]] }}}>
<$transclude $variable="vtw-section" label="Used by" filter="[tag[Record]] [tag[FX]] +[search:provisions,conflicting_provisions,decisions,claims,findings,scenarios,pair_with,experiments,components,related:regexp<rx>] +[sort[title]]"/>
</$let>
<%endif%>
<%else%>
<%if [all[current]tag[LP]] %>
<$list filter="CN RL VD CL SC FR EX FX CS" variable="t">
<%if [tag<t>contains:concepts<id>] %>
<div class="vtw-rollup">
<h3><$link to=<<t>>><$text text={{{ [[$:/vtw/schema/]addsuffix<t>get[plural]] }}}/></$link>&#32;<span class="vtw-count">(<$count filter="[tag<t>contains:concepts<id>]"/>)</span></h3>
<$transclude $variable="vtw-table" filter="[tag<t>contains:concepts<id>sort[title]]"/>
</div>
<%endif%>
</$list>
<%endif%>
<$list filter="[[$:/vtw/relations]indexes[]] -concepts" variable="f">
<$let hits={{{ [tag[Record]] [tag[FX]] :filter[get<f>enlist-input[]match<id>] +[sort[title]format:titlelist[]join[ ]] }}}>
<%if [<hits>!is[blank]] %>
<div class="vtw-rollup">
<h3>Linked here via <$text text={{{ [<f>search-replace:g[_],[ ]] }}}/>&#32;<span class="vtw-count">(<$count filter="[enlist<hits>]"/>)</span></h3>
<$transclude $variable="vtw-table" filter="[enlist<hits>]"/>
</div>
<%endif%>
</$let>
</$list>
<%endif%>
</$let>
<%endif%>
''')

# ------------------------------------------------------------------ journey templates

put("$:/vtw/ui/JourneyTop", tags="$:/tags/ViewTemplate", list__before="$:/core/ui/ViewTemplate/body", text=r'''
\whitespace trim
<%if [enlist{$:/vtw/path!!list}match<currentTiddler>] %>
<$let here=<<currentTiddler>> n={{{ [enlist{$:/vtw/path!!list}allbefore<currentTiddler>count[]add[1]] }}} total={{{ [enlist{$:/vtw/path!!list}count[]] }}}>
<div class="vtw-journey">
<div class="vtw-kicker">Research path&#32;·&#32;step&#32;<$text text=<<n>>/>&#32;of&#32;<$text text=<<total>>/>&#32;·&#32;review:&#32;<$text text={{{ [all[current]get[review_status]else[not submitted]] }}}/>
&#32;·&#32;<$list filter="[enlist{$:/vtw/path!!list}before<here>]">←&#32;<$link><$text text=<<currentTiddler>>/></$link></$list>
&#32;<$list filter="[enlist{$:/vtw/path!!list}after<here>]"><$link><$text text=<<currentTiddler>>/></$link>&#32;→</$list></div>
<div class="vtw-title"><$text text={{!!caption}}/></div>
<div class="vtw-question"><$transclude field="question" mode="inline"/></div>
<h2 class="vtw-jh"><span>1</span> Starting point</h2>
<%if [all[current]has[starting_point]] %><$transclude field="starting_point" mode="block"/><%endif%>
<%if [tag[CN]contains:carried_to<here>] %>
<p>''Carried in from earlier steps.''&#32;These conclusions are where this step begins:</p>
<$list filter="[tag[CN]contains:carried_to<here>sort[title]]"><<vtw-conclusion-card>></$list>
<%elseif [all[current]!has[starting_point]] %><p class="vtw-none">No starting point recorded.</p>
<%endif%>
<h2 class="vtw-jh"><span>2</span> The path</h2>
<%if [all[current]get[text]trim[]!is[blank]] :else[[none]] +[match[none]] %><p class="vtw-none">Not started.</p><%endif%>
</div>
</$let>
<%endif%>
''')

put("$:/vtw/ui/JourneyBottom", tags="$:/tags/ViewTemplate", list__after="$:/core/ui/ViewTemplate/body", text=r'''
\whitespace trim
<%if [enlist{$:/vtw/path!!list}match<currentTiddler>] %>
<$let here=<<currentTiddler>>>
<div class="vtw-journey">
<h2 class="vtw-jh"><span>3</span> Conclusions</h2>
<%if [tag[CN]field:task<here>] %>
<p class="vtw-lede">Draft conclusions, not reviewed. Each names the records it rests on; open them to see the evidence.</p>
<$list filter="[tag[CN]field:task<here>sort[title]]"><<vtw-conclusion-card>></$list>
<%else%><p class="vtw-none">No conclusions yet.</p>
<%endif%>
<h2 class="vtw-jh"><span>4</span> Where this leads</h2>
<%if [tag[CN]field:task<here>has[carried_to]] :else[[none]] +[match[none]] %><p class="vtw-none">Nothing carried forward yet.</p><%endif%>
<$list filter="[enlist{$:/vtw/path!!list}allafter<here>]" variable="next">
<$let carried={{{ [tag[CN]field:task<here>contains:carried_to<next>sort[title]format:titlelist[]join[ ]] }}}>
<%if [<carried>!is[blank]] %>
<div class="vtw-next"><$link to=<<next>>><$text text=<<next>>/>&#32;<$text text={{{ [<next>get[caption]] }}}/></$link>&#32;starts from&#32;<$list filter="[enlist<carried>]" join=", "><$link><$text text={{!!caption}}/></$link></$list>.
<div class="vtw-readsum"><$transclude tiddler=<<next>> field="question" mode="inline"/></div></div>
<%endif%>
</$let>
</$list>
<%if [[$:/config/vtw/mode]get[text]match[editor]] %>
<h3>Records introduced by this step</h3>
<$list filter="CN LP RL VD CL FR SC EX FX CS" variable="t"><%if [tag<t>field:introduced_by<here>] %><div><$link to=<<t>>><$text text={{{ [[$:/vtw/schema/]addsuffix<t>get[plural]] }}}/></$link>: <$count filter="[tag<t>field:introduced_by<here>]"/></div><%endif%></$list>
<%endif%>
</div>
</$let>
<%endif%>
''')

# ------------------------------------------------------------------ Home and sidebar

put("Home", text=r'''
\whitespace trim
<div class="vtw-home">
<p class="vtw-lede">This workbench follows one research path: from the Livepeer 2.0 litepaper to evidence-backed conclusions about its economics and validation. Each step starts from what the previous step concluded, uses organized records to test it, and ends in a few plain-language conclusions that the next step picks up.</p>
<p>''Start with the first step:''&#32;<$link to="M1.1"><$text text={{M1.1!!caption}}/></$link>.&#32;Read the starting point and conclusions; open the path in between when you want to see how the evidence gets there. Ask an agent to walk you through any record.</p>

<h2>The path</h2>
<ol class="vtw-pathlist">
<$list filter="[enlist{$:/vtw/path!!list}]">
<li><$link><strong><$text text=<<currentTiddler>>/></strong>&#32;<$text text={{!!caption}}/></$link>
<div class="vtw-readsum"><$transclude field="question" mode="inline"/></div>
<div class="vtw-idsmall">
<%if [tag[CN]field:task<currentTiddler>] %><$count filter="[tag[CN]field:task<currentTiddler>]"/>&#32;draft conclusions<%elseif [all[current]get[text]!is[blank]] %>in progress<%else%>not started<%endif%>
<%if [tag[CN]contains:carried_to<currentTiddler>] %>&#32;·&#32;starts from&#32;<$count filter="[tag[CN]contains:carried_to<currentTiddler>]"/>&#32;carried-in conclusions<%endif%>
</div></li>
</$list>
</ol>

<h2>Where things stand</h2>
<p class="vtw-lede">Draft conclusions from M1.1, not yet reviewed:</p>
<$transclude $variable="vtw-readlist" filter="[tag[CN]sort[title]]"/>

<h2>Other ways in</h2>
<ul>
<li>''How the paper works, mechanism by mechanism:''&#32;<$list filter="[tag[LP]sort[title]]" join=" · "><$link><$text text={{!!caption}}/></$link></$list></li>
<li>''How money moves:''&#32;<$link to="View: Cooperative flow">Cooperative flow</$link></li>
<li>''Find a rule, number or decision:''&#32;<$link to="View: Record finder">Record finder</$link>&#32;·&#32;<$link to="View: Parameter sheet">Parameter sheet</$link>&#32;·&#32;<$link to="View: Open decisions">Open decisions</$link></li>
</ul>
<details class="vtw-details"><summary>For editors and agents</summary>
<p><$link to="Conventions">Conventions</$link>&#32;·&#32;<$link to="About this wiki">About this wiki</$link>&#32;·&#32;<$link to="SRC-LP20">Source: litepaper snapshot</$link></p>
<$list filter="[tag[View]sort[title]]"><div><$link/> <span class="vtw-refcap"><$text text={{!!description}}/></span></div></$list>
</details>
</div>
''')

put("$:/vtw/ui/SideBarViews", text=r'''
\whitespace trim
<div class="vtw-side">
<p><<vtw-mode-toggle>></p>
<div><$link to="Home">Start here</$link></div>
<p class="vtw-side-h">Research path</p>
<$list filter="[enlist{$:/vtw/path!!list}]"><div><$link><$text text=<<currentTiddler>>/>&#32;<span class="vtw-refcap"><$text text={{!!caption}}/></span></$link></div></$list>
<p class="vtw-side-h">Views</p>
<$list filter="[[Conventions]] [tag[View]sort[title]]"><div><$link><$text text={{{ [all[current]removeprefix[View: ]else<currentTiddler>] }}}/></$link></div></$list>
<p class="vtw-side-h">Record types</p>
<$list filter="CN LP RL VD CL FR SC EX CS" variable="t"><div><$link to=<<t>>><$text text={{{ [[$:/vtw/schema/]addsuffix<t>get[plural]] }}}/></$link>&#32;<span class="vtw-count">(<$count filter="[tag<t>]"/>)</span></div></$list>
</div>
''')

put("$:/vtw/styles", text=wiki["$:/vtw/styles"]["text"] + r'''
.vtw-overview { font-size: 1.05em; line-height: 1.5; margin: 0.3em 0 0.5em; }
.vtw-inpaper { color: #4b6272; font-size: 0.92em; margin-bottom: 0.4em; }
details.vtw-details { margin-top: 0.4em; }
details.vtw-details > summary { cursor: pointer; color: #4b6272; font-size: 0.9em; }
ul.vtw-read { list-style: none; padding-left: 0; margin: 0.2em 0 0.6em; }
ul.vtw-read li { padding: 0.3em 0; border-bottom: 1px solid #eef2f5; }
.vtw-idsmall { color: #8a99a3; font-size: 0.8em; }
.vtw-readsum { color: #33424d; font-size: 0.93em; }
.vtw-rsec h3 { font-size: 1.05em; margin: 1em 0 0.2em; color: #23343f; }
.vtw-journey .vtw-title { font-size: 1.5em; }
.vtw-question { font-size: 1.1em; font-style: italic; margin: 0.3em 0 0.8em; }
h2.vtw-jh { border-bottom: 2px solid #2f6f8f; padding-bottom: 0.1em; margin-top: 1.2em; }
h2.vtw-jh span { display: inline-block; width: 1.4em; height: 1.4em; line-height: 1.4em; text-align: center; border-radius: 50%; background: #2f6f8f; color: #fff; font-size: 0.8em; margin-right: 0.4em; }
.vtw-step { border-left: 3px solid #cfdde6; padding: 0.1em 0 0.1em 0.9em; margin: 0.8em 0; }
.vtw-step h3 { margin: 0.2em 0; }
.vtw-data { background: #f5f9fb; border: 1px solid #dfe9ef; padding: 0.4em 0.7em; margin: 0.4em 0; font-size: 0.93em; }
.vtw-leadsto { color: #2f6f8f; font-size: 0.92em; }
.vtw-concl { border: 1px solid #d5e0e7; border-left: 4px solid #2f6f8f; padding: 0.5em 0.8em; margin: 0.6em 0; background: #fbfdfe; }
.vtw-concl-h { font-weight: 600; font-size: 1.05em; }
.vtw-concl-s { margin: 0.3em 0; line-height: 1.45; }
.vtw-concl-b, .vtw-concl-e { font-size: 0.9em; color: #4b6272; margin-top: 0.2em; }
.vtw-st-supported-by-text { background: #dcefe4; }
.vtw-next { margin: 0.5em 0; }
ol.vtw-pathlist li { margin: 0.5em 0; }
.vtw-toggle { font-size: 0.85em; }
''')

# ------------------------------------------------------------------ conclusions (M1.1, draft)

CN = [
    ("CN-01", "Anyone can sell; entry is gated only at rewards and seats", "supported-by-text",
     "The paper lets any address list and sell without a bond or node cap, and never caps fees. Stake limits only the inflation reward and who may validate. So any entry problem is about rewards, validator access and practical friction, not permission to sell.",
     "Registration, uncapped fees and the stake-rank validator rule are explicit. How outsiders actually find customers is unmeasured.",
     dict(provisions="RL-07 RL-11 RL-19", findings="FR-02 FR-05", concepts="LP-03 LP-04 LP-06", carried_to="M1.3 M2", participants="operator customer")),
    ("CN-02", "The reward formula cannot yet be computed exactly", "supported-by-text",
     "The main text gives min(fee share, stake share) scaled by the median honesty score, but the appendix describes node rewards differently. Nothing says what happens to reward left unassigned when fee and stake shares diverge. Any economic test must first pick and label an interpretation.",
     "The two descriptions are both in the paper (VD-06). In the worked example with fees 90/10 against stake 10/90, 752 of 940 LPT has no stated destination (illustrative).",
     dict(decisions="VD-06 VD-12 VD-05", findings="FR-24", experiments="EX-01", concepts="LP-04 LP-13", carried_to="M1.4 M2", participants="operator governance")),
    ("CN-03", "Validators judge dishonesty under rules that do not exist yet", "supported-by-text",
     "Validators are asked to catch self-dealing, fee fabrication and incorrect results, not to grade service quality. The paper gives no proof standard, quorum, abstention rule, appeal or constitution, so how a score is reached is undefined.",
     "The purpose is explicit (RL-25); the procedure questions are all open decisions, and the constitution is one of the paper's own open questions.",
     dict(provisions="RL-25 RL-65", decisions="VD-09 VD-10 VD-07 VD-21", concepts="LP-07 LP-14", carried_to="M1.2 M1.3", participants="validator operator governance")),
    ("CN-04", "The reward never checks demand or value", "inference",
     "A node's reward depends on three inputs: its fee share, its stake share and a dishonesty score. Execution, correctness and availability matter only as evidence of dishonesty. Whether the work was independently wanted, or worth subsidizing, is not an input at all.",
     "This is a reading of the reward formula against the separate claims a job can raise; M1.2 should test it claim by claim.",
     dict(claims="CL-09 CL-08 CL-07 CL-05 CL-06", decisions="VD-19", concepts="LP-04 LP-07 LP-02", carried_to="M1.2 M2", participants="validator governance")),
    ("CN-05", "Self-funded real usage is the central untested risk", "hypothesis",
     "If paid fees drive rewards, a party could pay its own node for real, correctly executed work and collect more than it spent. The paper's defenses (stake caps, the 7-round delay and an emissions cap) each limit part of this; none has been tested. This is a hypothesis for M2, not a finding.",
     "The paper itself names self-dealing as the concern its design must handle. Its defenses are stated rationales; no worked example has been run, and common ownership alone is not misconduct.",
     dict(findings="FR-01 FR-19 FR-21 FR-23", scenarios="SC-06 SC-07", concepts="LP-04 LP-07 LP-09 LP-12", carried_to="M1.2 M1.3 M2", participants="operator validator")),
    ("CN-06", "The economics rest on untested assumptions and unmade choices", "supported-by-text",
     "The emissions schedule is not chosen, and most rules the reward depends on remain open decisions. The link from goals to mechanisms rests on assumptions the paper does not test: that fees track meaningful work, that delegators move stake in time, that buybacks execute well.",
     "The emissions section calls itself an idea draft; the open decisions and assumptions are recorded individually.",
     dict(decisions="VD-14", findings="FR-13 FR-15 FR-16 FR-17", concepts="LP-12 LP-02 LP-05 LP-11", carried_to="M1.4 M2", participants="governance delegator")),
]
for rid, cap, status, stmt, basis, rel in CN:
    put(rid, record_type="CN", caption=cap, tags="Record CN", stage="M1", status=status, statement=stmt, basis=basis,
        task="M1.1", introduced_by="M1.1", last_changed_by="M1.1", text="", **rel)

# ------------------------------------------------------------------ M1.1 journey

M11_PATH = r'''
<div class="vtw-step">
<h3>What is the paper trying to achieve?</h3>
Its central promise is that <<r RL-03>>: fees for honest work, not stake alone, should earn new LPT. Every role should do active work (<<r RL-04>>), governance keeps room to adjust (<<r RL-05>>), and simplicity breaks ties (<<r RL-06>>).
<div class="vtw-leadsto">Concept: <<r LP-02>></div>
</div>

<div class="vtw-step">
<h3>How does money move when everyone cooperates?</h3>
There are two separate flows (<<r "View: Cooperative flow">>). Customers pay USDC; half goes to the node and half buys LPT, which is burned. Rewards come from a separate LPT mint split 94/1/5 between nodes, validators and the treasury.
<div class="vtw-data">''Worked example'' (<<r EX-01.F1>>, illustrative): <$transclude tiddler="EX-01.F1" field="inputs" mode="inline"/> → <$transclude tiddler="EX-01.F1" field="expected" mode="inline"/><br/>
''Fee side'' (<<r EX-01.F9>>): <$transclude tiddler="EX-01.F9" field="expected" mode="inline"/></div>
</div>

<div class="vtw-step">
<h3>What decides a node's reward?</h3>
The smaller of its fee share and stake share (<<r RL-10>>), scaled by the median honesty score (<<r RL-24>>). When fee and stake shares line up, the whole node budget is paid. When they diverge, much of it is not, and the paper does not say where it goes (<<r VD-12>>). The appendix also describes the formula differently (<<r VD-06>>).
<div class="vtw-data">''Diverging shares'' (<<r EX-01.F2>>): <$transclude tiddler="EX-01.F2" field="inputs" mode="inline"/> → <$transclude tiddler="EX-01.F2" field="expected" mode="inline"/></div>
<div class="vtw-leadsto">Leads to: <<r CN-02>></div>
</div>

<div class="vtw-step">
<h3>Who can take part, and where is stake required?</h3>
Anyone can list and sell (<<r RL-07>>); fees are never capped (<<r RL-11>>). Stake matters only for the size of the inflation reward and for validator seats (<<r RL-19>>). An understaked newcomer earns less inflation than an equally busy staked node (<<r FR-05>>).
<div class="vtw-data">''Entrant example'' (<<r EX-01.F13>>): <$transclude tiddler="EX-01.F13" field="inputs" mode="inline"/> → <$transclude tiddler="EX-01.F13" field="expected" mode="inline"/></div>
<div class="vtw-leadsto">Leads to: <<r CN-01>></div>
</div>

<div class="vtw-step">
<h3>What are validators asked to judge, and how?</h3>
Dishonesty (self-dealing, fee fabrication, incorrect results), not service quality (<<r RL-25>>). How a score is reached, who must take part, and how it can be challenged are all open.
<div class="vtw-data"><$count filter="[tag[VD]field:status[open]] :filter[get[classification]split[+]match[J]]"/> open decisions involve validator judgment, among them <<r VD-09>>, <<r VD-10>> and <<r VD-21>>.</div>
<div class="vtw-leadsto">Leads to: <<r CN-03>></div>
</div>

<div class="vtw-step">
<h3>What does the reward actually check?</h3>
A job can raise separate claims: paid, executed, correct, available, independently wanted, worth subsidizing. The reward formula uses only a few.
<div class="vtw-data">Claims the reward uses directly: <$list filter="[tag[CL]!field:reward_input[none]!field:reward_input[open]sort[title]]" join=", "><$link><$text text={{!!caption}}/></$link></$list>.<br/>
Claims it does not use: <$list filter="[tag[CL]field:reward_input[none]sort[title]]" join=", "><$link><$text text={{!!caption}}/></$link></$list>.</div>
<div class="vtw-leadsto">Leads to: <<r CN-04>></div>
</div>

<div class="vtw-step">
<h3>Where could it go wrong?</h3>
The paper worries about self-dealing. The hard case is not fake work but real work paid for by the party that collects the reward (<<r FR-01>>). It looks identical to genuine related-party use (<<r SC-06>> beside <<r SC-07>>). The paper's defenses each cover part of it: stake caps (<<r FR-19>>), the delay (<<r FR-21>>) and the emissions cap (<<r FR-23>>).
<div class="vtw-leadsto">Leads to: <<r CN-05>></div>
</div>

<div class="vtw-step">
<h3>What is still undecided?</h3>
The emissions schedule is an idea draft with three concepts (<<r LP-12>>). Beyond that:
<div class="vtw-data"><$count filter="[tag[VD]field:status[open]]"/> open decisions, <$count filter="[tag[VD]field:status[open]] :filter[get[classification]split[+]match[G]]"/> of them needing a governance choice (<<r "View: Open decisions">>). <$count filter="[tag[FR]field:status[assumption]]"/> assumptions connect goals to mechanisms, none tested (<<r "View: Findings register">>).</div>
<div class="vtw-leadsto">Leads to: <<r CN-06>></div>
</div>
'''

put("M1.1", caption="Understand what the litepaper does", text=M11_PATH,
    question="What does the litepaper seek to obtain, how are its economic mechanisms intended to work, and what assumptions connect the two? (issue #6)",
    starting_point=r'''We begin with nothing but the Livepeer 2.0 litepaper (<<r SRC-LP20>>). It proposes open node entry, USDC payments, rewards tied to both fees and stake, and a validator set that scores honesty. Its emissions section is an unfinished draft, and the paper says none of it is final. We treat every value as a proposal, not a decision.''')
put("M1.2", question="Which facts would a validator need to establish for reward eligibility, and would those facts actually protect the intended benefit? (issue #7)", text="")
put("M1.3", question="What representative behavior could extract rewards without delivering the intended benefit, and what useful activity could look similar? (issue #8)", text="")
put("M1.4", question="What would need to change from current Livepeer behavior to reach the litepaper's proposed system? (issue #14)", text="")
put("M2", caption="Test litepaper incentives and evidence limits", text="",
    question="Which of the litepaper's material economic concerns hold up in small worked examples under stated assumptions, and what can validators actually observe?")

# ------------------------------------------------------------------ LP-04 overview (reader sample)

put("LP-04", overview=r'''MFS is the paper's answer to "rewards should follow real work". A node's share of new LPT is the smaller of its share of network fees and its share of stake, then scaled by the validators' median honesty score. Fees themselves are never capped; only the inflation reward is.

Two things are unsettled: the appendix describes the formula differently, and nothing says what happens to reward left over when fee and stake shares don't line up. Whether the stake cap stops someone paying themselves for real work is the central question carried into M2.''')

json.dump(OUT, sys.stdout, indent=1, ensure_ascii=False)
