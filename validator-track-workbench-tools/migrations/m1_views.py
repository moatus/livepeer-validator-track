"""One-time seed: navigable views (tag View). Output is importable tiddler JSON."""

from __future__ import annotations

import json
import sys

V = []


def view(title, description, text):
    V.append({"title": title, "tags": "View", "description": description, "text": text.strip("\n")})


view("View: Concept index", "The paper's concepts with counts of linked records", r'''
\whitespace trim
<table class="vtw-grid"><tbody>
<tr><th>ID</th><th>Concept</th><th>Kind</th><th>In paper</th><th>RL</th><th>VD open</th><th>CL</th><th>SC</th><th>FR</th><th>EX</th><th>CS</th></tr>
<$list filter="[tag[LP]sort[title]]">
<tr>
<td><$link/></td><td><$text text={{!!caption}}/></td><td><$text text={{!!kind}}/></td><td><<vtw-status>></td>
<td><$count filter="[tag[RL]contains:concepts<currentTiddler>]"/></td>
<td><$count filter="[tag[VD]field:status[open]contains:concepts<currentTiddler>]"/></td>
<td><$count filter="[tag[CL]contains:concepts<currentTiddler>]"/></td>
<td><$count filter="[tag[SC]contains:concepts<currentTiddler>]"/></td>
<td><$count filter="[tag[FR]contains:concepts<currentTiddler>]"/></td>
<td><$count filter="[tag[EX]contains:concepts<currentTiddler>]"/></td>
<td><$count filter="[tag[CS]contains:concepts<currentTiddler>]"/></td>
</tr>
</$list>
</tbody></table>
''')

view("View: Open decisions", "Open VD records by concept, by decision label and by owning milestone", r'''
\whitespace trim
<p><$count filter="[tag[VD]field:status[open]]"/> open decisions. Split or resolved decisions are listed in [[VD]].</p>
<h2>By concept</h2>
<$list filter="[tag[LP]sort[title]]" variable="lp">
<%if [tag[VD]field:status[open]contains:concepts<lp>] %>
<h3><$link to=<<lp>>><$text text=<<lp>>/></$link>&#32;<$text text={{{ [<lp>get[caption]] }}}/></h3>
<$transclude $variable="vtw-table" filter="[tag[VD]field:status[open]contains:concepts<lp>sort[title]]"/>
<%endif%>
</$list>
<h2>By decision label</h2>
<$list filter="[[$:/vtw/labels]indexes[]]" variable="lab">
<h3><$text text=<<lab>>/>&#32;<span class="vtw-count"><$text text={{{ [[$:/vtw/labels]getindex<lab>] }}}/></span></h3>
<$transclude $variable="vtw-table" filter="[tag[VD]field:status[open]] :filter[get[classification]split[+]match<lab>] +[sort[title]]"/>
</$list>
<h2>By owning milestone</h2>
<$list filter="[tag[VD]field:status[open]get[owner_milestone]enlist-input[]] +[sort[]]" variable="m">
<h3><$text text=<<m>>/></h3>
<$transclude $variable="vtw-table" filter="[tag[VD]field:status[open]contains:owner_milestone<m>sort[title]]"/>
</$list>
''')

view("View: Claims matrix", "Claims by observer, evidence, limits and reward input (M1.2)", r'''
\whitespace trim
<p>Payment, execution, correctness, availability, independent demand and economic value are separate claims. ''reward input'' says whether the paper's reward uses the claim directly. <$transclude $variable="vtw-new" type="CL"/></p>
<table class="vtw-grid"><tbody>
<tr><th>Claim</th><th>Reward input</th><th>Labels</th><th>Who can observe</th><th>Evidence</th><th>Does not establish</th><th>Decisions</th><th>Scenarios</th></tr>
<$list filter="[tag[CL]sort[title]]">
<$let id=<<currentTiddler>>>
<tr>
<td><$link/><br/><$text text={{!!caption}}/><br/><<vtw-status>></td>
<td><$text text={{!!reward_input}}/></td>
<td><$text text={{!!classification}}/></td>
<td><$transclude field="observers" mode="inline"/></td>
<td><$transclude field="evidence_types" mode="inline"/></td>
<td><$transclude field="does_not_establish" mode="inline"/></td>
<td><$list filter="[tag[VD]contains:claims<id>sort[title]]" join=" "><$link/></$list></td>
<td><$list filter="[tag[SC]contains:claims<id>sort[title]]" join=" "><$link/></$list></td>
</tr>
</$let>
</$list>
</tbody></table>
''')

