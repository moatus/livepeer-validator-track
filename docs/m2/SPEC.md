# M2 specification: test litepaper incentives and evidence limits

Version **0.12 · 2026-10-14**. Status: **drafted**. Revision history is at the end. Owner: Shane (@moatus).

This specification defines M2 and its shared modeling contract. The completed September pilot is preserved in §5. Slices 1, [2](SLICE-02.md) and [2b](SLICE-02B.md) are complete and reviewed by the owner (2026-10-14). The remaining program is consolidated into topical slices under §4, with study identities preserved. How the work is run, reviewed and handed between agents is in the [runbook](RUNBOOK.md). The milestone's definition is in [MILESTONES.md](../../MILESTONES.md#m2--test-litepaper-incentives-and-evidence-limits); this file does not change it.

## 1. Purpose and boundary

M2 tests the litepaper. It reassembles the mechanisms M1 took apart, tests the critical questions with small reproducible examples and focused evidence inquiries, and records what would resolve each concern. It hands M3 the concerns that plausible completions of the paper leave unresolved, together with the areas the paper leaves unaddressed.

Boundaries that hold for every slice:

- **Litepaper only.** M2 examines the paper's own mechanisms and the readings the paper allows. It does not describe or compare against a successor mechanism. The October paper proposes a fee-independent decaying emissions ceiling; a fixed one-round allowance may represent that schedule at a declared round. The September pilot’s fixed-pool control remains historical, not a claim about October policy.
- **Small, not simulated.** A table, a calculation or a bounded case comparison that answers its question is enough. No network simulation, agent-based framework or Monte Carlo study is in scope for M2. If a question appears to need one, stop and record why in the run log; the owner decides.
- **Conditional results.** Every result names the rules, interpretations and assumptions it holds under. A profitable deviation with everyone else held fixed is not an equilibrium and not evidence of prevalence. Modelled vulnerability and observed prevalence are reported separately.
- **Distinct claims.** Payment, execution, correctness, availability, independent demand and economic value are separate claims (CL-01 to CL-06). The paper's multiplier concerns dishonesty, not service quality.
- **Counterevidence stays.** The paper's defenses get a fair test. Where a defense holds, that is a result and goes into the record.

## 2. What a complete M2 leaves behind

M2 is complete when a reviewer can choose any of the nine critical questions (GT-01 to GT-04, GT-06 to GT-10) and find three things: an assessment under stated conditions, a result they can rerun or a table they can trace, and a disposition (build work, more evidence, incentive issue, policy choice, or M3).

**Where each critical question gets its disposition**

| Critical question | Closed by |
| --- | --- |
| GT-01 | Purpose half: Slices 1, 2, 2b and EX-04/EX-07 (does not separate). Correctness half: E2. |
| GT-02 | Slice 3 |
| GT-03 | Slices 1, 2, 2b |
| GT-04 | Close pass, using P1 movement data; the SC-27/SC-28 example runs only if P1 shows material movement |
| GT-06 | E2 |
| GT-07 | Close pass, using P1's selection-rule note and the EX-06/EX-08 rerouting controls |
| GT-08 | Close pass, rule reading |
| GT-09 | Slice 3, using P1 concentration data |
| GT-10 | Close pass: unresolved, distinct from valuation sensitivity, routed to M4.1 |

| Step | Artifact | Where it lives |
| --- | --- | --- |
| M2.1 How the mechanisms behave together | Rule-interpretation register; participant and control map; one timeline; for each intended relationship, an assessment (supported, conditional, contradicted, unresolved); a ranked test list that confirms or replaces each proposed test | Workbench step page M2.1 and CN records |
| M2.2 Testing the critical questions | One result per consequential critical question: economic models (generated workbook or script with a verifier), evidence tabletop packets, and short current-system data notes | `experiments/m2/<slug>/`, described by EX and FX records, summarized on step page M2.2 with FR and CN records |
| M2.3 What would resolve each concern? | Every design question and finding classified by what would resolve it; each concern assessed (finding status `supported`, `weakened` or `rejected`; critical-question status `significant`, `not-significant` or `unresolved`); plausible completions compared; M3 handoff list with the paper's retained strengths beside it | Workbench step page M2.3, FR updates and CN records |

These support the three existing M2 deliverables. They are not a parallel report. Reviewed versions are recorded by commit in the [deliverable register](../../deliverables/README.md), as for M1.

**Connected result required.** M2 also leaves one reusable scenario ledger that connects capability entry, price, outside demand and routing, controlled purchases, execution costs, stake, commissions and validator scores. Later studies amend this ledger or explicitly explain why they cannot. An inventory of independent tests is insufficient. Report job volume, customer spending, network fees, operator and delegator receipts and net income, buyback spending and tokens burned, scheduled ceiling, actual issuance and unminted node allowance, with effects on non-selected operators. [Slice 2](SLICE-02.md) establishes the first bounded implementation; remaining slices test its deferred assumptions.

**"Unresolved" counts as a result** only when the inquiry has identified the missing rule or evidence that leaves it unresolved. A test that was proposed and never run does not count.

## 3. Methods

