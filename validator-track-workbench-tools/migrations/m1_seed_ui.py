"""One-time seed: workbench UI, conventions, schema and meta tiddlers.

Output is importable tiddler JSON (vtw.py import). After import the workbench
HTML is authoritative; do not maintain this file as a parallel source.
"""

from __future__ import annotations

import json
import sys

T = []


def add(title, text="", **fields):
    t = {"title": title, "text": text.strip("\n")}
    for k, v in fields.items():
        t[k.replace("__", "-")] = v
    T.append(t)


# ------------------------------------------------------------------ site config

add("$:/SiteTitle", "Validator track workbench")
add("$:/SiteSubtitle", "Private working wiki · Livepeer 2.0 litepaper records")
add("$:/DefaultTiddlers", "[[Home]]")
add("$:/config/WikiParserRules/Inline/wikilink", "disable")
add("$:/config/Navigation/UpdateAddressBar", "no")
add("$:/language/DefaultNewTiddlerTitle", "New Tiddler")

# ------------------------------------------------------------------ schema (single authority)

PARTICIPANTS = "customer operator delegator validator governance"
add("$:/vtw/participants", "Participant vocabulary for the ''participants'' field.", list=PARTICIPANTS)

RELATIONS = {
    "concepts": "LP",
    "provisions": "RL",
    "conflicting_provisions": "RL",
    "decisions": "VD",
    "claims": "CL",
    "findings": "FR",
    "scenarios": "SC",
    "pair_with": "SC",
    "experiments": "EX",
    "components": "CS",
    "related": "*",
}
add("$:/vtw/relations", "\n".join(f"{k}: {v}" for k, v in RELATIONS.items()),
    type="application/x-tiddler-dictionary",
    description="ID-valued relationship fields and the record types each may point to (* = any record)")

FIELDS = {
    "title": "Stable ID (e.g. LP-04). Never renamed; other records refer to it.",
    "caption": "Readable name shown next to the ID.",
    "record_type": "LP, RL, VD, CL, FR, SC, EX, FX or CS. Also a tag.",
    "stage": "Milestone whose research boundary the record belongs to (M1, M2 ...).",
    "status": "Evidence or source status, from the record type's vocabulary. For LP and RL it is the status in the paper. Review status is never stored on a record.",
    "source_ref": "Explicit locator: source ID then line ranges, e.g. SRC-LP20 L55-63, L220. Several sources are separated by ';'.",
    "introduced_by": "Task that created the record (M1.1 ...).",
    "last_changed_by": "Task that last changed the record's substance.",
    "migrated_from": "Where migrated content came from (draft file and old row ID). Drives the crosswalk.",
    "migration_note": "What changed during migration, when more than a copy.",
    "concepts": "LP IDs the record concerns. Concept pages derive their lists from this field.",
    "provisions": "RL IDs the record depends on or discusses.",
    "conflicting_provisions": "RL IDs that are in tension and must be reconciled (VD).",
    "decisions": "VD IDs the record depends on or raises.",
    "claims": "CL IDs at issue.",
    "findings": "FR IDs (rarely needed; FR records usually point outward).",
    "scenarios": "SC IDs.",
    "pair_with": "The paired legitimate lookalike or adversarial SC record.",
    "experiments": "EX IDs that test, reproduce or illustrate the record.",
    "components": "CS IDs (M1.4).",
    "related": "Other explicit links not covered by a typed field.",
    "participants": "Participant tags: customer, operator, delegator, validator, governance.",
    "kind": "LP: objective, principle, mechanism, parameter-set, exclusion, open-question. RL: principle, objective, rule, formula, parameter, alternative, exclusion, open-question, reported-figure, illustration.",
    "in_paper": "What the paper says, at most two sentences.",
    "formula": "Formula as stated or reconstructed; reconstruction names its EX record.",
    "value": "Proposed or stated value, as written in the paper.",
    "unit": "Unit of the value.",
    "governance_adjustable": "yes, no, n/a or unstated, per the paper's appendix.",
    "question": "The single question the record answers or leaves open.",
    "classification": "Decision labels joined by '+': D deterministic accounting, E external observation, J judgment, G governance/policy, S stochastic service output.",
    "paper_says": "What the paper provides toward the decision (was 'evidence' in the draft CSV).",
    "evidence_needed": "Specification or evidence that would settle the decision.",
    "residual_uncertainty": "What remains unspecified or unknown.",
    "authority": "Who decides or observes under the paper's outline.",
    "consequence": "What the decision changes.",
    "specification_status": "How far the paper specifies the rule.",
    "follow_up": "Where the question is taken next.",
    "owner_milestone": "Tasks or milestones expected to carry the question (M1.2, M1.3, M1.4, M2, M3).",
    "claim": "The claim, stated so that it could be true or false of a job or node.",
    "observers": "Who can observe evidence for the claim.",
    "evidence_types": "Kinds of evidence that could support the claim.",
    "does_not_establish": "What the claim, even if proven, does not show.",
    "reward_input": "Whether the paper's reward uses the claim directly: MFS, multiplier, none or open.",
    "statement": "The assumption, hypothesis or finding in one sentence or two.",
    "evidence": "Evidence for or against, with sources.",
    "would_change": "What would weaken, strengthen or resolve it (counterevidence belongs here).",
    "implication": "Consequence if it holds.",
    "design_question": "The question it raises for later tasks, without proposing a mechanism.",
    "sc_type": "cooperative, market-pressure, adversarial or lookalike.",
    "situation": "The case in two or three sentences.",
    "observable": "What a validator could observe.",
    "litepaper_outcome": "What the paper's rules do in this case, with line references.",
    "ambiguity": "What the paper leaves unsettled for this case.",
    "inputs": "Inputs and controls.",
    "method": "How the experiment works.",
    "results": "Results, each tagged illustrative or measured.",
    "limits": "What the experiment does not establish.",
    "reproduce": "Commands to reproduce, from the repository root.",
    "repo_path": "Location of code and outputs in the public repository working tree.",
    "expected": "Fixture result.",
    "checked_by": "verify.py (automated) or hand (arithmetic in a draft, not automated).",
    "layer": "contract, off-chain or role (CS).",
    "deployed_version": "Deployed version, address or release inspected (CS).",
    "change": "Current system to litepaper: retain, modify, replace, remove, new or unknown (CS).",
    "impact": "Impact notes (CS).",
    "unknowns": "Open items (CS).",
    "planned_artifact": "Artifact path planned in MILESTONES.md.",
    "issue": "GitHub task issue.",
    "review_status": "Not submitted, In review, Accepted or Changes requested. Only task tiddlers carry it.",
    "sha256": "Content hash identifying a source version.",
}
add("$:/vtw/fields", "\n".join(f"{k}: {v}" for k, v in FIELDS.items()), type="application/x-tiddler-dictionary")

