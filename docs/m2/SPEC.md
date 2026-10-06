# M2 specification: test litepaper incentives and evidence limits

Version **0.6 · 2026-10-06**. Status: **drafted**. Revision history is at the end. Owner: Shane (@moatus).

This specification says what M2 must produce and specifies its first unit of work, Slice 1, in enough detail for an agent to carry it out. How the work is run, reviewed and handed between agents is in the [runbook](RUNBOOK.md). The milestone's definition is in [MILESTONES.md](../../MILESTONES.md#m2--test-litepaper-incentives-and-evidence-limits); this file does not change it.

## 1. Purpose and boundary

M2 tests the litepaper. It reassembles the mechanisms M1 took apart, tests the critical questions with small reproducible examples and focused evidence inquiries, and records what would resolve each concern. It hands M3 the concerns that plausible completions of the paper leave unresolved, together with the areas the paper leaves unaddressed.

Boundaries that hold for every slice:

- **Litepaper only.** M2 examines the paper's own mechanisms and the readings the paper allows. It does not describe or compare against a successor mechanism. A fixed emissions pool, where used, is an analytical control and not a proposed policy.
- **Small, not simulated.** A table, a calculation or a bounded case comparison that answers its question is enough. No network simulation, agent-based framework or Monte Carlo study is in scope for M2. If a question appears to need one, stop and record why in the run log; the owner decides.
- **Conditional results.** Every result names the rules, interpretations and assumptions it holds under. A profitable deviation with everyone else held fixed is not an equilibrium and not evidence of prevalence. Modelled vulnerability and observed prevalence are reported separately.
- **Distinct claims.** Payment, execution, correctness, availability, independent demand and economic value are separate claims (CL-01 to CL-06). The paper's multiplier concerns dishonesty, not service quality.
- **Counterevidence stays.** The paper's defenses get a fair test. Where a defense holds, that is a result and goes into the record.

## 2. What a complete M2 leaves behind

M2 is complete when a reviewer can choose any of the nine critical questions (GT-01 to GT-04, GT-06 to GT-10) and find three things: an assessment under stated conditions, a result they can rerun or a table they can trace, and a disposition (build work, more evidence, incentive issue, policy choice, or M3).

| Step | Artifact | Where it lives |
| --- | --- | --- |
| M2.1 How the mechanisms behave together | Rule-interpretation register; participant and control map; one timeline; for each intended relationship, an assessment (supported, conditional, contradicted, unresolved); a ranked test list that confirms or replaces each proposed test | Workbench step page M2.1 and CN records |
| M2.2 Testing the critical questions | One result per consequential critical question: economic models (generated workbook or script with a verifier), evidence tabletop packets, and short current-system data notes | `experiments/m2/<slug>/`, described by EX and FX records, summarized on step page M2.2 with FR and CN records |
| M2.3 What would resolve each concern? | Every design question and finding classified by what would resolve it; each concern assessed (finding status `supported`, `weakened` or `rejected`; critical-question status `significant`, `not-significant` or `unresolved`); plausible completions compared; M3 handoff list with the paper's retained strengths beside it | Workbench step page M2.3, FR updates and CN records |

These support the three existing M2 deliverables. They are not a parallel report. Reviewed versions are recorded by commit in the [deliverable register](../../deliverables/README.md), as for M1.

**"Unresolved" counts as a result** only when the inquiry has identified the missing rule or evidence that leaves it unresolved. A test that was proposed and never run does not count.

## 3. Methods

| Method | Use it for | Form | Must include |
| --- | --- | --- | --- |
| **Economic example** | Payoffs, break-even points, which assumption drives a sign | `build.py` generates CSV or Markdown tables (an XLSX workbook only where readers need to edit inputs); `verify.py` checks independent arithmetic against hand-computed fixtures; pinned dependencies; one reproduce line | Inputs labelled paper-proposed, illustrative or measured; LPT and USDC kept separate until a stated price converts them; each receipt counted once; the cooperative case first |
| **Evidence tabletop** | Whether obtainable evidence separates a case from its legitimate lookalike before the claim | A structured case packet (Markdown plus a CSV matrix) with a completeness check script, `verify.py` | The alleged violation stated first; acceptable error and cost committed before outcomes are examined; evidence revealed in arrival order up to round n+7; each claim marked established, contradicted or unknown |
| **Current-system data note** | How today's network actually behaves, where a model's assumption depends on it | A short note plus the query script and a dated, versioned data extract | Source, block range or date range, query, and a label that this is today's system, not a forecast for the litepaper |
| **Rule reading** | Questions about governance or rule sequencing that need no numbers | A timeline or comparison table on the step page | The stated rule variants and where the result changes between them |

Synthetic case packets can test the logic of a judgment. They cannot establish whether evidence exists in practice, how long review takes, or how often reviewers err. Claims of that kind need inspected sources or a real, bounded exercise.

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