| Method | Use it for | Form | Must include |
| --- | --- | --- | --- |
| **Economic example** | Payoffs, break-even points, which assumption drives a sign | `build.py` generates CSV or Markdown tables (an XLSX workbook only where readers need to edit inputs); `verify.py` checks independent arithmetic against hand-computed fixtures; pinned dependencies; one reproduce line | Inputs labelled paper-proposed, illustrative or measured; LPT and USDC kept separate until a stated price converts them; each receipt counted once; the cooperative case first |
| **Evidence tabletop** | Whether obtainable evidence separates a case from its legitimate lookalike before the claim | A structured case packet (Markdown plus a CSV matrix) with a completeness check script, `verify.py` | The alleged violation stated first; acceptable error and cost committed before outcomes are examined; evidence revealed in arrival order up to round n+7; each claim marked established, contradicted or unknown |
| **Current-system data note** | How today's network actually behaves, where a model's assumption depends on it | A short note plus the query script and a dated, versioned data extract | Source, block range or date range, query, and a label that this is today's system, not a forecast for the litepaper |
| **Rule reading** | Questions about governance or rule sequencing that need no numbers | A timeline or comparison table on the step page | The stated rule variants and where the result changes between them |

Synthetic case packets can test the logic of a judgment. They cannot establish whether evidence exists in practice, how long review takes, or how often reviewers err. Claims of that kind need inspected sources or a real, bounded exercise.

### Shared measured network baseline

All network-grounded M2 modeling uses the single frozen artifact [`livepeer-arbitrum-2026-10-09-v1.json`](../../experiments/m2/network-snapshot/livepeer-arbitrum-2026-10-09-v1.json), through its [reader and usage contract](../../experiments/m2/network-snapshot/README.md). Record the snapshot ID, content hash, chosen fee series and observation window/round in each result. Keep all pools and relevant fee recipients in network denominators even when modeling only selected operators. Measured current-system facts stay separate from the model's declared litepaper version, costs, scores, ownership assumptions, strategic choices and overrides. Refreshes receive new versions; do not modify the baseline in place. The original Slice 1 illustrative cases and arithmetic fixtures retain their stated inputs and historical results; network-grounded extensions load this shared baseline. The snapshot remains drafted until separately reviewed.

Agent readers use `experiments/m2/network-snapshot/query.py catalog` to discover fields and exact source paths, then retrieve bounded summaries, operator rows, round pools or evidence extracts. Do not ingest the whole snapshot into an agent's context. Bulk calculations use the Python reader locally and return only their outputs; every extract carries the snapshot identity/hash and selected source paths. The [agent access instructions](../../experiments/m2/network-snapshot/README.md#agent-access-without-loading-the-dataset-into-context) define pagination and output limits.

## 4. How M2 is executed: slices

M2 runs as **slices**. A slice carries one concern through all three steps: its part of the M2.1 reconstruction, its M2.2 tests and its M2.3 consolidation. The step pages accumulate across slices. Slice 1 is run first as a **pilot**: it is scoped to exercise every stage, gate and handoff in the runbook while keeping the research content small, so that what it teaches is about the process. The runbook and this specification are updated from its retrospectives before Slice 2 starts.

Each slice has four stages:

| Stage | Step | Output | Can run in parallel with |
| --- | --- | --- | --- |
| A — Reconstruct | M2.1 | Register rows, control map, timeline, confirmed tests, M2.1 conclusion for the slice | — |
| B — Model | M2.2 | Economic example (EX + FX records, `experiments/m2/…`) | C |
| C — Evidence | M2.2 | Evidence tabletop (EX + FX records, `experiments/m2/…`) | B |
| D — Consolidate | M2.3 | Classifications, concern assessment, completions compared, M3 handoff items | — |

A slice may omit B or C where its question needs only one. Every stage ends at a review gate (runbook §6).

### Active sequence and preserved study identities

The October preparation is authorized; it does not imply owner acceptance of the pilot or publication. The second numbered slice is now the connected model. Historical references to “Slice 2 — Evidence before the claim” mean the deferred study **E2** below, not the new Slice 2. Existing case and experiment IDs retain their identities.