LABELS = {
    "D": "deterministic accounting over agreed inputs",
    "E": "external observation",
    "J": "interpretive judgment",
    "G": "protocol or governance policy choice",
    "S": "stochastic service output or availability",
}
add("$:/vtw/labels", "\n".join(f"{k}: {v}" for k, v in LABELS.items()), type="application/x-tiddler-dictionary")

COMMON = "caption stage status source_ref concepts participants"
TAIL = "related introduced_by last_changed_by migrated_from migration_note"
SCHEMA = {
    "LP": dict(name="Concept", plural="Concepts", id__pattern=r"^LP-\d{2}$",
               display=f"caption kind status in_paper formula source_ref participants {TAIL}",
               required="caption kind status in_paper source_ref stage introduced_by",
               vocab__kind="objective principle mechanism parameter-set exclusion open-question",
               vocab__status="explicit proposed-value open-draft",
               summary="in_paper", needs__concepts="no",
               description="One litepaper mechanism, objective, exclusion or group of open questions. Primary key for everything else."),
    "RL": dict(name="Provision", plural="Provisions", id__pattern=r"^RL-\d{2}$",
               display=f"caption kind status value unit governance_adjustable in_paper formula source_ref concepts participants {TAIL}",
               required="caption kind status in_paper source_ref concepts stage introduced_by",
               vocab__kind="principle objective rule formula parameter alternative exclusion open-question reported-figure illustration",
               vocab__status="explicit proposed-value open-draft illustrative",
               vocab__governance_adjustable="yes no n/a unstated",
               summary="in_paper", needs__concepts="yes",
               description="One stated rule, formula, parameter, alternative, exclusion or open question in the paper. The parameter sheet is RL with kind=parameter."),
    "VD": dict(name="Decision", plural="Decisions", id__pattern=r"^VD-\d{2}$",
               display=f"caption status question classification paper_says evidence_needed residual_uncertainty authority consequence specification_status provisions conflicting_provisions claims concepts participants owner_milestone follow_up source_ref {TAIL}",
               required="caption status question classification paper_says source_ref concepts stage introduced_by",
               vocab__status="open interpreted-for-modeling resolved-by-governance split",
               pattern__classification=r"^[DEJGS](\+[DEJGS])*$",
               summary="question", needs__concepts="yes",
               description="One rule the paper needs but does not specify, or specifies inconsistently."),
    "CL": dict(name="Claim", plural="Claims", id__pattern=r"^CL-\d{2}$",
               display=f"caption status claim reward_input classification observers evidence_types does_not_establish concepts participants source_ref {TAIL}",
               required="caption status claim reward_input concepts stage introduced_by",
               vocab__status="seed analysed",
               vocab__reward_input="MFS multiplier none open",
               pattern__classification=r"^([DEJGS](\+[DEJGS])*|open)$",
               summary="claim", needs__concepts="yes",
               description="One distinct thing that can be asserted about a job or node. Payment, execution, correctness, availability, independent demand and economic value are separate claims."),
    "FR": dict(name="Finding", plural="Findings", id__pattern=r"^FR-\d{2}$",
               display=f"caption status statement evidence would_change implication design_question provisions decisions claims experiments concepts participants source_ref {TAIL}",
               required="caption status statement concepts stage introduced_by",
               vocab__status="assumption hypothesis inference supported weakened rejected",
               summary="statement", needs__concepts="yes",
               description="One assumption, hypothesis, inference or tested finding with its status and counterevidence."),
    "SC": dict(name="Scenario", plural="Scenarios", id__pattern=r"^SC-\d{2}$",
               display=f"caption status sc_type pair_with situation observable litepaper_outcome ambiguity claims decisions experiments concepts participants source_ref {TAIL}",
               required="caption status sc_type situation concepts stage introduced_by",
               vocab__status="seed specified",
               vocab__sc_type="cooperative market-pressure adversarial lookalike",
               summary="situation", needs__concepts="yes",
               description="One cooperative, market-pressure, adversarial or lookalike case. Ordered cooperative, then market pressure, then strategic."),
    "EX": dict(name="Experiment", plural="Experiments", id__pattern=r"^EX-\d{2}$",
               display=f"caption status question inputs method formula results limits reproduce repo_path provisions decisions concepts participants source_ref {TAIL}",
               required="caption status question concepts stage introduced_by",
               vocab__status="proposed reproducible retired",
               summary="question", needs__concepts="yes",
               description="One reproducible model or fixture set. Code and outputs stay in Git."),
    "FX": dict(name="Fixture", plural="Fixtures", id__pattern=r"^EX-\d{2}\.F\d+$",
               display=f"caption status inputs expected checked_by experiments concepts source_ref {TAIL}",
               required="caption status inputs expected checked_by experiments stage introduced_by",
               vocab__status="illustrative measured",
               vocab__checked_by="verify.py hand",
               summary="expected", needs__concepts="no",
               description="One fixture row of an experiment. Titled EX-nn.Fk."),
    "CS": dict(name="Component", plural="Components", id__pattern=r"^CS-\d{2}$",
               display=f"caption status layer deployed_version change impact unknowns concepts provisions participants source_ref {TAIL}",
               required="caption status layer change concepts source_ref stage introduced_by",
               vocab__status="seed mapped",
               vocab__layer="contract off-chain role",
               vocab__change="retain modify replace remove new unknown",
               summary="impact", needs__concepts="yes",
               description="One contract, off-chain component or participant role in the current system, mapped to the litepaper (M1.4)."),
}
for rt, s in SCHEMA.items():
    add(f"$:/vtw/schema/{rt}", s.pop("description"), record_type=rt,
        required__tags=f"{'FX' if rt == 'FX' else 'Record ' + rt}", **s)