view("View: Scenario pairs", "Legitimate lookalikes beside adversarial cases; cooperative journeys (M1.3)", r'''
\whitespace trim
<p>Ordered cooperative, then market pressure, then strategic. <$transclude $variable="vtw-new" type="SC"/></p>
<h2>Cooperative journeys and unpaired cases</h2>
<$transclude $variable="vtw-table" filter="[tag[SC]!has[pair_with]sort[title]]"/>
<h2>Pairs</h2>
<$list filter="[tag[SC]has[pair_with]] :filter[get[pair_with]compare:string:gt<currentTiddler>] +[sort[title]]" variable="a">
<div class="vtw-pair">
<$list filter="[<a>] [<a>get[pair_with]]">
<div class="vtw-card">
<div class="vtw-kicker"><$text text={{!!sc_type}}/>&#32;<<vtw-status>></div>
<div><$link/>&#32;<strong><$text text={{!!caption}}/></strong></div>
<p><$transclude field="situation" mode="inline"/></p>
<p>''Paper:'' <$transclude field="litepaper_outcome" mode="inline"/></p>
<p>''Unsettled:'' <$transclude field="ambiguity" mode="inline"/></p>
<p>''Claims:'' <$list filter="[all[current]get[claims]enlist-input[]]" join=" "><$link/></$list> · ''Decisions:'' <$list filter="[all[current]get[decisions]enlist-input[]]" join=" "><$link/></$list></p>
</div>
</$list>
</div>
</$list>
''')

view("View: Parameter sheet", "Provisions with kind=parameter", r'''
\whitespace trim
<p>Values are as written in the paper; ''status'' says whether each is a proposal, illustrative or an open draft.</p>
<table class="vtw-grid"><tbody>
<tr><th>ID</th><th>Parameter</th><th>Value</th><th>Unit</th><th>Status</th><th>Governance-adjustable</th><th>Source</th><th>Concepts</th><th>Decisions</th></tr>
<$list filter="[tag[RL]field:kind[parameter]sort[title]]">
<$let id=<<currentTiddler>>>
<tr><td><$link/></td><td><$text text={{!!caption}}/></td><td><$text text={{!!value}}/></td><td><$text text={{!!unit}}/></td><td><<vtw-status>></td><td><$text text={{!!governance_adjustable}}/></td><td><$text text={{!!source_ref}}/></td>
<td><$list filter="[all[current]get[concepts]enlist-input[]]" join=" "><$link/></$list></td>
<td><$list filter="[tag[VD]contains:provisions<id>] [tag[VD]contains:conflicting_provisions<id>] +[sort[title]]" join=" "><$link/></$list></td>
</tr>
</$let>
</$list>
</tbody></table>
''')

