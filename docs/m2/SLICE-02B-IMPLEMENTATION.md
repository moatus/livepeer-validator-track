# Slice 2b implementation: three agent workloads

Version **1.2 · 2026-10-12**. Definition status before implementation: **ready for phased implementation; not started**. Aligned with SLICE-02B.md 1.2.

**Execution status:** Frozen inputs and reproducible [EX-08 accounting](../../experiments/m2/strategic-self-funding/README.md) are implemented and technically checked. Consolidation and its [listening guide](../reviewer-resources/m2-slice-02b-story-listening-guide.md) were reviewed by the owner, 2026-10-14 ([#28](https://github.com/moatus/livepeer-validator-track/issues/28)); the original workload and acceptance definitions below are preserved.

The research design is already defined in [SLICE-02B.md](SLICE-02B.md). This specification implements it through M2.1, M2.2 and M2.3. There is no slice-design phase. Read [SPEC.md](SPEC.md), [RUNBOOK.md](RUNBOOK.md), [MILESTONES.md](../../MILESTONES.md) and [WORKFLOW.md](../WORKFLOW.md); the owner's instructions take precedence.

## Precedent and authority

Reuse EX-06's all-pool accounting, EX-05's October calibration and snapshot interface, EX-03's source-scoped threshold methods, and EX-07's economic/evidence distinction. The only new experiment surface is a fixture/strategy adapter and bounded optimizer/timeline reporting required by the defined study. Do not duplicate the reward engine or introduce a simulator, new settlement subsystem, purpose oracle or scoring policy.

This plan authorizes preparation and defines future execution; its existence does not claim that an implementation phase ran. Local preparation branches from the existing Slice 2 work without inferring acceptance or merging it into `m2`. Research status remains drafted until owner review.

## Agents, sequencing and execution record

| Phase | One fresh implementation writer | One fresh independent reviewer | Dependency |
| --- | --- | --- | --- |
| 1 — M2.1 reconstruction and frozen inputs | Codex / `gpt-6.1-sol` | Claude / `claude-opus-5-5` | Defined Slice 2b and unchanged earlier experiments |
| 2 — M2.2 connected strategic tests | Codex / `gpt-6.1-sol` | Claude / `claude-opus-5-5` | Phase 1 accepted, imported and locally committed |
| 3 — M2.3 consolidation and narrative | Codex / `gpt-6.1-sol` | Claude / `claude-opus-5-5` | Phase 2 accepted, imported and locally committed |

The requested models override generic role defaults. Provider availability was checked during preparation; execution rechecks once at kickoff. Do not silently substitute models. Do not set reasoning effort unless separately requested. Writers and reviewers complete their assignments directly and do not spawn workers.

One integrator launches all pairs, owns the main workbench, imports approved change sets and is the only committer. Writers produce experiment files plus external change-set scripts/JSON and handoffs; reviewers are report-only. Use the main clone, sequential phases and fresh agents. An implementation writer may handle bounded corrections to its own phase before the same review gate closes.

Before launching this six-assignment job, establish the execution milestone record with three implementation acceptance milestones and a final technical handoff gate; record six primary assignments plus conditional fixes and local commit order. Keep execution interface identifiers with the external run log. Evidence records actual accepted commits and checks. If the required execution interface or a requested model is unavailable, report the specific execution dependency; no substitute process is inferred. Agent gates are technical acceptance, not human research acceptance.

Review a frozen local candidate commit prepared by the integrator after writer self-checks. The candidate contains only writer-owned tracked experiment or reader files; workbench change sets are reviewed on a scratch copy and imported/committed only after the gate passes. If a phase changes only workbench records, the candidate can be the unchanged current commit plus an explicitly hashed external change set and scratch copy. This ordering replaces only RUNBOOK §4.5's commit timing. After each gate-close import and commit, §4.5's lint, unit tests, clean-clone rebuild and commit-message rules still apply. If changes are needed, the writer supplies fixes and the integrator adds new candidate commits or revised external change sets; no amendment, reset or history rewriting. Opus rechecks affected acceptance. A blocked candidate remains local, unaccepted history. Proceed only with no unresolved blocker. Phase 2 presents two sequential candidates to the same reviewer: first the accounting adapter, optimizer, verifier and all core, control and fee-leaning confirmation rows; second the supplements, timelines, evidence table and records. The second candidate starts only after the first passes. Maximum three review/fix cycles per candidate; diagnose and report remaining blockers at that bound. A clean review needs no extra fixer assignment. Keep review reports and run logs outside the public repository.

## Preparation already completed by this specification

- Slice identity, research question, rule reading, network structures, actor positions, market scales, spending/budget bounds, comparisons and stopping conditions are fixed in SLICE-02B.md.
- The study catalogue and milestone/reader pointers register it as defined, implementation pending; original studies and status are preserved.
- Preparation is on `m2-slice-02b-strategic-self-funding`, descended from Slice 2 commit `e0c66a69bfea64a5484ffa55bf96535874553bb6`. This ancestry is a local continuation, not owner acceptance of Slice 2.
- No new experiment outcomes or workbench findings are authored in preparation. Each phase brief receives the actual baseline commit/hash, ID reservations and external run location at dispatch.

## Phase 1 — M2.1: reconstruct and freeze the defined comparison

**Concrete result:** a validated machine-readable input contract and workbench reconstruction from which one M2.2 writer can calculate every specified comparison without inventing economic assumptions.

**Hard core:** construct whole-network states that conserve fees and stake, preserve valid actor ranks, and separate network structure, own-business headroom and total fee scale. A list of scenario titles without reproducible vectors fails this phase.

**Writer workload:**

1. Audit EX-03 to EX-07 and document which conditions were varied, fixed or deferred. Carry valid accounting and historical methods forward; do not carry September emissions concepts into October.
2. Materialize all SLICE-02B definitions in `experiments/m2/strategic-self-funding/inputs.json`, `networks.json` and `scenarios.json`, with units, source pointers/hashes, transformations, parents, actor ranks, paired useful references and permitted bounds. Commit construction rules and deterministic input-vector hashes in `networks.json`; generated vectors remain ignored. Freeze their serialization and Decimal precision. Implement only fixture/schema validation needed to freeze these inputs; no reward, profit or loss outcomes.
3. Validate the 54 core profiles, the three fee-leaning confirmations, nine aligned controls, measured references, supplementary selection keys (one-factor overrides, appendix, capability, demand, price/routing, budget convention, controlled invoice price and the three timeline schedules), normalized vectors and stable source identities. The new actor's traffic must visibly rebalance the other pools. Explicitly record confounded D/C changes, full-retention upper-bound assumptions, native victim-retention proxies, the exact recomputed measured ratio and the budget convention's meaning. Freeze one-round versus fixed-stock budget periods, inclusive capacity boundaries, the invoice-price offer construction and all supplementary capacity/setup/price rules.
4. Reserve new EX/FR/FX/CN/register IDs after inspecting occupied IDs. Supply compact control and timeline maps, claimant/retention definitions, budget versus advance-liquidity boundary, reference comparisons and exact source-scoped rule readings.
5. Prepare changes to M2.1 and GT-03/GT-07 plus relevant VD-06/19 handoffs. Include bounded GT-04/GT-10 back-links where delegator-effect and valuation comparisons touch those questions; do not claim their full studies completed. Preserve GT-01's original pending study and EX-07 disclosure/scope limits. Update only assigned reconstruction fields; outcomes remain blank/pending.
6. Produce a change-set script/JSON, scratch render/checks, implementation report, retrospective and a self-contained Phase 2 handoff. Put these process files in the external run location.

**Scope:** the new experiment's input/fixture files and README; assigned M2.1/GT records through change sets. No edits to frozen sources, earlier experiment inputs/results, main workbench, historical guides or deliverable acceptance.

**Opus gate:** independently validate sums, formulas and actor selections; inspect at least one profile from each structure and both market definitions; check schema coverage of every declared supplement and its finite bounds. Check that balanced controls contain no contradictory headroom override and that no hidden purpose becomes observable evidence. Scratch lint must be 0 errors/0 warnings, workbench unit tests pass, rendered changed pages pass browser/word-budget checks with any declared budget reservation documented. Verify source hashes and adjacent-field consistency.

**Integrator close:** adjudicate findings, import accepted workbench reconstruction and commit it on top of the accepted candidate/fix commits, record all accepted versions and checks in the execution milestone record, and issue the Phase 2 mandate with the frozen inputs and reserved IDs. Phase 1 implementation must not redesign the study; substantive changes return as explicit design amendments.

## Phase 2 — M2.2: implement and test the connected strategy ledger

**Concrete result:** one deterministic reproduce command generates the defined strategies, affordable optima, honest-party effects, response comparisons and cohort accounting for every profile, with independent verification and source-scoped findings.

**Hard core:** correctly optimize one-round retained net value within stake-cap and cash-loss constraints, checking execution capacity, while calculating all honest participants and pending claims. Capacity binds only the harm-only reach in the no-cash-bound budget-convention rows, never a profitable optimum. A profitable sampled point or attacker-only table fails this phase.

**Writer workload:**

1. Build the checked EX-06 accounting adapter, continuous constrained optimizer, piecewise break-even/loss landmarks and finite progression generator. Expose arbitrary selected actor roles without implementing a second reward engine. The closed forms locate stationary points, cap kinks and loss landmarks; every reported payoff and all-pool effect is evaluated through EX-06 `account()`. Independently cross-check the closed-form result at each applicable candidate within the documented 1e-18 tolerance. EX-06's `comparison()` has matching cap-headroom algebra; check agreement rather than silently introducing a different cap rule. If a contained accounting interface change is necessary, reproduce all original cases and document the exact changed contract before using it.
2. Generate all frozen core/control/supplementary rows. Keep measured/native-retention references separate from standardized full-retention core states. Include useful-internal paired accounting, all 100 pool effects, outside receipts, total issuance/burn and explicit infeasibility/undefined labels. For every profile report `dcap`, `dB`, their minimum, the unminted-versus-peer-loss share of the actor's gain, and the "budget convention" label wherever the budget binds. Implement the budget-convention and controlled invoice-price rows as declared, and the capped-position stake arithmetic `dS` as a reported identity only.
3. Implement the four-round constant, escalating-ramp and equal-total-ramp cash budgets and per-cohort schedules/claims. At each earning round, apply its allowance and feasible cash/capacity boundary; unsold claims remain tokens. Distinguish cash shortfall, pending reward, permanently unavailable allowance and final collected value. Timelines use one fixed initial budget stock and a matched four-round no-purchase baseline. Compare pacing only between the equal-total schedules and with one-round use of that stock; report the escalating ramp as spending escalation; flag actors whose cap lies below the stock as having no pacing question. No schedule is a multi-round optimum or an emissions-decline test.
4. Reuse EX-07 only within its existing claim/evidence scope. Write a compact table separating scenario purpose, obtainable observations, rule-definition dependency and procedural response, with a column naming the EX-07 disclosure premise relied on or "not examined". Undisclosed control and unpacketed generic/full-volume conduct inherit no verdict. No new packets, empirical judgment rates or adverse median behavior are supplied.
5. Write the experiment README and source-scoped EX/FX/FR records, update M2.2 and relevant critical-question backlinks, including bounded GT-04/GT-10 delegator/valuation inputs, and supply Phase 3 with results both strengthening and weakening the concern. Register the actual experiment in `experiments/README.md` and add generated-output ignores.
6. Deliver source code, independent verifier, change-set script/JSON, checks, report, retrospective and self-contained handoff. Keep generated outputs ignored and process reports external.

**Scope:** new experiment folder, generated ignores and experiment index; assigned M2.2/EX/FX/FR/GT outcome fields through change sets. Earlier experiments remain unchanged unless an identified implementation defect or interface necessity is explicitly adjudicated. Preserve every original source-scoped result unless a demonstrated error requires a documented correction.

**Opus gate:** apply RUNBOOK Gate B and common checks, then:

- Hand-recalculate at least two nontrivial fixtures: a below-cap optimum with victim dilution, and a capped/budget-constrained case. Verify optimality through derivatives/kinks/endpoints, not the builder's own sampled outputs.
- Reproduce EX-06's original 12 cases and sensitivity outputs against the preserved engine/configuration; rerun EX-03, EX-04, EX-05 and EX-07 verifiers. A prior verifier pass establishes its actual scope, not broader empirical validity.
- Check fee/stake normalization, receipt conservation, cancellation of internal transfers once, external-owner exclusion, correct schedule, score boundaries, zero fees/rewards, all-pool loss aggregation and identity of matched capability/use accounting.
- Confirm critical reward/fee ratios, target-loss spending and inclusive reachability, the fee-limited 20% capacity-boundary label, honest stake-cap protection, zero profitable action in the fee-leaning/aligned controls, and separation of harm-only spending from profit-seeking conduct.
- Hand-check the headroom identity `dcap=(s-a)/(1-a)` and `dB` on one profile per structure; confirm every budget-bound stopping point carries the "budget convention" label; confirm the invoice-price rows reduce leakage toward `1-.5z` with `c` per job unchanged and that the near-parity interior optimum moves as the closed form predicts; confirm the equal-total ramp and constant schedule spend identical totals; confirm the capped-position `dS` arithmetic is reported as an identity with no cost or delay claim.
- Check every timeline through first and final claim horizons, budget exhaustion and no use of unsold rewards as cash. Review the meaning of return at each horizon.
- Perform a clean-checkout rebuild from candidate commit with repository-contained experiment dependencies. Scratch-workbench lint/unit/render checks pass. Evidence reuse supplies no new detection finding.

**Integrator close:** resolve findings, import accepted workbench experiment records/outcomes and commit them on top of accepted candidate/fix commits, record all accepted versions and checks, and provide Phase 3 the complete result coverage and limitation inventory. Do not label model scenarios observed misconduct.

## Phase 3 — M2.3: consolidate meaning and revise conclusion scope

**Concrete result:** an integrated account showing which network/player conditions allow profitable self-funding, its affordable reach and cost to honest participants, which defenses work, and what remains to resolve.

**Hard core:** explain differences across network conditions with counterexamples and stopping boundaries. Repeating “conditional incentive exists” without explaining strategic scale, beneficiaries and victims fails this phase.

**Writer workload:**

1. Compare actor ranks, own-business headroom, whole-network mismatch and fee scale using the accepted outputs. Write three principal stories, largest, middle and lower stake, each answering in order: what opportunity exists, what the actor spends, what it retains, who loses and how much, why it stops, and which changed condition reverses the result. Present the four market scales as a path from today's measured condition to a fee-dominant network and state where on it each defense begins to work. Explain profitable stopping points as one-round constrained optima, separately from maximum entitlement, budget-convention reach and harm-only spending; state the headroom identity as the bound on a single fixed-stake actor's harm. Explain fixed-stock timeline pacing from the equal-total pair only, without claiming a multi-round optimum. Explain the critical-ratio boundaries and the invoice-price leakage floor.
2. State which honest operators lose, how material individual/collective losses become, whether fees or actual issuance change, how much of the actor's gain is previously unminted allowance rather than peer loss, and what the bounded responses/timelines establish. Do not infer exit, equilibrium or practical response likelihood.
3. Reassess earlier conclusions: retain source-scoped findings, qualify overbroad formulations, and document any genuine contradiction/correction with exact evidence. Update reconstruction outcome columns and affected adjacent fields/backlinks; do not relabel historical research as October.
4. Assess fixed ceiling, MFS, network charge, outside retention, execution costs, claims and scoring against their demonstrated operating conditions. Compare main-text/appendix implications without choosing policy. Include no-gain/defensive cases and useful internal work.
5. Classify unresolved matters as implementation detail, evidence, incentives or policy, with specific E2/P1/studies 3–8 dependencies, including stake acquisition to raise a cap as a Slice 5/P1 dependency. Hand M3 only unresolved concerns/unaddressed areas with retained strengths; introduce no successor mechanism.
6. Update M2.3, relevant FR/CN/GT records and consistent reader/status/index fields through change sets. Write `docs/reviewer-resources/m2-slice-02b-story-listening-guide.md`, based only on the accepted research, conversational and light on identifiers/numbers, with source references outside the spoken narrative.
7. Supply report, retrospective, source-to-conclusion trace table, change sets and the final owner-review package. M2 and its deliverables remain drafted/in progress; this phase does not fill `reviewed_by` or declare owner acceptance.

**Scope:** assigned consolidation/adjacent workbench fields; the new listening guide and status pointers. No new economics, scenarios or behavioral premises; calculation defects go back to the Phase 2 writer and affected review gate.

**Opus gate:** apply RUNBOOK Gate D and common checks. Trace every material statement to a profile/row and its limits. Confirm cross-network differences have the right explanation, identities are anonymous synthetic roles, original source scopes persist, and evidence/intent/value remain distinct. Confirm the three stories answer the same questions in the same order, the budget convention is never described as a defense, and the measured-scale account carries its retention and valuation assumptions. Read the guide as a standalone spoken narrative. Scratch lint/unit/browser/word-budget checks pass; no unresolved substantive finding is carried as acceptance.

**Integrator close:** import accepted workbench consolidation and commit it on top of accepted candidate/fix commits, record evidence and complete the final technical handoff gate. Present the exact local artifact versions and unresolved practical dependencies for owner research review. No push, PR, board edit, merger into `m2`, reviewed-deliverable registration or protocol adoption follows automatically.

## Final acceptance and execution handoff

The final technical gate passes only when all three reviewed phase commits exist, earlier experiments reproduce, the new experiment rebuilds in a clean checkout, all declared comparisons have results or justified undefined boundaries, workbench/reader checks pass, and the narrative explains strategic reach and honest-party impact across conditions. A missing declared case is not satisfied by a promise to test later.

Dispatch briefs must include the exact source/branch/commit, governing documents, allowed edits, reserved IDs, external run paths, acceptance commands and expected outputs; say “complete directly; do not spawn workers.” The integrator supplies those operational details without putting private paths or run reports in public artifacts. Recheck live issues and board read-only at execution kickoff. Preserve unrelated local work and never stage local agent instructions.
