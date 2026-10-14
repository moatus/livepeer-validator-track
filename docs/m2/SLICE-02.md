# Slice 2: capability, pricing and self-funded traffic

Status: **drafted: connected accounting (EX-06) and evidence results (EX-07) consolidated in M2.3; reviewed by the owner, 2026-10-14 ([#27](https://github.com/moatus/livepeer-validator-track/issues/27))** · 2026-10-10 (prepared 2026-10-09). This is the next numbered M2 slice under [SPEC.md](SPEC.md) and [RUNBOOK.md](RUNBOOK.md). It builds on October reconciliation EX-05 and preserves September EX-03/EX-04. Preparation does not confer human review or protocol adoption.

The defined follow-up, [Slice 2b](SLICE-02B.md), extends these results with strategic spending, actor ranks and multiple whole-network conditions. Its [implementation plan](SLICE-02B-IMPLEMENTATION.md) has separate M2.1, M2.2 and M2.3 workloads. It preserves this slice's frozen inputs and source-scoped results; no broader test is retrospectively attributed to EX-06 or EX-07.

## Question and bounded outcome

Under October's scheduled emissions and network-wide fee share, when do capability entry, ordinary price competition and real self-funded jobs change operator income, rewards, burn and actual issuance? What observations could establish the economically relevant distinction between useful niche/internal work, legitimate discounts and the specified alleged violation?

Produce one reusable accounting ledger and a small ordered scenario table. Do not build a network simulator, infer observed misconduct, or assume a separate reward pool for each capability. Being the sole provider can affect routing; it does not create a separate fee denominator or automatic reward entitlement. The contribution the paper intends to reward must be stated before interpreting a profitable choice.

## Inputs to freeze at Stage A

| Input | Source / rule | Limit |
| --- | --- | --- |
| October paper | [PDF](../sources/litepaper-2026-10.pdf), SHA-256 `b438da2b7d25d3043a3387b9db262293c2a0ec7801a765e5a3a249759b41569a`; [extraction](../litepaper-2.0.md), SHA-256 `3e4a385ec19837f4b506b01989fac62cc33f99f28411bc1258f10c065e29240e` | `SRC-LP20-OCT`; verify hashes before using line locators. MFS L123–150; scoring L198–213; fee split L298–307; schedule L388–395; unminted node allowance L413–416; fee-linked attack discussion L462–470; appendix L646–670. Preserve main-text/appendix mismatch. |
| Historical pilot | [September text](../sources/litepaper-2026-09.md), EX-03 and EX-04 | Old concepts C0–C3 are historical, not October alternatives. Use original fixtures to check continuity, not current policy. |
| Measured snapshot | [Reader contract](../../experiments/m2/network-snapshot/README.md), ID `livepeer-arbitrum-2026-10-09-v1`; content hash `b879cc73be95d0e5bdcd5c5bc2f2bc342a7319eb27cb6ffdd2ee6c25f4bb60e8` | Completed round 4364 for matched stake, fees and allowance. Raw redeemed-fee series is primary; 30-day aggregates are context, never silently divided into a matched round. |
| October bridge | `experiments/m2/october-reconciliation/`; EX-05 | Consume verified results and source assumptions; no extrapolation from one frozen round to future annual issuance. |
| M1 questions | GT-03, GT-07; GT-01; GT-04, GT-10 boundary inputs | SC-01, SC-03, SC-04, SC-06, SC-07, SC-12, SC-23, SC-29–SC-31, SC-40–SC-43; MX-02, MX-04, MX-06, MX-07, MX-09, MX-12; CN-21 selection rule. Read current October annotations. |
| Price, volume and cost | Explicit scenario configuration | No measured capability demand, routing elasticity or unit cost exists in the baseline. Job counts are synthetic units; map measured fee receipts to illustrative price × volume transparently. Unit cost is independent of invoice price. |
| Stake and retention | Same-round stake/cuts; explicit organization boundary | Capture-time operator-address stake is only a proxy for organizational ownership and its application to round 4364 is an assumption. Keep other-address receipts visible; do not identify beneficial owners. |
| Reward and burn prices | Explicit positive LPT price assumptions | Report token and currency quantities separately; no endogenous token-price effect or price forecast. |

Stage A records all selected JSON pointers, input/output units and overrides in `inputs.json` (planned). Fees measured in indexed USD are replayed as hypothetical USDC only under a named conversion assumption. Preserve all 100 pools in network totals and every applicable historical fee recipient if using the history series. Other pools can be aggregated for display, never dropped from calculations.

## Shared accounting contract

For each operator and capability, distinguish outside jobs `q_out`, controlled jobs `q_self`, price per job `p`, cost per executed job `c`, and separately stated setup cost or internal use value. Fees are `p × (q_out + q_self)`; resource costs are `c × (q_out + q_self)`. Do not scale `c` automatically when `p` changes. Use capability-specific costs where required, and name the common job unit before combining volumes.

For a declared round since launch, compute the scheduled allowance from `EmissionBase × 2^(−r/840)`, or use an explicitly labelled measured-round calibration. State the calibration rather than treating the deployed round number as rounds since a hypothetical launch. The main-text base reading uses `0.94 × allowance × min(operator fee share, operator stake share) × median score`. Record unallocated or score-withheld amounts and their timing interpretation. Validator and treasury shares sum to 6% and mint in full under the October paper. Keep their recipient allocation separate from modeled operator-role income, and do not invent validator receipts for selected operators.

Show the appendix reading in one matched control if it changes the conclusion; do not repeat the September emissions sweep. At zero network fees, define MFS fee shares as zero under an explicit model boundary convention and identify appendix normalization as undefined unless a separate rule is registered.

Apply operator fee and reward cuts, then the organization's declared ownership share to the delegator remainder. Show external delegators' receipts separately. For controlled purchases, cancel internal transfers exactly once at the organization boundary; retain payment leakage to the network, outside owners and execution providers. Report cash return separately from declared internal use value and token valuation. “Income” must say whether execution/setup costs and controlled-payer outflows were deducted.

Each scenario reports:

- Outside and controlled job volumes by capability, outside spending and controlled spending, total network fees and selected operator fee shares.
- Operator retained fee and LPT receipts, outside delegator receipts, organization net cash/value and changes for the rest of the network.
- Network buyback spending, assumed burn execution price and tokens burned; the unmodeled cost/slippage boundary.
- Scheduled LPT ceiling, claimable node LPT, node LPT actually minted under the stated claim assumption, unminted node allowance, and full validator/treasury mint. If burn is converted, show net token supply change.

Claimable is not already minted. A full-claim baseline may make them equal at the declared claim horizon; a delayed/unclaimed sensitivity keeps them separate. A fall in all fees at unchanged relative shares leaves MFS rewards unchanged at fixed stake/scores, but changes burn spending. A redistribution of fees may change both total claimability and individual rewards. Test both rather than applying the proportional case universally.

## Finite scenario sequence

Stage A may amend the grid with a recorded reason before results, but must keep these comparisons and the stop boundary.

| Order | Comparison | Controlled change and legitimate reference |
| --- | --- | --- |
| 0 Cooperative | Outside customers buy useful service; no controlled purchases | Baseline snapshot scale; explicitly synthetic job/capability decomposition; all parties' accounting balances. |
| 1 Ordinary competition | One operator discounts an existing capability; then a share-constant network price reduction | Hold unit execution costs fixed. For the unilateral discount use both unchanged outside demand and a stated rerouting rule; preserve total outside volume in the rerouting control. No invented empirical elasticity. |
| 2 Capability entry | A sole provider lists a real niche capability | Compare outside-funded useful demand and internal production/testing against added controlled work with no assumed use value. State setup cost, demand and capacity boundary; all fee shares remain network-wide. |
| 3 Controlled purchases | Add real self-funded jobs to the discounted or niche offer | Compare matched price/cost/jobs where possible; cheapest status explains route choice but proves neither independent demand nor improper intent. Include a pre-existing fee share above the stake cap as counterevidence. |
| 4 One response | One competitor matches price **or** one explicit stake movement after its stated delay | Recompute the entire network denominator and consequences once. This is bounded feedback, not an equilibrium or prediction; movement speed remains for P1/Slice 5. |

Limit the main table to **12 scenarios**, including controls. Use no more than two selected operators for detailed changes (one below and one above the stake cap if available), preserving all other pools. One synthetic boundary fixture may supply a missing above-cap position. At most **three price levels and three independent unit-cost levels** in a separate one-factor sensitivity; do not take a Cartesian product with every score, ownership and routing choice. Test score 1 and one explicitly stated adverse-score bound, outside ownership and one alternative retention bound, and a fixed-price valuation sensitivity only where each can change a decision. Stop once the questions have conditional signs and boundaries; record further questions for their preserved studies.

## Stage A — reconstruct and freeze

Read the manifest, current M1/M2 records and EX-05. Produce the rule register, compact participant/control map, source-version timeline and finite grid. Explicitly state routing, total outside demand, niche demand, unit cost, capacity, self-funding budget, stake timing, cuts, organizational ownership, score/claim rule and full-mint assumptions. Classify every entry as paper-stated, measured, illustrative or unresolved; mark computed, stated or deferred. Confirm the intended contribution and narrow/broad allegation readings without introducing a common-ownership or independent-customer requirement as paper policy.

Deliver a reviewable change set for M2.1, GT-03/GT-07 and bounded GT-01 handoffs; a machine-readable input manifest and scenario schema; exact reservations for new records; Stage B/C briefs updated only where the reconstruction requires it. **No scenario outcomes in Stage A.** Illustrative inputs are allowed. Pass when every Stage B/C dependency is identified and a reader could recreate the prescribed comparisons.

## Stage B — model

Create EX-06 in `experiments/m2/capability-pricing/` (planned): `README.md`, `inputs.json`, `build.py`, `verify.py`; use Python standard library and `Decimal` accounting through the snapshot reader. Generate a scenario CSV and short Markdown accounting report; generated outputs stay ignored. Reuse EX-05 accounting only through an explicit import or a clearly checked common interface, never by copying its output as measured input. A sibling dependency must reproduce in a clean checkout.

Verify independent hand-calculated fixtures and invariants: internal-transfer cancellation; external-owner exclusion; price changes at constant cost; network denominators under rerouting and capability entry; proportional fee compression at constant shares; above-cap and zero-fee boundaries; conservation of receipts, fee split and burn; ceiling = node minted + unminted node allowance + validator/treasury mint under the full-claim convention; score and unclaimed cases; and the surviving appendix comparison. For delayed claims, reconcile pending claimable amounts separately so the equation does not mislabel them permanently unminted. No profitable outcome is itself an adverse-evidence finding.

Pass when one reproduce command rebuilds deterministic tables, independent fixtures pass, input provenance and non-selected operator effects appear in every result, and all comparisons have stated limits. Do not expand beyond the finite grid to chase an expected result.

## Stage C — focused evidence

Before outcomes, write and commit the tolerance/allegation document through the integrator. Build a bounded packet for niche useful work/internal testing versus controlled purchases, and ordinary discount routing versus the specified misrepresentation allegation. Reuse EX-04's claim matrix and explicitly keyed judgment readings; allow public records and one disclosed source in arrival order to the declared claim deadline. Keep CL-01/02/03/05/06/07 distinct. No new feed, ownership inference, truthful-purpose oracle or synthetic error rate is assumed.

Planned folder: `experiments/m2/evidence-capability-pricing/`, with tolerances, packets, source index, matrix/verdict CSVs, `verify.py` and README. Reserve the next experiment ID at Stage A after checking the current registry (EX-06 is the economic model). Check file/record paths, allowed values, source versions and per-tolerance outcomes. Report evidence separation separately from procedural score consequences and disclosure burden. **E2's original pairs remain pending unless separately completed and explicitly recorded.**

## Stage D — integrate

Connect every observed/modelled change to the relevant M1 mechanism, condition, beneficiary and cost bearer. Update M2.1 register outcome columns, M2.2 findings and M2.3 dispositions, without treating assumptions as demonstrated causes. Assess actual defenses and counterevidence, including MFS caps, non-minting, ordinary customer benefit and outside retention. Distinguish a surviving incentive, missing evidence, a policy definition and missing implementation detail. Preserve original EX/FR/CN identities and historical results.

Deliver a single concise connected comparison with links to the ledger, an evidence-limit table and a backlog showing what E2, P1 and Slices 3–8 still test. No M2 completion, human review or M3 mechanism is inferred. Stop when the bounded question is answered and every unresolved dependency has a named owner study.

## Pickup and stop conditions

The integrator checks live issue/board state read-only, current branch, existing local changes and source hashes; verifies the snapshot and EX-05; then creates the Slice 2 branch from the recorded October preparation commit. Preserve local authoring work. Reserve IDs using `vtw.py counts` and `find`; never assume this brief's next-free number remains free. EX-06 is reserved for this model; new FR/CN/I IDs are recorded in the Stage A brief after inspecting actual occupied IDs.

Stop a dependent calculation when a required interpretation has no defensible reading, a source/hash fails, or an assumption changes the declared question. Record capability data gaps and use labelled bounds where defensible; absent empirical routing data is not a reason to invent it or demand a new data collection project before starting. Paid access or external publication require the applicable authorization. Results weakening the concern are required outputs, not reasons to stop research. Stage A starts only when requested; this preparation does not execute it.