view("View: Findings register", "Assumptions, hypotheses, inferences and findings with their status", r'''
\whitespace trim
<div class="vtw-callout">''<$link to="FR-01"/> <$text text={{FR-01!!caption}}/>'' (<$text text={{FR-01!!status}}/>): <$transclude tiddler="FR-01" field="statement" mode="inline"/></div>
<$list filter="[[$:/vtw/schema/FR]get[vocab-status]enlist-input[]]" variable="st">
<%if [tag[FR]field:status<st>] %>
<h3><$text text=<<st>>/>&#32;<span class="vtw-count">(<$count filter="[tag[FR]field:status<st>]"/>)</span></h3>
<table class="vtw-grid"><tbody>
<tr><th>ID</th><th>Statement</th><th>Would change it</th><th>Concepts</th><th>Tests</th></tr>
<$list filter="[tag[FR]field:status<st>sort[title]]">
<tr><td><$link/><br/><$text text={{!!caption}}/></td><td><$transclude field="statement" mode="inline"/></td><td><$transclude field="would_change" mode="inline"/></td>
<td><$list filter="[all[current]get[concepts]enlist-input[]]" join=" "><$link/></$list></td>
<td><$list filter="[all[current]get[experiments]enlist-input[]]" join=" "><$link/></$list></td></tr>
</$list>
</tbody></table>
<%endif%>
</$list>
''')

view("View: Component impact", "Current system to litepaper, by component and system area (M1.4)", r'''
\whitespace trim
<p>One CS record per contract, off-chain component or participant role in the current system. Record the deployed version inspected. <$transclude $variable="vtw-new" type="CS"/></p>
<%if [tag[CS]] %>
<$list filter="[[$:/vtw/schema/CS]get[vocab-layer]enlist-input[]]" variable="layer">
<%if [tag[CS]field:layer<layer>] %>
<h3><$text text=<<layer>>/></h3>
<table class="vtw-grid"><tbody>
<tr><th>ID</th><th>Component</th><th>Deployed version</th><th>Change</th><th>Concepts</th><th>Impact</th><th>Unknowns</th></tr>
<$list filter="[tag[CS]field:layer<layer>sort[title]]">
<tr><td><$link/></td><td><$text text={{!!caption}}/></td><td><$text text={{!!deployed_version}}/></td><td><$text text={{!!change}}/></td>
<td><$list filter="[all[current]get[concepts]enlist-input[]]" join=" "><$link/></$list></td>
<td><$transclude field="impact" mode="inline"/></td><td><$transclude field="unknowns" mode="inline"/></td></tr>
</$list>
</tbody></table>
<%endif%>
</$list>
<%else%>
<p class="vtw-none">No component records yet. M1.4 has not started.</p>
<%endif%>
''')

view("View: By participant", "Records tagged with each participant", r'''
\whitespace trim
<p>Participant: <$select tiddler="$:/temp/vtw/participant" default="operator">
<$list filter="[enlist{$:/vtw/participants!!list}]"><option value=<<currentTiddler>>><$text text=<<currentTiddler>>/></option></$list>
</$select></p>
<$let p={{{ [[$:/temp/vtw/participant]get[text]else[operator]] }}}>
<$list filter="LP RL VD CL FR SC EX CS" variable="t">
<%if [tag<t>contains:participants<p>] %>
<h3><$text text={{{ [[$:/vtw/schema/]addsuffix<t>get[plural]] }}}/>&#32;<span class="vtw-count">(<$count filter="[tag<t>contains:participants<p>]"/>)</span></h3>
<$transclude $variable="vtw-table" filter="[tag<t>contains:participants<p>sort[title]]"/>
<%endif%>
</$list>
</$let>
''')

