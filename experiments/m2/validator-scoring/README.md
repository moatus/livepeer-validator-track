# EX-11: validator choices and conditional seat control

Task: [M2.9, issue 31](https://github.com/moatus/livepeer-validator-track/issues/31), GT-02 and GT-09. Drafted research; P1 and E2 remain pending owner review. This is a conditional calculation, not observed behavior, an equilibrium, a participation forecast or adopted policy.

Question: when is scoring from evidence privately preferable to leniency, abstention or an unsupported low score, and what conditional stake places a majority of seats?

[Assumptions](assumptions.md), [source manifest](input-manifest.json) and [finite comparison contract](cases.json) were fixed before outcomes. Their prospective status is retained as historical provenance. The calculation implements exactly 16 core choices, 12 named controls and 32 seat rows; no cost, ownership or coalition cross product. [build.py](build.py) writes ignored tables and all-pool ledgers; [verify.py](verify.py) checks independent arithmetic and boundaries.

## Sources and input status

October text SHA-256 `3e4a385ec19837f4b506b01989fac62cc33f99f28411bc1258f10c065e29240e`; PDF `b438da2b7d25d3043a3387b9db262293c2a0ec7801a765e5a3a249759b41569a`. Exact pages/lines are in the manifest and assumptions. September is historical. Paper-proposed quantities include 33 voluntary stake-ranked seats, median scores, a 1% validator allocation and the 840-round half-life. Missing-score rules, score magnitudes, eligibility and cuts applied to validator pay are illustrative completions.

The unchanged EX-06 S00 ledger uses all 100 pools from `livepeer-arbitrum-2026-10-09-v1`, round 4364 (2026-10-08T13:13:02Z to 2026-10-09T10:33:55Z exclusive). The illustrative launch ceiling is calibrated to that round's actual issuance: 29,288.551807149820347749 LPT. Historical ETH-indexed USD fees are replayed as hypothetical USDC at 1:1. Demand, execution cost and ownership proxies remain EX-06 assumptions. Valuation is 1.71765 USDC/LPT; burn execution price is separately passed at the same frozen number. Unsold LPT valuation is distinct from cash.

P1's frozen 90-day extract has file SHA-256 `b69e2b0949953b348470c772b4fc46f9c6510e37e3fb17b5f959a9fc7529d1c8`, content hash `9f1a8e13b628f68ab65a2a796bc344e455cbbadc55f68221daf39bf75c49c414`. Only its offline checkpoint raw pages are decoded; no generated P1 table is an input and no new extraction occurs. Checkpoints are 484622259, 494961555, 505240413 and 514893852. All indexed pools are ranked, separately from active flags and active-round bonded stake. Current-system observations are not a forecast under the proposed rules.

E2 supplies P (inconclusive purpose) and K (sufficient only for the selected K1 term breach, with authenticated accepted-term/job/node binding, independent delivered-byte custody and safe timely same-byte access stipulated). Knowledge-required stays unknown. Losing these conditions withdraws K sufficiency. No new evidence verdict is generated. VD-19 is a labelled research premise, not protocol policy; common ownership alone is not misconduct.

## Method and outputs

Cooperative C01–03 are calculated first: all 33 follow the available evidence, yielding P=1 and conditional K=0. Then the core compares E (review: P=1, K=0), L (lenient 1), A (missing), and U (unsupported 0). Each holds the other 32 at 16 zeros/16 ones as a pivotal control, not measured participation. F fills missing with 1 and takes the median over 33. Q excludes missing from its median, requires 17 of fixed 33 and retains prior 1 on failure; even medians average the middle pair. Invalid scores are rejected. K's E and U may have the same number but different evidentiary basis and effort.

`generated/core.csv` supplies each choice's receipts, target/delegator exposure, all three paired utility inequalities and its separate participation threshold. `controls.csv` supplies C01–12, including quorum boundaries, symbolic split/eligibility comparisons, earning ages 840/1680 and a symbolic later-claim median. `seats.csv` supplies 32 exact-wei seat rows; `p1_rankings.csv` retains every indexed address, rank and active/status flags; `p1_populations.csv` separates live-pool and active-round denominators. `tables.md` is a readable view of both tables. `results.json` includes all these rows plus original ledger fields for all 100 participants, network totals, all 33 validator receipts and cost symbols for each numerical case/control. C12 includes pending n+7 and full-score reference n+8 ledgers; its changed n+8 median remains symbolic.

The existing `capability-pricing/build.py` engine is loaded and left unchanged. Deep copies alter only target A's score/claim or the named schedule age. Target A is accounting stake rank 1; the focal validator is rank 2; all top 33 are stipulated to opt in, breaking ties by address. These are synthetic roles, not allegations against source addresses. Native own-node commission and owned-delegator fractions apply to validator pay as an assumption. Cross-node ownership x remains symbolic.

The overlay divides the engine's existing full .01C mint by active-seat bonded stake, independent of action. It does not mint again. Operator commission, owned delegation and outside-delegator validator receipts are separate. C08 compares equal versus stake pay algebraically; C09 compares active versus timely-submitter eligibility without choosing extra recipient identities. Empty eligibility leaves the full mint undistributed; a nonempty zero-weight denominator is undefined. Neither pay weights nor pay eligibility change score denominators.

## Conditional results and thresholds

With the pivotal background, F gives E/L/A/U multipliers 1/1/1/0 for P and 0/1/1/0 for K. Q gives 1/1/.5/0 for P and 0/1/.5/0 for K. Sufficient K evidence can support an adverse judgment, but actual submissions and their aggregation remain separate conditions. Cooperative C02–03 demonstrate a supported conditional adverse aggregate, preserving the paper's scoring defense within those conditions.

At the declared calibration, the focal participant retains 4.871863921126 LPT of validator pay, valued at 8.368157064122 USDC-equivalent per earning cohort before unknown role costs. Outside delegators at that validator receive 43.845720023246 LPT; gross validator receipt is larger than participant retention. Target A's full-score node claim is 846.047413771421 LPT, valued at 1,453.213340264482 USDC-equivalent before ownership cuts. The ledgers show its retained and outside-delegator components separately. Other nodes' rewards and validator pay stay unchanged when A's score changes. No withheld rival allowance transfers to the scorer; missed rewards are not principal slashing.

Write D_i(a)=c_i(a)+o_i(a)+alpha_i(a)K_tool, all USDC per cohort; Z_i(a) is an unknown signed residual for business, standing, retaliation, network-value or coordination effects. Shared network tooling K_tool is separate from private interpretation/submission effort and is charged only through each participant's allocated share, not in full to everyone. Opportunity cost excludes the same hours already in c. Unknown hours and wage remain unknown.

For each pair a,b, prefer a only when:

```
D_i(a)-D_i(b) <= P_claim*(retained_G_i(a)-retained_G_i(b))
                 + x_i,target*P_claim*(R_target(a)-R_target(b))
                 + Z_i(a)-Z_i(b)
```

All three inequalities must hold to prefer a over all choices; equality allows a tie. Other cross-node reward terms cancel in this score-only comparison. Base validator-pay differences are zero. For example, K/F E versus L requires extra review/opportunity/tool cost <= −1453.213340264482*x_i,target + DeltaZ. K/Q E versus A has coefficient −726.606670132241. P E versus L has zero reward coefficient; K E versus U also has zero coefficient, preserving the different basis. Conditional positive extra effort with equal other costs and residuals favors the cheaper identical-score action; no observed sign of those unknowns is assigned. Shared tooling may lower private effort but does not establish free review.

Joining versus declining is a separate inequality:

```
incremental D <= P_claim*(retained_G_i + sum_j x_ij*(R_j(a)-R_j(replacement))) + DeltaZ
```

Cooperative evidence-following replacement makes the node difference zero; the validator-only affordable total cost is 8.368157064122 USDC-equivalent at r=0, 4.184078532061 at r=840 and 2.092039266031 at r=1680, holding valuation and all other terms fixed. Outside cooperative controls, replacement scores remain unknown. For reward-difference quantity H in LPT, the valuation threshold is (incremental D−DeltaZ)/H when H>0; reverse the inequality for H<0. If H=0, cost <=DeltaZ is required, with no finite price threshold that changes the sign. Fees and node business receipts retained on declining are not foregone validator pay. No participation-rate prediction follows from shrinking scheduled compensation.

Node accounting preserves fees/jobs/execution costs and burn. At full scores S00 node mint is 5,231.546419663645 LPT, MFS-unused 22,299.692279057186, validator mint 292.885518071498 and treasury mint 1,464.427590357491. For each ledger, ceiling = node actual mint + MFS-unused + score-withheld + pending + validator full mint + treasury full mint. Lowering A's score reduces issuance under the inherited score-withheld non-minting completion. Claim n+8 applies m8 to the original earned allowance; it does not apply an additional schedule decay. Pending is not collected income.

Seats require 17 of 33 under hypothetical unlimited eligible registration/opt-in and fixed incumbents. For separately varied largest k coordinated incumbents or largest d decliners, new capital is (17−k)*(original rank 17+k+d stake+1 wei); existing controlled holdings are separate. The end-checkpoint base is exactly 6,454,209.130265542461741864 LPT. Redistribution uses the smallest number j of highest-stake donor pools with controlled stake strictly greater than 17*(original rank 17+j stake+1 wei). j=2 at all four checkpoints. At the end, stipulated controlled donor stake is 8,563,354.934939629961370029 LPT; 6,206,912.316848201439881046 funds entrants and 2,356,442.618091428521488983 remains outside eligible nodes. It requires control and mobility of delegated stake, not merely pool operation. Thresholds are not acquisition costs; majority seats do not establish an actual attack, and submitted-score influence is distinct from seat control.

## Limits and reproduction

Private/contested effort, opportunity cost, shared-tool engineering cost/incidence, signed residuals, cross-node beneficial ownership, acquisition/control prices, available liquidity and proposed-rule movement costs are unknown. Addresses do not identify organizations or misconduct. No token-purchase model, behavioral probability, practical evidence-access result or successor mechanism is supplied. The appendix work/score-weighted reward wording remains unresolved; adverse appendix scores exceed EX-06's interface. Results are conditional on main-text MFS and the declared score-withheld completion.

From repository root, Python 3.10+ standard library only, offline, no Git metadata or credentials required:

```bash
python3 experiments/m2/validator-scoring/check_inputs.py
python3 experiments/m2/validator-scoring/build.py
python3 experiments/m2/validator-scoring/verify.py
```

The input check establishes 39 source pins and the prospective contract, not validity of evidence judgments. The verifier uses independent hand constants for aggregation, compensation, utility units, two-pool accounting and exact-wei seats; checks empty/missing/invalid/even/quorum and zero denominators; replays all-pool accounting, conservation, earning/claim separation, independent P1 source constants and original EX-06 fixtures without writing historical outputs. These checks cannot establish unknown costs, beneficial ownership, production custody/access, actual submission or policy adoption. Stop at the finite tables and inequalities; materially changed evidence, rules or costs can reopen them. Practical effort/access work belongs to M4.2 and procedure to M4.3.
