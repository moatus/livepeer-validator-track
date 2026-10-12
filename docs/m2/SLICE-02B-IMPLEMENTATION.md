# Slice 2b implementation: three agent workloads

Version **1.0 · 2026-10-12**. Status: **ready for phased implementation; not started**.

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

Before launching this six-assignment job, create the harness's native milestone map with three implementation acceptance milestones and a final technical handoff gate; record six primary assignments plus conditional fixes and local commit order. Map evidence records actual accepted commits and checks. If the interface or a requested model is unavailable, report the specific execution dependency; no substitute process is inferred. Agent gates are technical acceptance, not human research acceptance.

Review a frozen local candidate commit prepared by the integrator after writer self-checks. If changes are needed, the writer supplies fixes, the integrator freezes the revised candidate and Opus rechecks affected acceptance. Proceed only with no unresolved blocker. Maximum three review/fix cycles per phase; diagnose and report remaining blockers at that bound. A clean review needs no extra fixer assignment. Keep review reports and run logs outside the public repository.

## Preparation already completed by this specification

- Slice identity, research question, rule reading, network structures, actor positions, market scales, spending/budget bounds, comparisons and stopping conditions are fixed in SLICE-02B.md.
- The study catalogue and milestone/reader pointers register it as defined, implementation pending; original studies and status are preserved.
- Preparation is on `m2-slice-02b-strategic-self-funding`, descended from Slice 2 commit `e0c66a69bfea64a5484ffa55bf96535874553bb6`. This ancestry is a local continuation, not owner acceptance of Slice 2.
- No new experiment outcomes or workbench findings are authored in preparation. Each phase brief receives the actual baseline commit/hash, ID reservations and external run location at dispatch.

## Phase 1 — M2.1: reconstruct and freeze the defined comparison

**Concrete result:** a validated machine-readable input contract and workbench reconstruction from which one M2.2 writer can calculate every specified comparison without inventing economic assumptions.

**Hard core:** construct whole-network states that conserve fees and stake, preserve valid actor ranks, and separate network structure, own-business headroom and total fee scale. A list of scenario titles without reproducible vectors fails this phase.

**Writer workload:**

1. Audit EX-03/05/06/07 and document which conditions were varied, fixed or deferred. Carry valid accounting and historical methods forward; do not carry September emissions concepts into October.
2. Materialize all SLICE-02B definitions in `experiments/m2/strategic-self-funding/inputs.json`, `networks.json` and `scenarios.json`, with units, source pointers/hashes, transformations, parents, actor ranks, paired useful references and permitted bounds. Implement only fixture/schema validation needed to freeze these inputs; no reward, profit or loss outcomes.
3. Validate the 36 core profiles, aligned controls, measured references, supplementary selection keys, normalized vectors and stable source identities. The new actor's traffic must visibly rebalance the other pools. Explicitly record confounded D/C changes, full-retention upper-bound assumptions and the source ratio outside stress bounds if applicable.
4. Reserve new EX/FR/FX/CN/register IDs after inspecting occupied IDs. Supply compact control and timeline maps, claimant/retention definitions, budget versus advance-liquidity boundary, reference comparisons and exact source-scoped rule readings.
5. Prepare changes to M2.1 and GT-03/GT-07 plus relevant VD-06/19 handoffs. Preserve GT-01's original pending study and EX-07 limits. Update only assigned reconstruction fields; outcomes remain blank/pending.
6. Produce a change-set script/JSON, scratch render/checks, implementation report, retrospective and a self-contained Phase 2 handoff. Put these process files in the external run location.

**Scope:** the new experiment's input/fixture files and README; assigned M2.1/GT records through change sets. No edits to frozen sources, earlier experiment inputs/results, main workbench, historical guides or deliverable acceptance.