# templates for new records (fields only; the button supplies title and tags)
for rt, s in SCHEMA.items():
    if rt == "FX":
        continue
    fields = {f: "" for f in SCHEMA[rt]["display"].split() if f not in ("caption",)}
    fields.update(record_type=rt, stage="M1", caption="", status=SCHEMA[rt]["vocab__status"].split()[0])
    add(f"$:/vtw/template/{rt}", "", **fields)

# ------------------------------------------------------------------ global procedures

add("$:/vtw/procedures", r'''
\whitespace trim

\function vtw.next(type) [[00]] [tag<type>removeprefix<type>removeprefix[-]] +[maxall[]add[1]pad[2]addprefix[-]addprefix<type>]

\procedure vtw-ref(id)
<span class="vtw-ref"><$link to=<<id>>><$text text=<<id>>/></$link>
<%if [<id>!is[tiddler]] %><span class="vtw-missing">&#32;missing</span>
<%elseif [<id>has[caption]] %><span class="vtw-refcap">&#32;<$text text={{{ [<id>get[caption]] }}}/></span>
<%endif%></span>
\end

\procedure vtw-refs(field)
<$list filter="[all[current]get<field>enlist-input[]]" variable="id"><$transclude $variable="vtw-ref" id=<<id>>/></$list>
\end

\procedure vtw-status()
<%if [all[current]has[status]] %><span class=`vtw-status vtw-st-${[{!!status}]}$`><$text text={{!!status}}/></span><%endif%>
\end

\procedure vtw-table(filter)
<table class="vtw-list"><tbody>
<$list filter=<<filter>> emptyMessage="<tr><td class='vtw-none'>none</td></tr>">
<tr>
<td class="vtw-id"><$link/></td>
<td class="vtw-cap"><$text text={{!!caption}}/></td>
<td class="vtw-sum"><$let sf={{{ [[$:/vtw/schema/]addsuffix{!!record_type}get[summary]] }}}><$transclude field=<<sf>> mode="inline"/></$let></td>
<td class="vtw-st"><<vtw-status>></td>
</tr>
</$list>
</tbody></table>
\end

\procedure vtw-new(type)
<$let schema={{{ [[$:/vtw/schema/]addsuffix<type>] }}} next={{{ [function[vtw.next],<type>] }}}>
<$button class="vtw-new" tooltip={{{ [[Create ]addsuffix<next>] }}}>
<$action-sendmessage $message="tm-new-tiddler" $param={{{ [[$:/vtw/template/]addsuffix<type>] }}} title=<<next>> tags={{{ [[Record]] [<type>] +[join[ ]] }}}/>
New <$text text={{{ [<schema>get[name]lowercase[]] }}}/> (<$text text=<<next>>/>)
</$button>
</$let>
\end

\procedure vtw-type-index()
<$let type=<<currentTiddler>> schema={{{ [[$:/vtw/schema/]addsuffix<currentTiddler>] }}}>
<p class="vtw-lede"><$transclude tiddler=<<schema>> field="text" mode="inline"/></p>
<p><$count filter="[tag<type>]"/> records. <$transclude $variable="vtw-new" type=<<type>>/></p>
<$transclude $variable="vtw-table" filter="[tag<type>sort[title]]"/>
</$let>
\end
''', tags="$:/tags/Global")

