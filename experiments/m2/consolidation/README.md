# M2 consolidation — finite delegation and source readings (EX-12)

Status: reviewed and accepted on 2026-10-27. This package completes the bounded inquiries for studies 5–8; the workbench records the complete M2 assessment and handoff. Research acceptance does not adopt protocol policy.

The accepted prospective [assumptions](assumptions.md) and [cases](cases.json) are preserved byte-for-byte from foundation `c421f028183c54c00f1f169e39d7e18fd8429fe0`. The [input manifest](input-manifest.json) retains the 103 source/contract pins used for reproduction. The original deliverable-register pin and its later publication identity are preserved separately as historical reporting metadata; that register supplies no calculation input and changes as research is accepted. Their “no computed outcomes” / `no_outcomes` declarations describe the prospective phase when the comparison was frozen. They are historical contract declarations, not assertions that this later package lacks results. The checker validates the source/contract pins; current acceptance status is recorded in the deliverable register. No source, selection, clock or rule pin was changed to obtain an outcome.

## Question, source versions and input status

Can stake reach a productive understaked node in time under the specified readings, and can the same fee opportunity arise from controlled real purchases? Separately, what do pinned selection code, pending-rule passages and buyback evidence establish? Stop after one fixed comparison and three source readings. No sweep, new collection, purpose detector, seat model, simulation, GT-03 optimization or successor mechanism.

October text SHA-256 `3e4a385ec19837f4b506b01989fac62cc33f99f28411bc1258f10c065e29240e`, PDF and historical September archive are pinned. October pp3–5 L125–258 grounds fees, MFS, active delegation, opt-in validators and elimination/delay of transfers; L248/L250/L257 say days while L233/L592 say rounds. These clocks are not equated. P6 L271–278 grounds current-at-claim medians; pp7–8 L382–416 the 840-round ceiling; p9 L464–470 and appendix L646–717 ground oracle removal, envelope ambiguity and DEX execution limits. Main-text MFS remains the base; appendix fee-work weighting remains unresolved.

Measured calibration is snapshot `livepeer-arbitrum-2026-10-09-v1`, content SHA `b879cc73be95d0e5bdcd5c5bc2f2bc342a7319eb27cb6ffdd2ee6c25f4bb60e8`, completed round4364, interval `[2026-10-08T13:13:02Z,2026-10-09T10:33:55Z)`, capture block513206238. All100 pools remain. S=29,903,540.460131219004671427 LPT; F=820.9606640078432096592741806596851 indexed USD, replayed1:1 as hypothetical USDC. Raw fee proportions and capture-time cuts/address-owned fractions are source inputs; applying those fractions backward is a proxy, not beneficial ownership. Costs, capacity, work, routing, timing, scores and future price are illustrative.

## Method and units

[build.py](build.py) calls the unchanged EX-06 `load_inputs()`/`account()` interfaces. Source rank50 target gets initial stake/fee shares .02, with the other99 proportionally reallocated. Rank1 donor retains its native cuts; its operator-owned LPT amount is fixed as outside-delegated .08S moves. Tiny residuals go to the frozen nonactor pools and are checked. Target k=.10,d=0,w=0; it remains unregistered as validator despite already being top-N eligible. Donor registration/distribution is unknown. Validator participant receipts are excluded, not zero; omission can understate forgone source yield if the donor registers and shares pay. Seat/scoring/governance interaction remains unassessed for GT-09.

Both SC-27 productive outside work and SC-28 controlled purchases execute matched x=4F/45=72.974281245142 USDC/job-equivalents at p1,c.30, raising target fee share to .10 for earning rounds0–23. Case purpose is modeler knowledge, not observable evidence. Original work persists. No-movement, fresh, unbond/rebond and delayed-transfer lanes produce 2×4×46=368 observation rows and192 earning cohorts. Decision1, fresh eligible2, existing withdrawal/completion22 and eligible23, exit24 and withdrawal45 are fixed illustrative choices. Fresh round1 is a bonding/activation wait, not an unbonding wait; the generated generic “initial wait” label is retained. Existing options implement the paper's elimination/delay requirement, not today's instant movement. Fresh dS=4S/45 increases S; existing .08S transfer restores S only on arrival; unbond interim reduces it to .92S. Source eligibility/score snapshots are readings requiring specification.