view("View: Record finder", "Search and filter all records by text, type, concept, participant and status", r'''
\whitespace trim
\function vtw.sel.type() [[$:/temp/vtw/finder]get[type]!is[blank]else[all]]
\function vtw.sel.concept() [[$:/temp/vtw/finder]get[concept]!is[blank]else[all]]
\function vtw.sel.participant() [[$:/temp/vtw/finder]get[participant]!is[blank]else[all]]
\function vtw.sel.status() [[$:/temp/vtw/finder]get[status]!is[blank]else[all]]
<div class="vtw-finder">
<$edit-text tiddler="$:/temp/vtw/finder" field="q" tag="input" placeholder="Search all fields" class="vtw-q"/>
<br/>
<$select tiddler="$:/temp/vtw/finder" field="type" default="all">
<option value="all">all types</option>
<$list filter="LP RL VD CL FR SC EX FX CS" variable="t"><option value=<<t>>><$text text={{{ [[$:/vtw/schema/]addsuffix<t>get[plural]] }}}/></option></$list>
</$select>
<$select tiddler="$:/temp/vtw/finder" field="concept" default="all">
<option value="all">all concepts</option>
<$list filter="[tag[LP]sort[title]]"><option value=<<currentTiddler>>><$text text={{{ [all[current]addsuffix[ ]addsuffix{!!caption}] }}}/></option></$list>
</$select>
<$select tiddler="$:/temp/vtw/finder" field="participant" default="all">
<option value="all">all participants</option>
<$list filter="[enlist{$:/vtw/participants!!list}]"><option value=<<currentTiddler>>><$text text=<<currentTiddler>>/></option></$list>
</$select>
<$select tiddler="$:/temp/vtw/finder" field="status" default="all">
<option value="all">any status</option>
<$list filter="[tag[Record]] [tag[FX]] +[get[status]] +[sort[]]" variable="s"><option value=<<s>>><$text text=<<s>>/></option></$list>
</$select>
<$button class="tc-btn-invisible" tooltip="Clear filters"><$action-deletetiddler $tiddler="$:/temp/vtw/finder"/>clear</$button>
</div>
<$let hits={{{ [tag[Record]] [tag[FX]] +[search:*{$:/temp/vtw/finder!!q}] :filter[get[record_type]append[all]match<vtw.sel.type>] :filter[get[concepts]enlist-input[]append<currentTiddler>append[all]match<vtw.sel.concept>] :filter[get[participants]enlist-input[]append[all]match<vtw.sel.participant>] :filter[get[status]append[all]match<vtw.sel.status>] +[sort[title]format:titlelist[]join[ ]] }}}>
<p class="vtw-count"><$count filter="[enlist<hits>]"/>&#32;matching records</p>
<$transclude $variable="vtw-table" filter="[enlist<hits>]"/>
</$let>
''')

view("View: Crosswalk", "Old draft rows and sections to new record IDs", r'''
\whitespace trim
<p>Where each migrated record came from in [[SRC-M1-DRAFTS]]. Records without an entry were drawn directly from [[SRC-LP20]].</p>
<table class="vtw-grid"><tbody>
<tr><th>Migrated from</th><th>Record</th><th>Note</th></tr>
<$list filter="[has[migrated_from]!prefix[$:/]] :sort:string[get[migrated_from]]">
<tr><td><$text text={{!!migrated_from}}/></td><td><$link/>&#32;<$text text={{!!caption}}/></td><td><$transclude field="migration_note" mode="inline"/></td></tr>
</$list>
</tbody></table>
''')

view("View: Milestone dashboard", "Tasks, briefs, records introduced and review status", r'''
\whitespace trim
<p>Review status belongs to the task, never to a record. Only Shane sets Accepted.</p>
<table class="vtw-grid"><tbody>
<tr><th>Task</th><th>Question / brief</th><th>Planned artifact</th><th>Records introduced</th><th>Records last changed</th><th>Review status</th></tr>
<$list filter="[tag[Task]sort[title]]">
<tr><td><$link/><br/><$text text={{!!caption}}/></td>
<td><a href={{!!issue}} target="_blank" rel="noopener noreferrer">issue</a></td>
<td><code><$text text={{!!planned_artifact}}/></code></td>
<td><$count filter="[tag[Record]field:introduced_by<currentTiddler>] [tag[FX]field:introduced_by<currentTiddler>]"/></td>
<td><$count filter="[tag[Record]field:last_changed_by<currentTiddler>] [tag[FX]field:last_changed_by<currentTiddler>]"/></td>
<td><$text text={{!!review_status}}/></td></tr>
</$list>
</tbody></table>
''')