# ------------------------------------------------------------------ view templates

add("$:/vtw/ui/RecordHeader", r'''
\whitespace trim
<%if [all[current]has[record_type]] -[all[current]prefix[$:/]] %>
<$let schema={{{ [[$:/vtw/schema/]addsuffix{!!record_type}] }}}>
<div class="vtw-header">
<div class="vtw-kicker"><$link to={{!!record_type}}><$text text={{{ [<schema>get[name]] }}}/></$link>&#32;·&#32;<$text text={{!!stage}}/>&#32;<<vtw-status>></div>
<div class="vtw-title"><$text text={{!!caption}}/></div>
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
</div>
</$let>
<%endif%>
''', tags="$:/tags/ViewTemplate", list__before="$:/core/ui/ViewTemplate/body")

add("$:/vtw/ui/RecordRollup", r'''
\whitespace trim
<%if [all[current]has[record_type]] -[all[current]prefix[$:/]] %>
<$let id=<<currentTiddler>>>
<%if [all[current]tag[LP]] %>
<$list filter="RL VD CL SC FR EX FX CS" variable="t">
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
</$let>
<%endif%>
''', tags="$:/tags/ViewTemplate", list__after="$:/core/ui/ViewTemplate/body")

add("$:/vtw/ui/SideBarViews", r'''
\whitespace trim
<div class="vtw-side">
<$list filter="[[Home]] [[Conventions]] [tag[View]sort[title]]"><div><$link><$text text={{{ [all[current]get[caption]else<currentTiddler>] }}}/></$link></div></$list>
<p class="vtw-side-h">Record types</p>
<$list filter="LP RL VD CL FR SC EX CS" variable="t"><div><$link to=<<t>>><$text text={{{ [[$:/vtw/schema/]addsuffix<t>get[plural]] }}}/></$link>&#32;<span class="vtw-count">(<$count filter="[tag<t>]"/>)</span></div></$list>
</div>
''', tags="$:/tags/SideBar", caption="Workbench", list__before="$:/core/ui/SideBar/Open")

add("$:/vtw/ui/SearchResults", """\\import [[$:/core/ui/DefaultSearchResultList]]
<<searchResultList>>
""", tags="$:/tags/SearchResults", caption="Records (all fields)",
    first__search__filter="[!is[system]search:title,caption<userInput>sort[title]limit[250]]",
    second__search__filter="[!is[system]search:*<userInput>sort[title]limit[250]]",
    list__before="$:/core/ui/DefaultSearchResultList")
add("$:/config/SearchResults/Default", "$:/vtw/ui/SearchResults")