C(r)=C0×2^(−r/840), C0 calibrated through EX-06 to the measured round's actual-issuance scale at hypothetical launch age0. Deployed round4364 is not launch age. Cohorts earn only0–23, collect at n+7 through30. `pool-ledger.csv` reports each cohort at full-score claim; `rounds.csv` places node mint at actual claim and tracks pending separately. Validator/treasury full envelope mint is assigned at earning, without participant allocation. Later observation rows track claims/exit only; they do not represent a zero-activity network or earn new cohorts. Unused allowance is never redistributed. Principal is unavailable during locks, not confiscated, spent on jobs or compounded.

LPT rewards and USDC fees stay separate. Participant node LPT=(b/B)(1−k)R; USDC fee share=(b/B)d(.5f). Earning ownership survives exit. Operator cash subtracts the controlled invoice and all execution costs once. Internal payer receipts cancel; the network half funds burn, with no second charge. The declared 1.71765 USDC/LPT conversion values unsold LPT separately from cash and fixes burn execution; it is neither a market quote nor liquidity evidence. Acquisition/liquidity/gas/financing/opportunity costs and fresh outside return remain unknown.

## Results and measured context

Illustrative totals over24 earning cohorts, common to both cases for LPT receipts:

| Lane | New principal LPT | Destination delegator LPT | Source candidate LPT | Moving delegator net LPT vs staying | Moving delegator net USDC vs staying |
| --- | ---: | ---: | ---: | ---: | ---: |
| No movement | 0 | 0 | 10654.575261 | 0 | 0 |
| Fresh | 2658092.485345 | 44043.435900 | 0 | undefined: outside return unknown | undefined |
| Unbond/rebond | 0 | 1944.982778 | 448.166158 | −8261.426324 | −88.902916 |
| Delayed transfer | 0 | 1944.982778 | 10214.834654 | +1505.242172 | −3.865344 |

Fresh principal is distinct from2,392,283.23681049752037371416 LPT existing moving principal. The no-movement source row tracks that existing-principal benchmark. Fresh capital has no measured donor source; its outside return is unknown, while all original donor owners remain in the full pool ledger. The remaining-donor comparison holds the same outside-principal subset, excluding the .08S existing benchmark, fixed across lanes. The frozen window mechanically fixes fresh22/existing1 elevated eligible rounds. Neither overlap is a measured response speed or opportunity duration. Exit24 is modeler-fixed, not a decline observed at25 or foresight.

Donor-pool node rewards change by zero in every lane: this donor stays fee-bound in this calibration. Remaining donor-delegator LPT nevertheless rises10,203.185600 with unbond/rebond and439.601723 with delayed transfer, because its unchanged principal shares the pool with less competing eligible principal. Moving source receipts lost are10,206.409103 LPT/88.902916 USDC and439.740606 LPT/3.865344 USDC respectively. Do not infer a donor-pool reward loss from those participant losses. The interim .92S denominator also raises the target's share before arrival and changes other-pool MFS rewards. The computed cumulative effects are reported below, against the **same case’s no-movement lane**, summed over earning rounds0–23 and full claims7–30. SC-27 and SC-28 have identical LPT/fee-allocation effects under the matched work; their payer cash differs as above. All values are illustrative on the frozen calibration.

| Lane | Node actual mint LPT | Unminted node allowance LPT | Total actual mint Δ LPT | Target-pool mint Δ LPT | Other98 mint Δ LPT | Remaining-donor fee Δ USDC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| No movement | 133861.765886 | 520658.102541 | 0 | 0 | 0 | 0 |
| Fresh | 179045.817940 | 475474.050486 | +45184.052054 | +47958.407980 | −2774.355926 | 0 |
| Unbond/rebond | 139503.794848 | 515016.073579 | +5642.028962 | +3204.526724 | +2437.502238 | +88.874838 |
| Delayed transfer | 136022.857862 | 518497.010565 | +2161.091976 | +2161.091976 | 0 | +3.864123 |

The cumulative scheduled ceiling is696297.732369LPT in every lane. Validator/treasury envelopes mint6962.977324/34814.886618LPT, unchanged across lanes, so **total actual mint changes equal node mint changes**; total actual mint is175639.629828/220823.681882/181281.658790/177800.721804LPT in table order. Unminted allowance falls by the corresponding mint increase. Donor-pool mint Δ is zero in this fee-bound-donor calibration, not generally. Fresh stake dilutes stake-bound peers; interim unbonding reduces S and raises their shares.