### Slice catalogue (proposed order; Stage A of each slice may revise it)

| Slice | Critical questions | Cases | Main methods | Notes |
| --- | --- | --- | --- | --- |
| **1 — Self-funded real usage (pilot)** | GT-03; GT-01 for one pair only | SC-07 beside SC-23; SC-01 as the cooperative reference | Economic example; evidence tabletop | Specified in §5 |
| 1b — Self-funded follow-up | GT-03 | As Slice 1 | Economic example | Run only if Slice 1 shows that a deferred variant (§5.9) could change a sign |
| 2 — Evidence before the claim | GT-01 (remaining pairs) | SC-07 beside SC-06; SC-16 beside SC-17; SC-11 beside SC-10 | Evidence tabletop | Reuses the Slice 1 packet format |
| 3 — Will validators score defensibly? | GT-02, GT-09 | SC-09, SC-19, SC-20, SC-21, SC-24, SC-35, SC-36, SC-37 | Small repeated payoff table; seat-control cost table | Uses Slice 1–2 evidence assumptions; GT-09 uses data note P1 |
| 4 — Defending a reward | GT-06 | SC-25 beside SC-26 | Evidence tabletop; effort and access table | |
| 5 — Delegation in time | GT-04 | SC-27 beside SC-28; SC-04, SC-08 | Round-by-round example | Uses data note P1 (HQ-01) |
| 6 — Access to paid work | GT-07 | SC-29, SC-30, SC-31; SC-03, SC-12 | Selection comparison under stated rules | Needs a stated selection rule (CN-21) |
| 7 — Rule changes while rewards are pending | GT-08 | SC-32, SC-33, SC-34 | Rule reading (timeline) | |
| 8 — LPT price | GT-10 | SC-38 beside SC-39 | Sensitivity; manipulation cost only where a concrete price source and liquidity assumption exist | |
| P1 — Current-system data notes | Supports GT-04, GT-09, HQ-03 | — | Data notes | Proposed as the second run, starting with stake movement speed (HQ-01), to test the data-note method and a light run. Then concentration of top stake and the shape of real fee spikes. Data access and any API keys are owner decisions |

## 5. Slice 1 — Self-funded real usage (pilot)

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

## 6. Owner decisions for Slice 1

| Decision | Status |
| --- | --- |
| Slice 1 scope | Run as a pilot (§5, deferred items in §5.9), including the appendix reading and the evidence stage with one pair. Decided by the owner, 2026-10-05 |
| Illustrative network scale: the paper's year-0 figures, $1.1M fees and $35M mint per year | Confirmed by the owner, 2026-10-05 |
| Run logs, briefs and review reports | Kept outside the public repository, in a separate local repository with its own history (runbook §7.4); the owner may publish them once the process is settled. Decided by the owner, 2026-10-05 and 2026-10-06 |
| Roles | One integrator per slice, the only agent that imports into the workbench and commits; one writer agent per stage; a fresh reviewer of a different model at each gate (runbook §1). For the pilot the owner chose the writer and reviewer models. The owner reviews the slice before any step is marked reviewed. Decided by the owner, 2026-10-06 |
| Branching | Work stays off `main`. `m2` is the integration branch; each slice runs on `m2-slice-NN-<slug>` and merges into `m2` after owner review. Decided by the owner, 2026-10-05 |
| Publishing | The integrator commits to the slice branch locally; pushes, PRs and issue comments only with owner approval |
| `carried_to` for M2.3 conclusions | Open. Default: `carried_to: M2`, with the disposition in the statement. Alternative: add an M3 stage page to the workbench so that conclusions can name M3 |
| Order of runs | Slice 1 (pilot), then P1 (stake movement speed) as a short second run, subject to a data-access decision; then Slice 2 onward |

## Revision history

| Version | Date | Change |
| --- | --- | --- |
| 0.1 | 2026-10-05 | First draft |
| 0.2 | 2026-10-05 | Owner decisions recorded: year-0 scale; run logs local |
| 0.3 | 2026-10-05 | Slice 1 rescoped as a pilot to test the runbook: one evidence pair, a reduced sweep, deferred items (§5.9), process coverage (§5.10); P1 proposed as the second run |
| 0.4 | 2026-10-05 | Fixes from an independent review: ID blocks for parallel stages, register column written by Stage D, `R_y` handling, concrete fixtures, marginal and average returns, `q*` defined, emissions labels, validator share assumption, Stage C files and columns, `carried_to` default, pilot outputs as CSV/Markdown |
| 0.5 | 2026-10-05 | Branching decision recorded (§6) |
| 0.6 | 2026-10-06 | Roles and run-log decisions recorded; FR-42 and the paper's key passages added to Stage A; defense-by-defense assessment added to Stage D |