add("$:/vtw/styles", r'''
.vtw-header { border-left: 4px solid #2f6f8f; padding: 0.4em 0.8em; margin-bottom: 1em; background: #f5f9fb; }
.vtw-kicker { font-size: 0.85em; color: #4b6272; text-transform: uppercase; letter-spacing: 0.04em; }
.vtw-title { font-size: 1.25em; font-weight: 600; margin: 0.1em 0 0.4em; }
table.vtw-fields, table.vtw-list, table.vtw-grid { width: 100%; border-collapse: collapse; margin: 0; }
table.vtw-fields th { width: 11em; text-align: left; vertical-align: top; font-weight: 500; color: #4b6272; background: none; }
table.vtw-fields td, table.vtw-fields th, table.vtw-list td, table.vtw-grid td, table.vtw-grid th { border: none; border-bottom: 1px solid #e3eaef; padding: 0.25em 0.4em; vertical-align: top; }
table.vtw-grid th { background: #eaf1f5; text-align: left; }
td.vtw-id { white-space: nowrap; width: 5.5em; }
td.vtw-cap { width: 15em; font-weight: 500; }
td.vtw-sum { color: #33424d; font-size: 0.92em; }
td.vtw-st { width: 8em; }
.vtw-ref { display: block; }
.vtw-refcap { color: #4b6272; }
.vtw-missing { color: #b00020; font-weight: 600; }
.vtw-status { display: inline-block; padding: 0 0.45em; border-radius: 0.6em; font-size: 0.8em; background: #e3eaef; color: #23343f; text-transform: none; letter-spacing: 0; }
.vtw-st-open, .vtw-st-hypothesis { background: #fff1cc; }
.vtw-st-assumption { background: #e8e1f5; }
.vtw-st-inference { background: #dcefe4; }
.vtw-st-seed, .vtw-st-proposed { background: #f0e6d8; }
.vtw-st-split, .vtw-st-retired { background: #eeeeee; color: #777; }
.vtw-st-open-draft, .vtw-st-illustrative { background: #fde2e1; }
.vtw-rollup { margin-top: 1.2em; }
.vtw-rollup h3 { margin-bottom: 0.2em; font-size: 1.05em; }
.vtw-count { color: #6b7f8c; font-weight: normal; font-size: 0.9em; }
.vtw-callout { border: 1px solid #d9a400; background: #fff8e1; padding: 0.6em 0.9em; margin: 0.8em 0; }
.vtw-lede { color: #33424d; }
.vtw-none { color: #8a99a3; font-style: italic; }
.vtw-finder input, .vtw-finder select { margin: 0.2em 0.4em 0.2em 0; }
.vtw-finder input.vtw-q { width: 60%; }
.vtw-side div { padding: 0.1em 0; }
.vtw-side-h { margin: 0.8em 0 0.2em; font-weight: 600; color: #4b6272; }
.vtw-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8em; margin-bottom: 1em; }
.vtw-card { border: 1px solid #d5e0e7; padding: 0.4em 0.7em; }
.vtw-card .vtw-kicker { margin-bottom: 0.2em; }
''', tags="$:/tags/Stylesheet", type="text/css")

# ------------------------------------------------------------------ type index (tag) tiddlers

for rt, s in SCHEMA.items():
    if rt == "FX":
        add("FX", "<<vtw-type-index>>", caption="Fixtures")
    else:
        add(rt, "<<vtw-type-index>>", caption=SCHEMA[rt]["plural"])
add("Record", "Tag carried by every research record. Record types: [[LP]], [[RL]], [[VD]], [[CL]], [[FR]], [[SC]], [[EX]], [[CS]]; fixtures carry [[FX]]. See [[Conventions]].")
add("View", "Tag for navigable views.\n\n<<list-links filter:\"[tag[View]sort[title]]\">>")

# ------------------------------------------------------------------ home, about, conventions

add("Home", r'''
\whitespace trim
<p class="vtw-lede">Private working wiki for the validator track. It holds litepaper-grounded research records for M1 and M2. It is unpublished; Git receives only snapshots Shane approves. Read [[Conventions]] before editing.</p>

<div class="vtw-callout">''Central hypothesis for M2: <$link to="FR-01">FR-01</$link> <$text text={{FR-01!!caption}}/>'' (<$text text={{FR-01!!status}}/>)<br/><$transclude tiddler="FR-01" field="statement" mode="inline"/></div>

<table class="vtw-grid"><tbody>
<tr><th>Records</th><$list filter="LP RL VD CL FR SC EX CS" variable="t"><th><$link to=<<t>>><$text text=<<t>>/></$link></th></$list></tr>
<tr><td>count</td><$list filter="LP RL VD CL FR SC EX CS" variable="t"><td><$count filter="[tag<t>]"/></td></$list></tr>
</tbody></table>

<h3>Views</h3>
<$list filter="[tag[View]sort[title]]"><div><$link/> <span class="vtw-refcap"><$text text={{!!description}}/></span></div></$list>

<h3>Sources and tasks</h3>
<div><$link to="SRC-LP20"/> <span class="vtw-refcap"><$text text={{SRC-LP20!!caption}}/></span></div>
<div><$link to="SRC-M1-DRAFTS"/> <span class="vtw-refcap"><$text text={{SRC-M1-DRAFTS!!caption}}/></span></div>
<div><$link to="View: Milestone dashboard">Milestone dashboard</$link> · <$link to="About this wiki">About this wiki</$link></div>
''')