**Opus gate:** independently validate sums, formulas and actor selections; inspect at least one profile from each structure and both market definitions; check schema coverage of every declared supplement and its finite bounds. Check that balanced controls contain no contradictory headroom override and that no hidden purpose becomes observable evidence. Scratch lint must be 0 errors/0 warnings, workbench unit tests pass, rendered changed pages pass browser/word-budget checks with any declared budget reservation documented. Verify source hashes and adjacent-field consistency.

**Integrator close:** adjudicate findings, import only the accepted reconstruction, locally commit phase files, record evidence in the milestone map and issue the Phase 2 mandate with the frozen inputs and reserved IDs. Phase 1 implementation must not redesign the study; substantive changes return as explicit design amendments.

## Phase 2 — M2.2: implement and test the connected strategy ledger

**Concrete result:** one deterministic reproduce command generates the defined strategies, affordable optima, honest-party effects, response comparisons and cohort accounting for every profile, with independent verification and source-scoped findings.

**Hard core:** correctly optimize retained net value within stake, cash-loss and execution-capacity constraints, while calculating all honest participants and pending claims. A profitable sampled point or attacker-only table fails this phase.

**Writer workload:**

1. Build the checked EX-06 accounting adapter, continuous constrained optimizer, piecewise break-even/loss landmarks and finite progression generator. Expose arbitrary selected actor roles without copying a second reward formula. If a contained accounting interface change is necessary, reproduce all original cases and document the exact changed contract before using it.
2. Generate all frozen core/control/supplementary rows. Keep measured/native-retention references separate from standardized full-retention core states. Include useful-internal paired accounting, all 100 pool effects, outside receipts, total issuance/burn and explicit infeasibility/undefined labels.
3. Implement four-round constant/ramp cash budgets and per-cohort schedules/claims. At each earning round, apply its allowance and feasible cash/capacity boundary; unsold claims remain tokens. Distinguish cash shortfall, pending reward, permanently unavailable allowance and final collected value.
4. Reuse EX-07 only within its existing claim/evidence scope. Write a compact table separating scenario purpose, obtainable observations, rule-definition dependency and procedural response. No new packets, empirical judgment rates or adverse median behavior are supplied.
5. Write the experiment README and source-scoped EX/FX/FR records, update M2.2 and relevant critical-question backlinks, and supply Phase 3 with results both strengthening and weakening the concern. Register the actual experiment in `experiments/README.md` and add generated-output ignores.
6. Deliver source code, independent verifier, change-set script/JSON, checks, report, retrospective and self-contained handoff. Keep generated outputs ignored and process reports external.

**Scope:** new experiment folder, generated ignores and experiment index; assigned M2.2/EX/FX/FR/GT outcome fields through change sets. Earlier experiments remain unchanged unless an identified implementation defect or interface necessity is explicitly adjudicated. Preserve every original source-scoped result unless a demonstrated error requires a documented correction.

**Opus gate:** apply RUNBOOK Gate B and common checks, then:

- Hand-recalculate at least two nontrivial fixtures: a below-cap optimum with victim dilution, and a capped/budget-constrained case. Verify optimality through derivatives/kinks/endpoints, not the builder's own sampled outputs.
- Reproduce EX-06's original 12 cases and sensitivity outputs against the preserved engine/configuration; rerun EX-03, EX-05 and EX-07 verifiers. A prior verifier pass establishes its actual scope, not broader empirical validity.
- Check fee/stake normalization, receipt conservation, cancellation of internal transfers once, external-owner exclusion, correct schedule, score boundaries, zero fees/rewards, all-pool loss aggregation and identity of matched capability/use accounting.
- Confirm target-loss spending and reachability, honest stake-cap protection, zero profitable action in the appropriate control, and separation of harm-only spending from profit-seeking conduct.
- Check every timeline through first and final claim horizons, budget exhaustion and no use of unsold rewards as cash. Review the meaning of return at each horizon.
- Perform a clean-checkout rebuild from candidate commit with repository-contained experiment dependencies. Scratch-workbench lint/unit/render checks pass. Evidence reuse supplies no new detection finding.