The donor operator’s unchanged owned principal gains3.223503LPT/0.028078USDC with unbond/rebond and0.138884LPT/0.001221USDC with delayed transfer; fresh gives zero change. Its commission is unchanged because this donor’s pool reward/fees are unchanged. Moving-delegator forgone source receipts equal remaining-donor gains plus these donor-owned gains, separately in LPT and USDC, before rounding. This is redistribution within the fee-bound source pool, distinct from target receipts and network issuance. The CSVs retain exact decimals and every pool’s receipts; these totals do not add excluded validator-participant income or unknown costs.

Operator cash totals429.088774 USDC for SC-27 and−1322.293976 for SC-28 in every lane. Incremental work cash per round is+.2x=14.594856 versus−.8x=−58.379425, relative to original target work. Commission totals are1309.039737/6104.880535/1629.492409/1525.148934 LPT in no-movement/fresh/unbond/delayed order. These matched rewards and different payer costs supply no misconduct detector. Research premise VD-19 is distinct from protocol policy and common ownership is not itself abuse.

**P1 context beside the example:** the frozen90 UTC-day extract ending2026-10-15 independently reproduces104 instant bond redelegations totaling1,061,494.613512182428993605 LPT:3.620723% of29,317,201.302405724346755738 start active stake, or3.531673% of30,056,420.25136337776584275 end active stake. The102 intersecting-round average is10,406.809936 LPT; partial edges mean it is not decision latency, a proposed-rule rate, forecast or measured acquisition cost. Cross-delegate transfers separately total79,292.984791 LPT. Slower identified paths are three standalone rebonds339.525 LPT and seven later new-bond-class changes320,278.299237 LPT; later Bond funding is not established, within-window censoring remains, and transfer component flows must not be added twice. `p1_context()` reruns the pinned offline analyzer and event reconciliation from the frozen raw extract, intercepting writes into a compact result; no generated P1 table supplies inputs.

The full-score base retains the paper's score/lock boundary: at claim median m, all operator/delegator cohort node LPT scales by m; m=0 removes those receipts while paid fees remain. Source stake exposure during delay persists under the declared reading; principal is locked, not slashed. Anticipation, detection and actual validator action are unmodelled. At full scores the appendix fee-weight-only reading does not change target reward weight when stake arrives; no adverse appendix formula is invented.

Studies 6–8 are recorded in the workbench: [access (GT-07)](../../../validator-track-workbench.html#GT-07), [pending rules (GT-08)](../../../validator-track-workbench.html#GT-08) and [buyback execution (GT-10)](../../../validator-track-workbench.html#GT-10). Each question records its sources, assessment, limits and remaining work. Detailed dispute procedure belongs to M4.3.

## Reproduce and inspect

Offline Python3.10+ standard library, from repository root, no Git metadata required:

```bash
python3 experiments/m2/consolidation/check_inputs.py
python3 experiments/m2/consolidation/build.py
python3 experiments/m2/consolidation/verify.py
```

`generated/` is ignored: `rounds.csv`368 rows; `cohorts.csv`192; `pool-ledger.csv`19,200 with all100 source addresses; `summary.csv`8; compact `p1-context.json`, `calibration.json`, `results.md` and `hashes.json`. Decimal precision60/half-even for accounting; pinned P1 analysis preserves its historical precision100, then accounting context is restored. No output supplies an input. Reproduction regenerates all hashes deterministically.

[verify.py](verify.py) EX12.F1–F8 checks independent denominator identities, actual interim/source receipts, claim boundaries and preserved earning ownership, cash cancellation, all-pool ledger conservation, a hand6LPT/8USDC allocation, zero-score/fee/stake edges and appendix stake independence. These establish arithmetic under readings, not real acquisition cost, future behavior, prevalence, practical access, executed buybacks, fairness or owner acceptance. Historical engines/results/denominators and prospective inputs remain unchanged.

## Complete M2 assessment

[Workbench M2.3](../../../validator-track-workbench.html#M2.3) contains the complete assessment and M3 handoff, including retained strengths and concrete M4.1/M4.2 evidence destinations. Its linked critical-question records contain the source/result chains. The study-specific result text above retains its calculation boundary. The synthesis and shared network snapshot were reviewed and accepted on 2026-10-27. Exact reviewed versions are recorded in the [deliverable register](../../../deliverables/README.md). No protocol policy is adopted.