| Slice / study | Critical questions | Cases and method | Sequence and dependency |
| --- | --- | --- | --- |
| **1 — Self-funded real usage (September pilot)** | GT-03; GT-01 pair | SC-07 / SC-23; SC-01; EX-03 and EX-04 | Completed; reviewed by the owner, 2026-10-14 ([#26](https://github.com/moatus/livepeer-validator-track/issues/26)). §5 preserves original source and scope. |
| October reconciliation | GT-03 and affected M1/M2 claims | EX-05; `experiments/m2/october-reconciliation/` | Migration bridge: scheduled ceiling, MFS, non-minting and surviving evidence limits; does not relabel EX-03 as October. |
| **2 — Capability, pricing and self-funded traffic** | GT-03, GT-07; bounded GT-01, GT-04, GT-10 inputs | [Full brief](SLICE-02.md); EX-06, EX-07 | Completed; reviewed by the owner, 2026-10-14 ([#27](https://github.com/moatus/livepeer-validator-track/issues/27)). Shared snapshot, cooperative → competition → strategic cases, focused evidence comparison and one bounded response. |
| **2b — Strategic self-funding across network conditions** | GT-03; bounded GT-01, GT-04, GT-07, GT-10 inputs | [Defined study](SLICE-02B.md); [implementation phases](SLICE-02B-IMPLEMENTATION.md); largest/middle/lower stake, network structure, outside traffic, market scale from measured to fee-dominant, feasible optima and honest-party losses | Completed; reviewed by the owner, 2026-10-14 ([#28](https://github.com/moatus/livepeer-validator-track/issues/28)). Three sequential M2.1/M2.2/M2.3 workloads. Extends the shared ledger; preserves original results and E2/P1/studies 3–8. |
| **P1 — Current-system data notes** | HQ-01, HQ-03; inputs to GT-04, GT-07, GT-09 | Stake movement over a recent window from BondingManager bond, unbond, rebond and transfer events. Stake concentration, and the stake needed to seat a majority of validators when declined seats pass down the rank. The raw redeemed-fee series, so a genuine surge has a measured shape. Today's gateway selection rule, read from go-livepeer. Method: current-system data notes with query scripts and a dated extract. No model. | Runs first. Needs an owner data-access decision for chain history. Its movement result decides whether the GT-04 example runs in the close pass. The frozen snapshot does not establish movement speed or capability demand. Tracked in [#29](https://github.com/moatus/livepeer-validator-track/issues/29). |
| **E2 — Evidence and operator response (absorbs study 4)** | GT-01 correctness half; GT-06 | SC-11 / SC-10 as a tabletop in the EX-04 packet format. SC-16 / SC-17 answered from P1's fee series plus a reading of what the seven-round delay can observe. SC-07 / SC-06 recorded as inheriting the release-testing verdict, with the reason stated. SC-25 / SC-26 followed through notice, response, disclosure and correction before the claim boundary. An inventory of records that exist today (probabilistic tickets, winning tickets, transcoding verification, capability adverts, orchestrator statistics, invoice price per job): who holds each, whether it is public, and which claim CL-01 to CL-07 it bears on. | Opens after the VD-19 decision and after P1. No new synthetic purpose matrices. Bridges directly to M4.2. Keeps "defense burden" as its own conclusion. Tracked in [#30](https://github.com/moatus/livepeer-validator-track/issues/30). |
| **3 — Will validators score defensibly?** | GT-02, GT-09 | SC-09, SC-19–SC-21, SC-24, SC-35–SC-37. One payoff table for a validator choosing to score from evidence, stay lenient, abstain, or join an unsupported low score, under the full-set median and a quorum variant. It states the 1% share split, with compensation declining on the 840-round half-life. A seat-control cost table from P1 concentration. Uses the EX-08 result that unminted node allowance is not redistributed, so zeroing a rival yields no direct reward gain. | Opens after P1 and E2. Its evidence input is the established "does not separate" result. Feeds tested scores and costs into the shared ledger. Tracked in [#31](https://github.com/moatus/livepeer-validator-track/issues/31). |
| **Close — M2 consolidation pass** | GT-04, GT-07, GT-08, GT-10; final M3 handoff | Dispositions for studies 5 to 8 below, assembled from rule readings, P1 and existing results. Final M3 handoff list with the paper's retained strengths beside it. | Last. Satisfies §2 for every critical question. Tracked in [#32](https://github.com/moatus/livepeer-validator-track/issues/32). |
| 4 — Defending a reward | GT-06 | Merged into E2. | Identity retained; no separate run. |
| 5 — Delegation in time | GT-04 | SC-27 / SC-28 as a one-table round-by-round example, using P1's measured movement rate, EX-08 added-stake arithmetic and the 21-round lock. | In the close pass. Runs only if P1 shows material movement. Otherwise the disposition is "unresolved: measured movement negligible", with the measurement cited. |
| 6 — Access to paid work | GT-07 | Disposition from P1's selection-rule note and the EX-06/EX-08 rerouting controls. | In the close pass. No demand, elasticity or discovery model. |
| 7 — Rule changes while rewards are pending | GT-08 | SC-32–SC-34 as a rule-reading timeline, no numbers. | In the close pass. Procedure design belongs to M4.3. |
| 8 — LPT price | GT-10 | Carries EX-08's valuation sensitivity. Disposition: unresolved, distinct from valuation sensitivity; needs a buyback execution design and liquidity evidence. The September mint-price-oracle branch is retired under October, which removes that dependency. | In the close pass; routed to M4.1. |
| 1b — Historical follow-up | GT-03 | Deferred. Slice 2b's retention, cost, valuation and schedule overrides cover the §5.9 variants under October. | Runs only for an explicit historical question. |

**Stop rule for remaining briefs.** Every remaining brief states three things: the decision the slice could change; the new evidence or mechanism it examines that existing work does not; and the result that would end the inquiry. No further GT-03 modeling runs unless P1 shows stake acquisition is cheap and fast enough to reopen the stake-cap defense.

### Source and interpretation contract

Active work cites [October source](../litepaper-2.0.md), [authoritative PDF](../sources/litepaper-2026-10.pdf), and the source hash. Use PDF page plus section/quotation; line locators refer to that exact extraction only. September `L…` references in §5–6 refer exclusively to [the archived September text](../sources/litepaper-2026-09.md). Never reuse them against October.

October resolves the choice among September emissions concepts by stating a decaying token ceiling, but its appendix still describes work-proportional rewards weighted by scores. Register the surviving main-text/appendix mismatch; do not call it resolved. Main-text MFS is the base reading; keep a bounded appendix comparison or explicitly document which conclusions remain reading-dependent. Distinguish scheduled emission allowance, claimable node rewards, eventual actual mint and unminted node allowance. Validator and treasury portions mint in full under the paper; score application and claim timing must be declared.

Every register row labels scope as **computed**, **stated premise** or **deferred**. Separate sweep inputs from alternate rule readings. A test cannot confirm its own premise. Compare paper-stated or plainly implied completions; identify exploratory choices separately and never credit an uncomputed destination as a defense.

### Slice 2b execution contract

The owner requested Slice 2b's design to be completed before its implementation phases. SLICE-02B.md fixes the finite network/actor/market comparisons and affordable strategic question. Its inputs are materialized in M2.1, tested in M2.2 and consolidated in M2.3; there is no design phase. Each phase has one fresh `gpt-6.1-sol` writer and one fresh `claude-opus-5-5` reviewer. The integrator alone imports and commits. The defined budget is 54 core profiles across three market scales from the measured ratio to near parity, plus named controls and finite supplements, not an open-ended simulation. Agent gates do not confer owner research review. Exact phases, acceptance and boundary rules are in SLICE-02B-IMPLEMENTATION.md.

## 5. Slice 1 — Self-funded real usage (historical September pilot)

**Historical specification.** This section records the rules and IDs under which EX-03/EX-04 were produced. Its September source lines, emissions concepts, original slice numbering and future-tense instructions are retained for reproducibility, not as the active work order. The October reconciliation and §4 supersede its current-source assumptions and next-run sequence. Evidence verdicts mean obtainable evidence separates the pair; a procedural cut for failure to explain is a consequence, not proof of separation. Read that clarification with the original §5.5 schema.

Slice 1 has two purposes. Its research purpose is the core stake-cap (MFS) question: does the stake ceiling limit the payoff from paying one's own node for real work, under each reading of the node reward and each emissions concept? Its process purpose is to exercise every part of the runbook once (§5.10). Where the two pull apart, the scope stays small and the deferred items are listed in §5.9.

### 5.1 Question

**Under each emissions concept the paper lists, and under each reading of the node reward the paper allows, does one additional self-funded real job return more to the organization that controls both payer and node than it costs? Where does the return change sign? And can a validator, by the time the reward is claimable, tell that job apart from the operator's own release testing using evidence it can obtain?**

The two halves are reported separately (SC-07 requires this). A positive return is not a finding of misconduct: GT-03 strengthens only if the missing intended contribution is defined *and* the return is positive under named assumptions. A nonpositive return in a tested region weakens the concern there.

### 5.2 Inputs from M1 (read before starting)

| Kind | Records |
| --- | --- |
| Critical questions | GT-03 (full), GT-01 (its smallest test, for SC-07 beside SC-23) |
| Cases | SC-07, SC-23, SC-01; SC-06 for context only (its arithmetic matches SC-23; its evidence pair belongs to Slice 2); claim timing SC-14, SC-15, SC-22 |
| Findings | FR-01, FR-19, FR-23, FR-24, FR-26, FR-35, FR-40, FR-41, FR-42, FR-45 |
| Design questions | VD-05, VD-06, VD-09, VD-12, VD-14, VD-15, VD-19 |
| Conclusions | CN-05, CN-07, CN-17, CN-19, CN-20 |
| Claims | CL-01, CL-02, CL-03, CL-05, CL-06, CL-07 |
| Experiment | EX-01 and `experiments/m1/baseline-accounting/` |
| Litepaper | L51–63, L79–90, L107–109, L117–121, L128–172, L196, L205–235. Two passages carry most of the weight and should be quoted, not paraphrased with emphasis: L172 (the stake cap and the emissions cap do not stop a larger share of a fixed pool; "that's what validator scoring and the 7-round rewards delay are for") and L109 (the delay is argued for a one-round fee spike) |
| Step page | M2.1 "Reconstruction checklist from the M1 sample" (rules to state, consequences counted once, timeline) |

### 5.3 Stage A — Reconstruct the slice (M2.1)

Produce, on the M2.1 step page:

1. **Rule-interpretation register rows.** A table, one row per open rule this slice actually uses; rules other slices need wait for those slices. Columns: register ID (`I-01`, `I-02`, …, never reused), rule, design question, reading used in the base case, variants carried, and whether a variant changes the result (filled in after Stage B). At minimum:
   - node entitlement: main-text MFS, `min(fee share, stake share) × median`, as the base case; the appendix's "proportional to work, weighted by multiplier" as a variant (VD-06). Carry both: they differ on whether the stake ceiling exists.
   - emissions concept: concepts 1, 2 and 3 (L134–136) and a fixed-pool control (VD-14); how an annual figure becomes a per-round figure; rounds per year `R_y` (no source establishes a round length: CS-04 records that the protocol source does not; the paper's wording treats a round as about a day, L96, L101, L185). Use `R_y = 365`, labelled illustrative, and state every result per unit of network fees (`x/F`, `Δ/x`) so that `R_y` only scales dollar labels and the cap's position; whether the round's mint reads that round's fees (the base reading) or a longer window; the concept-1 baseline ratio, 32 as stated; the 28.8 figure (FR-41) is recorded in the register as a deferred variant (§5.9).
   - unassigned and withheld node emissions: not redistributed in the base case (VD-12). Do not assume they go to accusers or rivals.
   - fee split: 50/50 (VD-15); whether the operator shares the node cut with delegators.
   - price: the mint conversion price and the claim-time value of LPT; a buyback price effect held at zero and labelled as an assumption.
   - validator emission share: held at zero in the organization's payoff, stated as an assumption. At `s = 0.20` the node is plausibly among the top 33 by stake, and the 1% validator share (L84, L232) would add a receipt whose division rule is open (VD-17).
   - claim timing: claim at n+7 in the base case; a later claim changes the payout only if the median differs (VD-11, VD-31).
   - self-dealing standard for Stage C: a narrow standard (specified deceptive or reward-manipulating conduct) and a broad one (circular funding or purpose). Neither is a common-ownership ban or a settled rule of the paper (VD-09).

   Do not fill an open rule with the reading that makes the concern look strongest. Where unsure, carry two readings.
2. **Control map** for three setups: an independent customer (SC-01), an integrated organization that controls payer and node (SC-07, SC-23), and the same organization with outside delegators. The third setup is mapped but not modelled in the pilot (§5.9). For each: who controls customer funds, routing, operator addresses, stake, the reward claim and outside reward recipients.
3. **Timeline** for the slice: the job and settlement in round n, fee attribution, stake snapshot, evidence arrival, score updates, the first claimable round n+7, a later claim, and the 21-round stake movement.
4. **Intended relationships checked.** FR-26, FR-19, FR-35, FR-40 and FR-23 set out the paper's reasons. For each, state the condition it needs and whether the slice's tests can assess it.
5. **Structural overlap noted.** The highest stake ceilings sit with the nodes eligible to validate (FR-42, L81–83). Record, for the `s = 0.20` position in Stage B, whether such a node has room below its ceiling, and hand that to Stage D and Slice 3 as an input. High stake and common ownership are not misconduct, and no real operator is discussed.
6. **Tests confirmed or replaced.** Confirm, amend or replace the proposed tests on GT-03 and GT-01 (SC-07 beside SC-23) against §5.4 and §5.5. Expected amendments, each to be recorded with its reason: GT-01's test begins with SC-06 beside SC-07 and SC-23, and the pilot takes only SC-07 beside SC-23 (SC-06 moves to Slice 2); GT-03's test lists SC-03, SC-04 and outside reward ownership, which the pilot maps but does not model (§5.9). Stage A edits GT-03's and GT-01's `smallest_test` fields to match, and records each amendment in the run log and on the step page.
7. **One conclusion record** (CN, `task: M2.1`) stating what the reconstruction establishes for this slice and what it hands to Stage B and C.

### 5.4 Stage B — Economic example (M2.2): `EX-03` "Self-funded real job: incremental return"

**Location:** `experiments/m2/self-funded-return/` containing `build.py` (writes CSV and Markdown tables beside itself), `verify.py` and `README.md`. No XLSX workbook, LibreOffice recalculation or charts in the pilot. Generated outputs are not committed. Reuse EX-01's fixture pattern, but do not modify `experiments/m1/`.

**Notation** (one round; all USDC amounts per round):

| Symbol | Meaning | Base value and status |
| --- | --- | --- |
| `F` | Network fees per round before the addition | The paper's year-0 figure, $1.1M per year (L148), divided by `R_y`; paper-reported figure, illustrative scale |
| `f` | Node A's outside fees | `f/F ∈ {s/2, 2s}`: one start below the stake ceiling, one start above it; illustrative |
| `s` | A's stake share | {0.01, 0.05, 0.20}; illustrative |
| `x` | Added self-funded fees | Swept, as a fraction of `F`, from 0 until A's fee share passes `s` and beyond |
| `n` | Node cut | 0.5 (paper-proposed, L119) |
| `κ` | Execution cost per USDC of job | 0.3; illustrative (0.7 deferred, §5.9) |
| `u` | Internal use value per USDC of job | 0 for SC-07; > 0 for the SC-23 lookalike; illustrative |
| `ω` | Share of A's stake owned by the organization | 1.0 in the pilot (outside delegators deferred, §5.9); illustrative |
| `ρ` | Operator's retained share of the node cut | 1.0 (undelegated in the pilot) |
| `φ` | Operator's LPT reward cut | 1.0 in the pilot (no outside delegators to share with) |
| `m` | Median score at claim | 1 in the base case |
| `P_mint`, `P_claim` | USDC/LPT conversion at mint and value at claim | Equal in the base case; illustrative |
| `E` | Round emissions (LPT) before the 94/1/5 split | Per concept, below |

**Cash to the organization** (internal transfer cancelled, network half lost once):

```
ΔCash = −x + n·x·[ρ + (1−ρ)·ω] − κ·x + u·x
```

**Node reward (LPT)**, with `N = 0.94 · E` and fee share `a = (f+x)/(F+x)`:

- Base reading (main-text MFS): `R = N · min(a, s) · m`
- Appendix variant: `R = N · a·m / Σ_i (a_i·m_i)`. With every other node at `m = 1` this is `N · a·m / (a·m + 1 − a)`. There is no stake term.

**Emissions per round** (`R_y` = rounds per year from the register):

- **C0 fixed-pool control:** `E` fixed. Calibrate it to equal C1's pool at `x = 0`, so that C0 isolates share-taking from pool growth.
- **C1 declining share of fees, with cap** (base reading: the round's mint reads the round's fees): `E_USD = min(ratio_y · (F+x), 50,000,000 / R_y)`, `ratio_0 = 32`; year 0 only in the pilot (years 4 and 8 deferred, §5.9). At the year-0 scale the cap binds once network fees exceed $1.5625M per year, so a sweep of `x/F` beyond about 0.42 crosses into the capped region. `E = E_USD / P_mint`.
- **C2 fees plus mint held at $35M:** `E_USD = max(0, 35,000,000/R_y − ((F+x) − F_0))`, where `F_0` is the baseline per-round fee level. Each added dollar of fees lowers the mint target by a dollar while it is positive (FR-45). Note in the register that C2's baseline is $35M while C0 and C1 start from 32 × $1.1M = $35.2M, and that FR-45 records two readings of concept 2; at the year-0 scale both give a slope of −1.
- **C3 participation-based inflation with a 2–10% band:** the mint does not read fees, so `E` is unchanged by `x` within the round. Set `E` equal to C0's, labelled illustrative. Report it, and note that its incremental arithmetic then equals C0's.

**Organization's LPT gain and incremental return:**

```
R_before_org = R_before · [φ + (1−φ)·ω]        (R at x = 0, median 1)
R_after_org  = R_after  · [φ + (1−φ)·ω]
Δ            = P_claim · (R_after_org − R_before_org) + ΔCash
```

Report the average return `Δ/x` and the marginal return `∂Δ/∂x` side by side, because they diverge once `a` passes `s`. Report the break-even `x` or `s` where `Δ` changes sign, or "no sign change in the swept range", which is a valid result.

**Validation response sensitivity.** Without the job, the median is 1. With the job, the median at claim is 0 with probability `q`, otherwise 1. A zero median removes the node's *whole* round reward, including the reward on its outside fees:

```
E[Δ] = (1−q) · P_claim · R_after_org − P_claim · R_before_org + ΔCash
q*   = Δ(q=0) / (P_claim · R_after_org)       ("none" when Δ(q=0) ≤ 0)
```

Apply the same `q` to SC-23, where a zero median is a false cut, and report its cost there. Label `q` as a sensitivity, not a detection estimate. Whether any `q > 0` is supportable is the Stage C and GT-01 question.

**Sweep design (pilot).** Vary only: concept (C0–C3), entitlement reading (MFS, appendix), `s`, the starting `f/F` and `x/F`, with `x/F` running far enough to cross both the point where the stake ceiling binds and the C1 cap. Keep every other input at its base value. The code keeps `ω`, `ρ`, `φ` and `κ` as inputs so that Slice 1b can vary them without restructuring. Present each concept as a small table of `Δ/x` and `∂Δ/∂x` over `x/F` by `s`. Mark the region where `a < s` (a higher fee share raises the eligible share) and the region where `a ≥ s` (the stake ceiling binds).

**Comparisons in the same tables:** an outside job (SC-01: the organization pays nothing, receives the node cut and the reward change), self-funded (SC-07, `u = 0`) and release testing (SC-23, `u > 0`). The arithmetic for SC-07 and SC-23, and for related-party production (SC-06), differs only in `u`. Report that, rather than letting a table imply that the purpose shows in the numbers.

**Hand-checkable fixtures for `verify.py`** (`checked_by: verify.py`, FX `status: illustrative`; extend as needed). Unless stated: `F = 3,000`, `x = 100`, `n = 0.5`, `ρ = ω = φ = 1`, `κ = 0.3`, `u = 0`, `m = 1`, `R_y = 365`, `P_mint = P_claim`.

| Fixture | Setup | Expected |
| --- | --- | --- |
| EX-03.F1 | C0, MFS, `s = 0.05`, `f = 300` (`a` 0.100 → 0.129, binding throughout) | `ΔR = 0`; `Δ = −80` |
| EX-03.F2 | C1 year 0, MFS, `s = 0.05`, `f = 30` (`a` 0.010 → 0.042, below `s`); cap not binding (`32 · 3,100 < 50,000,000/365`) | `R_USD = 0.94 · 32 · (f+x)`, so `ΔR_USD = 3,008`; `Δ = +2,928`; independent of `P` |
| EX-03.F3 | As F2, but `f = 300` (binding throughout) | `ΔR_USD = 0.94 · 32 · s · x = 150.4`; `Δ = +70.4` |
| EX-03.F4 | C2 with a positive target | `∂E_USD/∂x = −1` |
| EX-03.F5 | C0, appendix variant, all `m = 1`, `f = 300` | `ΔR = N · [(f+x)/(F+x) − f/F]`, with no dependence on `s` |
| EX-03.F6 | Any concept, `q = 1` | `E[Δ] = −P_claim · R_before_org + ΔCash` |
| EX-03.F7 | As F1, with `u = 1` | `Δ = +20`: a lookalike job can be ordinary business |
| EX-03.F8 | `F = 0` and `x = 0` | `undefined/needs rule`, as in EX-01 |

These fixtures are arithmetic checks. They are not findings: F2's large return holds only under concept 1, the main-text reading, a fee share below stake share and full ownership, and it shows nothing about contribution or detectability.

**Records to create:** `EX-03` (`stage: M2`, `introduced_by: M2.2`, `status: reproducible` once `verify.py` passes from a clean clone), its FX rows, and one FR per result that could change a recommendation, using Stage B's ID block (§5.7). Each FR states its conditions, its counterevidence in `would_change`, and `resolved_by` / `spec_settles` / `still_to_test`. Add the new FR IDs to GT-03's `findings`. Report in the handoff note, for each register row, whether a variant changed a sign; Stage D writes that into the register's "changes the result?" column.

**Acceptance:** a reader can rerun every table with one command; every number is labelled paper-proposed, illustrative or measured; `verify.py` passes all fixtures; the README states the question, inputs, method, results, limits and reproduce line in EX-01's form; and the handoff note reports, for each register row, whether a variant changed a sign.

### 5.5 Stage C — Evidence tabletop (M2.2): `EX-04` "Evidence before the claim: self-funded job beside release testing"

**Location:** `experiments/m2/evidence-self-funded/`: `README.md`, `tolerances.md`, `packets/` (one Markdown packet per pair; one in the pilot), `matrix.csv`, and `verify.py`, which checks that every row holds allowed values and every evidence row cites a source.

**Matrix columns** (`matrix.csv`, one row per case × standard × evidence level × claim): `pair`, `case` (SC ID), `standard` (`narrow`, `broad`), `level` (`public`, `public+disclosed`), `claim` (CL ID), `value` (`established`, `contradicted`, `unknown`), `evidence` (record kinds relied on), `source` (`SRC-LP20 Lnn`, an `SRC-GOLP` or `SRC-PROTOCOL` path, or `not specified by the paper`), `arrival_round` (`n` to `n+7`, or `after n+7`), `note`. Verdicts go in a second file, `verdicts.csv`: `pair`, `standard`, `level`, `verdict` (`separates`, `does not separate`, `separates only with disclosure`), `who_discloses`, `burden`, `note`.

**Pair:** SC-07 beside SC-23 only. SC-07 beside SC-06 and the other pairs belong to Slice 2, which reuses this packet format.

**Procedure:**

1. **State the alleged violation first,** once under each self-dealing standard in the register (narrow, broad). No common-ownership standard.
2. **Commit the acceptable error and cost before examining outcomes:** tolerance for false cuts, tolerance for missed violations, reviewer effort per case, and the privacy or disclosure burden placed on the operator. Write them in `tolerances.md` and commit it on its own before `matrix.csv` or `verdicts.csv` exist. The reviewer checks the commit order.
3. **Reveal evidence in arrival order** up to round n+7, at two levels: (a) public records only; (b) public records plus one additional source whose disclosure is explicit (for example, the release test plan and the change that followed it). For each record kind, cite where it would come from: the paper, today's system (SRC-GOLP or SRC-PROTOCOL path), or "not specified by the paper". Do not invent a feed.
4. **Mark each claim** (CL-01 payment, CL-02 execution, CL-03 correctness, CL-05 independent demand, CL-06 economic value, CL-07 dishonesty finding) as `established`, `contradicted` or `unknown`, for each case, standard and evidence level.
5. **Give a separation verdict** for each pair, standard and level: `separates`, `does not separate`, or `separates only with disclosure`. Record who must disclose, at what burden, and whether the reward objective needs the distinction at all (GT-03 decides the last point).

**Limits to state:** the packets are synthetic. They test whether a judgment is logically supportable from the stated records. They do not measure detection accuracy, reviewer time or how common the behaviour is. Being unable to infer motive from an invented file does not show the distinction is impossible for every job.

**Records to create:** `EX-04`, its FX rows (one per pair, standard and level; FX `status: illustrative`; `checked_by: hand`, since verdicts are judgments and `verify.py` checks only completeness), and FR records for results that could change a recommendation, using Stage C's ID block (§5.7). Stage C edits GT-01 only to add its new FR IDs to `findings`. GT-01 stays `proposed`; it gains findings for this pair only.

The packet format, the matrix columns and `verify.py` are written to be reused by Slices 2 and 4. Keep pair-specific content out of `verify.py`.

### 5.6 Stage D — Consolidate the slice (M2.3)

1. Write each register row's "changes the result?" entry from Stage B's handoff note.
2. For each finding and design question listed in §5.2, plus the new FRs, confirm or change `resolved_by`, `spec_settles` and `still_to_test` against the Stage B and C results. Leave `reviewed_by` blank; only a named reviewer fills it.
3. Update finding statuses where the results warrant it (for example FR-01 from `hypothesis` to `supported`, `weakened` or `rejected`, under conditions stated in the statement). Updated M1 records keep `stage: M1` and `introduced_by`; set `last_changed_by` to the M2 step.
4. **Compare plausible completions:** the MFS and appendix readings (VD-06), the three emissions concepts and the control (VD-14), treatment of the unassigned remainder (VD-12), and the narrow and broad self-dealing standards (VD-09). Where a deferred variant (§5.9) could change the comparison, say so, and recommend whether Slice 1b should run. A plausible completion is a choice among options the paper states, or a specification it plainly implies. For each, record whether it resolves the concern or leaves it open, and its cost to honest participants. Do not propose new mechanisms.
5. Set GT-03's status to `significant`, `not-significant` or `unresolved`, with conditions in `would_change`.
6. **Assess each of the paper's defenses against its operating condition.** A defense counts as effective only where its condition is satisfied. Report a defense that works as counterevidence, with its actual reach, rather than dismissing it because it is incomplete elsewhere.

   | Defense | What must be established for it to work in this case |
   | --- | --- |
   | Network fee and burn | The unrecovered network half and costs outweigh the extra collectible reward; a positive burn alone is not enough |
   | Stake ceiling | The relevant share is constrained; its effect on share is distinguished from the pool's size; whether added stake reopens the route, at what cost and delay |
   | Emissions cap | Pool growth is bounded; separately, whether a larger share of the bounded pool remains attractive |
   | Claim delay | The extra time yields actionable evidence or changes the payoff; elapsed time is not evidence; the median current at claim applies |
   | Stake lock | The beneficiary bears an opportunity or liquidity cost large enough to matter; locked principal is not assumed lost |
   | Honesty scoring | A defined violation can be established at acceptable error, effort and timing, and enough validators have reason to act on it, including validators with room below their own ceilings (FR-42). The paper names this defense for share capture (L172); Stage C supplies the evidence half, and Slice 3 the incentive half |

7. Write CN records (`task: M2.3`): the concern's assessment, its conditions, and its disposition (M3, build list, evidence work or a policy choice), stated in `statement`. Set `carried_to: M2`, because lint accepts only existing stage or task pages and the workbench has no M3 page (§6). List the paper's strengths that the tests leave standing.
8. Add the slice's M3 handoff items to the M2.3 page.

### 5.7 Record identifiers

The next free identifiers at the time of writing are `EX-03`, `EX-04`, `FR-46`, `CN-22` and `I-01`. Check them with `vtw.py counts` and `find` before use (runbook §4); IDs are never reused. Because Stages B and C run in parallel, they take reserved blocks:

| Stage | EX | FR | CN |
| --- | --- | --- | --- |
| A | — | — | CN-22 onward |
| B | EX-03 | FR-46 to FR-49 | — |
| C | EX-04 | FR-50 to FR-53 | — |
| D | — | FR-54 onward | the next free CN |

Unused IDs in a block stay unused. If a block runs out, stop and record it in the run log.

### 5.8 Stop rule for Slice 1

Stop each half when it answers its question for the stated regions: the economic half when every concept and reading has a sign and a break-even, and the evidence half when the pair has a verdict for each standard and level. Do not add variants beyond the pilot scope, even where they look interesting; record them in the run log as proposals for Slice 1b. Do not extend into validator incentives (Slice 3) or other pairs (Slice 2). If a stage grows well beyond what this section describes, stop and record why in the run log: that is a process finding.

### 5.9 Deferred from the pilot

| Item | Goes to | Condition |
| --- | --- | --- |
| Outside delegators (`ω < 1`, `ρ < 1`, `φ < 1`) and the third control-map setup in the model | Slice 1b | Run if Stage D finds it could change a sign |
| Second execution-cost level (`κ = 0.7`) | Slice 1b | As above |
| C1 years 4 and 8 (ratio 8 and 2) | Slice 1b | As above |
| Concept-1 baseline ratio 28.8 instead of 32 (FR-41) | Slice 1b | As above |
| SC-07 beside SC-06 (related-party production) in the evidence tabletop | Slice 2 | Always |

### 5.10 What the pilot tests in the process

Each stage's retrospective (runbook §9) reports on the runbook parts it used. Between them, the stages should exercise:

| Process part | Exercised by |
| --- | --- |
| Cold pickup from the run log and handoff note alone | B, C and D, each by a different agent if possible |
| Rule register as the shared input to parallel stages | A, then B and C |
| Parallel stages on one branch, with the workbench lock | B and C |
| Gate review of each kind, with fixes and confirmation | Gates A–D |
| Clean-clone rebuild and verification | B (and C's `verify.py`) |
| Tolerances committed before outcomes, checked by commit order | C, Gate C |
| Record creation, IDs, lint, browser check and word budget | All stages |
| Step-page status fields across M2.1, M2.2 and M2.3 | A, B, C, D |
| Owner review, then retrospective and runbook update | End of slice |

## 6. Historical owner decisions for Slice 1

These decisions record the pilot. The October migration and Slice 2 preparation supersede the old proposed run order; they do not confer review or publication status.

| Decision | Status |
| --- | --- |
| Slice 1 scope | Run as a pilot (§5, deferred items in §5.9), including the appendix reading and the evidence stage with one pair. Decided by the owner, 2026-10-05 |
| Illustrative network scale: the paper's year-0 figures, $1.1M fees and $35M mint per year | Confirmed by the owner, 2026-10-05 |
| Run logs, briefs and review reports | Kept outside the public repository, in a separate local repository with its own history (runbook §7.4); the owner may publish them once the process is settled. Decided by the owner, 2026-10-05 and 2026-10-06 |
| Roles | One integrator per slice, the only agent that imports into the workbench and commits; one writer agent per stage; a fresh reviewer of a different model at each gate (runbook §1). For the pilot the owner chose the writer and reviewer models. The owner reviews the slice before any step is marked reviewed. Decided by the owner, 2026-10-06 |
| Branching | Work stays off `main`. `m2` is the integration branch; each slice runs on `m2-slice-NN-<slug>` and merges into `m2` after owner review. Decided by the owner, 2026-10-05 |
| Publishing | The integrator commits to the slice branch locally; pushes, PRs and issue comments only with owner approval |
| `carried_to` for M2.3 conclusions | Open. Default: `carried_to: M2`, with the disposition in the statement. Alternative: add an M3 stage page to the workbench so that conclusions can name M3 |
| Order of runs | Slices 1, 2 and 2b completed; then P1, E2, Slice 3, close pass. Decided by the owner, 2026-10-14 |

## Revision history

| Version | Date | Change |
| --- | --- | --- |
| 0.1 | 2026-10-05 | First draft |
| 0.2 | 2026-10-05 | Owner decisions recorded: year-0 scale; run logs local |
| 0.3 | 2026-10-05 | Slice 1 rescoped as a pilot to test the runbook: one evidence pair, a reduced sweep, deferred items (§5.9), process coverage (§5.10); P1 proposed as the second run |
| 0.4 | 2026-10-05 | Fixes from an independent review: ID blocks for parallel stages, register column written by Stage D, `R_y` handling, concrete fixtures, marginal and average returns, `q*` defined, emissions labels, validator share assumption, Stage C files and columns, `carried_to` default, pilot outputs as CSV/Markdown |
| 0.5 | 2026-10-05 | Branching decision recorded (§6) |
| 0.6 | 2026-10-06 | Roles and run-log decisions recorded; FR-42 and the paper's key passages added to Stage A; defense-by-defense assessment added to Stage D |
| 0.7 | 2026-10-09 | Owner requested a single reusable measured network snapshot for M2; added the shared baseline and model citation requirements, preserving the original illustrative pilot |
| 0.8 | 2026-10-09 | October source boundary and pilot reconciliation; connected scenario accounting; next numbered Slice 2 specified; E2/P1 and all remaining studies preserved; pilot retrospective incorporated without inventing human acceptance |
| 0.9 | 2026-10-12 | Registered defined Slice 2b and its three implementation workloads; multiple network structures, strategic optima and honest-party impacts; GPT-6.1-Sol writers and Opus 5.5 reviewers; original source-scoped studies and human review boundaries preserved |
| 0.10 | 2026-10-12 | Slice 2b amended before Phase 1 (SLICE-02B.md 1.2): measured and near-parity market scales in the core, headroom identity, budget convention, equal-total pacing, controlled invoice price, deferred stake acquisition |
| 0.11 | 2026-10-14 | Remaining program consolidated into topical slices: P1 first, E2 absorbs study 4 and adds operator response and a record inventory, Slice 3 adds declining compensation and seat cost from P1, studies 5–8 move to a close pass with stated dispositions, 1b deferred; per-question disposition table in §2; stop rule for remaining briefs; VD-19 decision required before E2. Owner direction, 2026-10-14 |
| 0.12 | 2026-10-14 | Slices 1, 2 and 2b and the M2 framework recorded as reviewed by the owner; task issues linked for P1, E2, Slice 3 and the consolidation pass. Owner research review, 2026-10-14 |