add("About this wiki", r'''
* Application: TiddlyWiki 5, version <<version>> (the core plugin in this file reports its own version: <$text text={{$:/core!!version}}/>).
* Created from the official empty wiki at https://tiddlywiki.com/empty.html, retrieved 2026-09-28; sha256 of the retrieved file `f161e81d0b25d6902ab259a5a8797c7a2a9abce3dc2d57e63d7a078100084028`. Upstream source: https://github.com/TiddlyWiki/TiddlyWiki5.
* Working file: `/home/mav/repos/livepeer/validator-track-workbench.html` (private, outside the public repository).
* Agent helper: `/home/mav/repos/livepeer/validator-track-workbench-tools/vtw.py` (export, import, lint, diff). It rewrites only the tiddler store and keeps a backup before every write.
* Saving from a browser downloads a new HTML file. Place it over the working file and reopen it before an agent edits again. See the editing protocol in [[Conventions]].
''')

add("Conventions", r'''
\whitespace trim
<h2>Standing disclaimer</h2>
<p>These records are research working material grounded in [[SRC-LP20]] and, for M1.4, current-system evidence. Nothing here is an accepted deliverable, an adopted parameter or a protocol decision. Paper values are proposals; illustrative numbers show conditions, not forecasts. Review status lives only on task tiddlers (see [[View: Milestone dashboard]]); a record's ''status'' is its evidence or source status. This is the only place the disclaimer is stated.</p>

<h2>Scope during M1 and M2</h2>
<p>Records explain and test the litepaper. They label assumptions and hypotheses, and establish gaps through findings. They do not describe successor mechanisms or compare against one. Record types and fields for M3 are added when M3 starts. The ID prefix EL is reserved and has no records. Preserve counterevidence in ''would_change''.</p>

<h2>Record types</h2>
<table class="vtw-grid"><tbody>
<tr><th>Prefix</th><th>Type</th><th>One record is</th><th>Status vocabulary</th><th>Required fields</th></tr>
<$list filter="[all[tiddlers]prefix[$:/vtw/schema/]sort[title]]">
<tr><td><$link to={{!!record_type}}><$text text={{!!record_type}}/></$link></td><td><$text text={{!!name}}/></td><td><$transclude field="text" mode="inline"/></td><td><$text text={{!!vocab-status}}/></td><td><$text text={{!!required}}/></td></tr>
</$list>
</tbody></table>

<h2>Fields</h2>
<p>Field meanings are defined once, here. Relationship fields hold stable IDs as a space-separated list; they are marked ⇢ with the record types they may point to.</p>
<table class="vtw-grid"><tbody>
<tr><th>Field</th><th>Meaning</th></tr>
<$list filter="[[$:/vtw/fields]indexes[]]" variable="f">
<tr><td><$text text=<<f>>/><%if [[$:/vtw/relations]indexes[]match<f>] %>&#32;⇢&#32;<$text text={{{ [[$:/vtw/relations]getindex<f>] }}}/><%endif%></td><td><$text text={{{ [[$:/vtw/fields]getindex<f>] }}}/></td></tr>
</$list>
</tbody></table>

<h2>Decision labels</h2>
<table class="vtw-grid"><tbody>
<$list filter="[[$:/vtw/labels]indexes[]]" variable="l"><tr><td><$text text=<<l>>/></td><td><$text text={{{ [[$:/vtw/labels]getindex<l>] }}}/></td></tr></$list>
</tbody></table>
<p>A rule may carry several labels: a mechanically computed median (D) can aggregate judgment-based scores (J). Ordinary customer choice is not governance.</p>

<h2>Identity and links</h2>
<ul>
<li>The title is the stable ID; ''caption'' is the readable name. Never rename a record; retire it with a status instead (VD uses ''split'', EX uses ''retired'').</li>
<li>IDs are never reused. New IDs take the next number (the ''New'' button on each type page does this).</li>
<li>Every non-LP record lists the LP IDs it concerns in ''concepts''. Concept pages derive their lists from that field and never repeat record content.</li>
<li>Store a relation once, on the record that depends on the other. Pages show links in both directions.</li>
<li>Participants are a field value, not a record type: <$text text={{$:/vtw/participants!!list}}/>.</li>
<li>TiddlyWiki does not enforce references. [[View: Reference check]] and `vtw.py lint` flag missing targets, wrong target types, duplicates and vocabulary errors.</li>
</ul>

<h2>Writing rules</h2>
<ul>
<li>''in_paper'' is at most two sentences plus a line reference. The reader knows the paper.</li>
<li>Hedging is a status value, not a sentence. Do not restate the disclaimer in records.</li>
<li>Every number carries its status: paper-proposed (RL status), illustrative, or measured.</li>
<li>A record answers one question. If it needs a second paragraph, split it.</li>
<li>No QA narrative inside records. Review history lives in the issue and PR.</li>
<li>Keep claims distinct: payment, execution, correctness, availability, independent demand and economic value. The paper's multiplier concerns dishonesty, not service quality.</li>
</ul>

<h2>Provenance</h2>
<p>Primary source: [[SRC-LP20]]. Line references (L55-63) refer to that exact snapshot. Records migrated from the unaccepted M1.1 drafts name their origin in ''migrated_from''; the drafts are identified in [[SRC-M1-DRAFTS]] and listed row by row in [[View: Crosswalk]].</p>

<h2>Editing protocol</h2>
<ol>
<li>One writer at a time. Save the browser copy and close or reload it before an agent edits the file; reopen after the agent finishes, before the next browser save.</li>
<li>A browser save downloads a new HTML file. Move it over `validator-track-workbench.html`, then reopen that file.</li>
<li>Agents change tiddlers with `vtw.py import` or `remove`, which back up the file first and can refuse to write if its hash changed (`--expect-sha`). No search-and-replace over the HTML.</li>
<li>For review, `vtw.py diff OLD NEW` lists created, modified and removed tiddlers with field-level changes. A JSON export is a review aid, never a second database.</li>
<li>Publication: Shane approves an exact snapshot; only then is it copied into the public repository or a release. Check every included tiddler for scope, restricted material and unresolved references first.</li>
</ol>
''')