view("View: Reference check", "Missing link targets, missing concepts and missing locators", r'''
\whitespace trim
<p>Browser-side check. `vtw.py lint` also checks target types, vocabularies, ID patterns, line ranges and scope terms.</p>
<h3>Links to missing records</h3>
<table class="vtw-grid"><tbody>
<tr><th>Record</th><th>Field</th><th>Missing target</th></tr>
<$list filter="[tag[Record]] [tag[FX]] +[sort[title]]" variable="r">
<$list filter="[[$:/vtw/relations]indexes[]]" variable="f">
<$list filter="[<r>get<f>enlist-input[]!is[tiddler]]" variable="m">
<tr><td><$link to=<<r>>/></td><td><$text text=<<f>>/></td><td class="vtw-missing"><$text text=<<m>>/></td></tr>
</$list>
</$list>
</$list>
</tbody></table>
<h3>Records without concepts</h3>
<$transclude $variable="vtw-table" filter="[tag[Record]!tag[LP]] :filter[get[concepts]else[]is[blank]] +[sort[title]]"/>
<h3>Records without a source locator</h3>
<$transclude $variable="vtw-table" filter="[tag[Record]!has[source_ref]] +[sort[title]]"/>
<h3>Unreciprocated scenario pairs</h3>
<$transclude $variable="vtw-table" filter="[tag[SC]has[pair_with]] :filter[get[pair_with]get[pair_with]else[-]!match<currentTiddler>] +[sort[title]]"/>
''')

view("View: Cooperative flow", "How a customer payment and a round's emissions move, step by step", r'''
\whitespace trim
<p>Reconstructed from the paper for an honest customer and a node delivering an agreed job. Customer USDC and LPT emissions are separate ledgers; LPT and USDC are never added.</p>
<table class="vtw-grid"><tbody>
<tr><th>#</th><th>Step</th><th>Provisions</th><th>Open</th></tr>
<tr><td>1</td><td>Customer or agent selects a listed node and pays USDC at the node's USD price.</td><td>[[RL-08]] [[RL-32]]</td><td>[[VD-02]] [[VD-03]]</td></tr>
<tr><td>2</td><td>The fee splits: node cut to the node, network fee to buy-back-and-burn.</td><td>[[RL-33]] [[RL-34]] [[RL-35]]</td><td>[[VD-15]]</td></tr>
<tr><td>3</td><td>The network fee buys LPT on the market; all purchased LPT is burned.</td><td>[[RL-36]] [[RL-37]] [[RL-41]]</td><td>[[VD-16]] [[VD-18]]</td></tr>
<tr><td>4</td><td>Separately, a governed mint sets round emissions. No schedule is selected.</td><td>[[RL-40]] [[RL-47]] [[RL-48]] [[RL-49]] [[RL-50]]</td><td>[[VD-14]]</td></tr>
<tr><td>5</td><td>Emissions split to nodes, validators and treasury.</td><td>[[RL-53]] [[RL-54]] [[RL-55]] [[RL-56]]</td><td>[[VD-17]]</td></tr>
<tr><td>6</td><td>Each node's share is min(fee share, stake share); delegated stake raises the ceiling.</td><td>[[RL-10]] [[RL-13]] [[RL-16]]</td><td>[[VD-05]] [[VD-06]]</td></tr>
<tr><td>7</td><td>Active validators score nodes; the median scales the MFS-eligible reward.</td><td>[[RL-23]] [[RL-24]] [[RL-25]]</td><td>[[VD-07]] [[VD-09]] [[VD-10]]</td></tr>
<tr><td>8</td><td>Round n becomes claimable at n+7 using the claim-time median; node and delegators share it under their cuts.</td><td>[[RL-30]] [[RL-31]] [[RL-15]]</td><td>[[VD-11]]</td></tr>
<tr><td>9</td><td>Envelope left unassigned by MFS, or withheld by scores, has no stated disposition.</td><td>[[RL-10]] [[RL-24]]</td><td>[[VD-12]]</td></tr>
</tbody></table>
<p>Worked numbers: [[EX-01]] (illustrative, fixed envelope).</p>
''')

json.dump(V, sys.stdout, indent=1, ensure_ascii=False)