**Integrator close:** resolve findings, import accepted experiment records and outcomes, locally commit, record accepted checks/commit, and provide Phase 3 the complete result coverage and limitation inventory. Do not label model scenarios observed misconduct.

## Phase 3 — M2.3: consolidate meaning and revise conclusion scope

**Concrete result:** an integrated account showing which network/player conditions allow profitable self-funding, its affordable reach and cost to honest participants, which defenses work, and what remains to resolve.

**Hard core:** explain differences across network conditions with counterexamples and stopping boundaries. Repeating “conditional incentive exists” without explaining strategic scale, beneficiaries and victims fails this phase.

**Writer workload:**

1. Compare actor ranks, own-business headroom, whole-network mismatch and fee scale using the accepted outputs. Explain profitable stopping points separately from maximum entitlement, capital-constrained reach and harm-only spending.
2. State which honest operators lose, how material individual/collective losses become, whether fees or actual issuance change, and what the bounded responses/timelines establish. Do not infer exit, equilibrium or practical response likelihood.
3. Reassess earlier conclusions: retain source-scoped findings, qualify overbroad formulations, and document any genuine contradiction/correction with exact evidence. Update reconstruction outcome columns and affected adjacent fields/backlinks; do not relabel historical research as October.
4. Assess fixed ceiling, MFS, network charge, outside retention, execution costs, claims and scoring against their demonstrated operating conditions. Compare main-text/appendix implications without choosing policy. Include no-gain/defensive cases and useful internal work.
5. Classify unresolved matters as implementation detail, evidence, incentives or policy, with specific E2/P1/studies 3–8 dependencies. Hand M3 only unresolved concerns/unaddressed areas with retained strengths; introduce no successor mechanism.
6. Update M2.3, relevant FR/CN/GT records and consistent reader/status/index fields through change sets. Write `docs/reviewer-resources/m2-slice-02b-story-listening-guide.md`, based only on the accepted research, conversational and light on identifiers/numbers, with source references outside the spoken narrative.
7. Supply report, retrospective, source-to-conclusion trace table, change sets and the final owner-review package. M2 and its deliverables remain drafted/in progress; this phase does not fill `reviewed_by` or declare owner acceptance.

**Scope:** assigned consolidation/adjacent workbench fields; the new listening guide and status pointers. No new economics, scenarios or behavioral premises; calculation defects go back to the Phase 2 writer and affected review gate.

**Opus gate:** apply RUNBOOK Gate D and common checks. Trace every material statement to a profile/row and its limits. Confirm cross-network differences have the right explanation, identities are anonymous synthetic roles, original source scopes persist, and evidence/intent/value remain distinct. Read the guide as a standalone spoken narrative. Scratch lint/unit/browser/word-budget checks pass; no unresolved substantive finding is carried as acceptance.

**Integrator close:** import/commit accepted consolidation, record evidence and complete the final technical handoff gate. Present the exact local artifact versions and unresolved practical dependencies for owner research review. No push, PR, board edit, merger into `m2`, reviewed-deliverable registration or protocol adoption follows automatically.

## Final acceptance and execution handoff

The final technical gate passes only when all three reviewed phase commits exist, earlier experiments reproduce, the new experiment rebuilds in a clean checkout, all declared comparisons have results or justified undefined boundaries, workbench/reader checks pass, and the narrative explains strategic reach and honest-party impact across conditions. A missing declared case is not satisfied by a promise to test later.

Dispatch briefs must include the exact source/branch/commit, governing documents, allowed edits, reserved IDs, external run paths, acceptance commands and expected outputs; say “complete directly; do not spawn workers.” The integrator supplies those operational details without putting private paths or run reports in public artifacts. Recheck live issues and board read-only at execution kickoff. Preserve unrelated local work and never stage local agent instructions.