# ------------------------------------------------------------------ sources

add("SRC-LP20", "Primary source for all M1 records. The emissions section is an open idea draft (L130), and the paper says none of the design is final until open questions are worked through in simulation, testing and feedback (L187). A canonical public copy or permalink for this version has not been established.",
    caption="Livepeer 2.0 Litepaper (Doug Petkanics, September 2026), local snapshot",
    record_kind="source", local_path="/home/mav/repos/livepeer/litepaper-2.0.md",
    sha256="5fc153408fb636d9750788ae987ada6daaa9fc3df3e44f70cadde51a6158fb71", lines="247", tags="Source")
add("SRC-M1-DRAFTS", r'''
Unaccepted M1.1 drafts (v0.3, 2026-09-26) used as migration input. They remain in the repository working tree, untracked and unreviewed, until Shane approves their replacement.

|!File (repository working tree)|!sha256|
|`deliverables/m1/litepaper-baseline-map.md`|`ec27a1cd9873d6cd404e5d319275492392c7f8ee3741132dc3f9e99fc8d96085`|
|`deliverables/m1/growth-and-entry-assessment.md`|`75b70cb6a13b2c3ca90b063a97b1b4f913a2ec7b08142a31cf435264608f739b`|
|`deliverables/m1/validator-decision-map.csv`|`1615f806550427fc3beb14456887bacfaa536e45492b36e58d05de4496a6f53b`|
|`deliverables/m1/litepaper-baseline-accounting.xlsx`|`c6fb9c291b1b2e8665a676f58e636f0ebae4012e28f5ccd90c2d3f632332df69`|
|`experiments/m1/baseline-accounting/build.py`|`286cd1c958b29f73f417d3685b009fd771982abe575187b87db08e0ecbbb1490`|
|`experiments/m1/baseline-accounting/verify.py`|`32f90744f9dd76dbad5bc07051ccf6a7f0f016436c1ba0d9bbaa2c0d33a1534c`|
|`experiments/m1/baseline-accounting/README.md`|`3f540fc2703a62b3a803efeae2b3e4617f67917a9607db11d5524f9dacf9c095`|
''', caption="M1.1 draft package v0.3 (migration input)", record_kind="source", tags="Source")
add("Source", "Source identities used in ''source_ref'' locators.\n\n<<list-links filter:\"[tag[Source]sort[title]]\">>")

# ------------------------------------------------------------------ tasks and stages

add("M1", "Use the litepaper as the design foundation. Separate outcomes from mechanisms and assumptions, identify the claims reward eligibility relies on, and map the current system to the paper.",
    caption="Objectives, assumptions and validation requirements", tags="Stage",
    issue="https://github.com/moatus/livepeer-validator-track/issues/1")
add("M2", "Small worked examples of the paper's material economic assumptions, evidence limits and a findings register. Modeled concern stays distinct from observed prevalence.",
    caption="Test litepaper incentives and evidence limits", tags="Stage",
    issue="https://github.com/moatus/livepeer-validator-track/issues/2")
add("Stage", "Milestones that bound records' research scope.\n\n<<list-links filter:\"[tag[Stage]sort[title]]\">>")
add("Task", "Milestone tasks. Each carries the task question, planned artifact, review status and, once drafted, its one-page brief.\n\n<<list-links filter:\"[tag[Task]sort[title]]\">>")

TASK_RECORDS = r'''
<h3>Records introduced by this task</h3>
<$list filter="LP RL VD CL FR SC EX FX CS" variable="t">
<%if [tag<t>field:introduced_by<currentTiddler>] %><div><$link to=<<t>>><$text text={{{ [[$:/vtw/schema/]addsuffix<t>get[plural]] }}}/></$link>: <$count filter="[tag<t>field:introduced_by<currentTiddler>]"/></div><%endif%>
</$list>
'''

add("M1.1", r'''
\whitespace trim
<h2>Brief (draft)</h2>
<p>''Question'' (issue #6). What does the litepaper seek to obtain, how are its economic mechanisms intended to work, and what assumptions connect the two?</p>
<p>''Answer.''</p>
<ol>
<li>The paper aims at open AI media compute in which inflation rewards follow real, honest work rather than stake alone ([[LP-01]], [[LP-02]]).</li>
<li>Entry is open: any address can list and sell without a bond or node cap. Stake limits only the inflation reward ([[RL-07]], [[RL-11]], [[FR-02]]).</li>
<li>A node's inflation share is min(fee share, stake share), scaled by the median 0-1 honesty score current when it claims, at least 7 rounds later ([[LP-04]], [[LP-07]], [[LP-09]]).</li>
<li>Customer USDC and LPT emissions are separate ledgers. Half of fees buys and burns LPT; a separately governed mint is split 94/1/5 ([[View: Cooperative flow]]).</li>
<li>The emissions schedule is an open draft with three concepts and a proposed cap ([[LP-12]]).</li>
<li>The score targets dishonesty (self-dealing, fee fabrication, incorrect results), not service quality ([[RL-25]]).</li>
<li><$count filter="[tag[VD]field:status[open]]"/> decisions stay open, notably the formula tension ([[VD-06]]), the unassigned remainder ([[VD-12]]), score procedure ([[VD-09]], [[VD-10]]) and claim-time finality ([[VD-11]]).</li>
<li>Objectives connect to mechanisms through assumptions the paper does not test: fees track meaningful work, validators can separate dishonesty from honest work, delegators can move stake in time, buybacks execute well ([[View: Findings register]], FR-12 to FR-22).</li>
<li>The central hypothesis for M2 is self-funded real usage ([[FR-01]]). The entrant reward gap is conditional arithmetic, not observed exclusion ([[FR-05]]).</li>
</ol>
<p>''Limits.'' Desk reading of one paper snapshot plus a fixed-envelope accounting reconstruction ([[EX-01]]). No deployed system, market or participant was observed. Claims and scenarios are seeds for M1.2 and M1.3.</p>
''' + TASK_RECORDS,
    caption="Map litepaper objectives, mechanisms and incentives", tags="Task", stage="M1",
    issue="https://github.com/moatus/livepeer-validator-track/issues/6",
    planned_artifact="deliverables/m1/litepaper-baseline-map.md", review_status="Not submitted")
add("M1.2", "<p>''Question'' (issue #7). Which facts would a validator need to establish for reward eligibility, and would those facts actually protect the intended benefit?</p>\n<p>Brief not started. Seed claims awaiting analysis: <$count filter=\"[tag[CL]field:status[seed]]\"/> (see [[View: Claims matrix]]).</p>" + TASK_RECORDS,
    caption="Determine what reward eligibility needs to establish", tags="Task", stage="M1",
    issue="https://github.com/moatus/livepeer-validator-track/issues/7",
    planned_artifact="deliverables/m1/claim-evidence-decision-note.md", review_status="Not submitted")
add("M1.3", "<p>''Question'' (issue #8). What representative behavior could extract rewards without delivering the intended benefit, and what useful activity could look similar?</p>\n<p>Brief not started. Seed scenarios awaiting specification: <$count filter=\"[tag[SC]field:status[seed]]\"/> (see [[View: Scenario pairs]]).</p>" + TASK_RECORDS,
    caption="Define adversarial scenarios and legitimate lookalikes", tags="Task", stage="M1",
    issue="https://github.com/moatus/livepeer-validator-track/issues/8",
    planned_artifact="deliverables/m1/initial-threat-scenarios.md", review_status="Not submitted")
add("M1.4", "<p>''Question'' (issue #14). What would need to change from current Livepeer behavior to reach the litepaper's proposed system?</p>\n<p>Not started. Component records use the CS template (see [[View: Component impact]]). Record the deployed version inspected in each record.</p>" + TASK_RECORDS,
    caption="Map the current system to the litepaper", tags="Task", stage="M1",
    issue="https://github.com/moatus/livepeer-validator-track/issues/14",
    planned_artifact="deliverables/m1/current-to-litepaper-impact-map.md", review_status="Not submitted")

json.dump(T, sys.stdout, indent=1, ensure_ascii=False)
