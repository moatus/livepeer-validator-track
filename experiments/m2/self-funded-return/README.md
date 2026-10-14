# M2.2 self-funded real job: incremental return (EX-03)

**Historical September experiment.** Its original assumptions, arithmetic and line citations are preserved. October supersedes the open emissions concepts and clarifies that unused MFS node allowances are never minted; see the [October reconciliation](../../m2/october-reconciliation/README.md). This experiment is not a current-paper result.

Version **v0.1**. Status **Reviewed by the owner, 2026-10-14**. This bounded example asks whether one additional real job returns more to the organization controlling payer and node than it costs, under each litepaper emissions concept and both node-entitlement readings. It implements [SPEC §5.4](../../../docs/m2/SPEC.md). All results are **illustrative** arithmetic; they are neither protocol decisions nor observations of the network.

## Source and scope

Doug Petkanics, *Livepeer 2.0 Litepaper* (Sept 2026), repository snapshot [docs/sources/litepaper-2026-09.md](../../../docs/sources/litepaper-2026-09.md), SHA-256 `5fc153408fb636d9750788ae987ada6daaa9fc3df3e44f70cadde51a6158fb71`. The build refuses a changed snapshot. Relevant passages: MFS L55–63; median L84–86; claim-time score L109/L224; separate fee/burn and mint L117–121; open emissions concepts L128–172; appendix distribution L231–235. The workbench's M2.1 register I-01–I-22 supplies the readings. The intended contribution is fees for real, honest work (L35); whether the objective distinguishes reward-seeking real usage from useful internal work remains open.

The observation boundary is one round of the paper's stated accounting under those readings, with others' choices fixed. No current-system data, equilibrium, prevalence or forecast is supplied. Payment, execution, correctness, availability, independent demand, economic value and dishonesty are distinct claims. Positive return and common ownership do not establish misconduct or what a validator can detect.

## Inputs and status

| Input | Value and status |
| --- | --- |
| Outside network fees before job, F (including A's f) | Paper-reported year-0 $1.1M annually (L148), used as **illustrative scale**, divided by illustrative R_y=365 rounds/year: 3,013.698630 USDC/round |
| A's stake share s; initial outside fee share b=f/F | **Illustrative** s=0.01, 0.05, 0.20; b=s/2 and 2s; fixed positive network stake |
| Added job fee x | **Illustrative** x/F=0–64; exact share/pool thresholds included; far endpoint only locates arithmetic sign changes, not a plausible activity forecast |
| Node cut n; node mint share | **Paper-proposed** 0.5 and 0.94 (L119, L231); separate validator/treasury envelopes 0.01/0.05 (L232–233) |
| Organization's stake ownership ω; fee retention ρ; reward cut φ | **Illustrative** 1 each; code retains these inputs and excludes receipts to outsiders |
| Cost κ; internal use value u | **Illustrative** κ=0.3 per USDC; SC-07 u=0; SC-23 symbolic u>0, tabulated at illustrative u=1; SC-06 has the same accounting apart from u |
| Mint/claim prices | **Illustrative** P_mint=P_claim=1 USDC/LPT for unit labels, positive and equal; price effects, financing and slippage held at zero |
| Claim and scores | **Paper-proposed** claim n+7, current median (L109/L224); **illustrative** median 1 and all other medians 1; no missing score in the supplied full odd scoring set |
| q, probability of a zero median after the addition | **Illustrative sensitivity**, 0, 0.05, 0.5, 1; same q on SC-23 is a false-cut sensitivity, not measured error |

## Method

Outside service (SC-01) comes first: the organization pays nothing, receives the node cut and bears execution cost, so ΔCash=0.2x. Useful release testing (SC-23) follows, beside self-funded real work (SC-07). Inside the organization, cancel the payer/node transfer: ΔCash=−x+nx[ρ+(1−ρ)ω]−κx+ux=(u−0.8)x. The network half leaves once; burning purchased LPT is not another expense. Declining the job (x=0) changes neither reward nor cash, and Δ/x is undefined. An outside-fee start above stake also represents ordinary pressure on a productive node's reward ceiling.

Let a=(f+x)/(F+x) and N=0.94E, with E in LPT. MFS reward is N min(a,s)m, unnormalized; unassigned or withheld amounts are not redistributed. The appendix reading interprets work as fee share: R=N am/(am+1−a), with no stake term and the score applied once. Organization reward is R[φ+(1−φ)ω]. Before-job R uses x=0 and median 1. Δ=P_claim(R_after_org−R_before_org)+ΔCash, converting LPT only at the stated claim price.

| Concept | USD-equivalent pool before conversion to LPT; status |
| --- | --- |
| C0 | Fixed at C1(x=0)=32F, **illustrative analytical control** |
| C1 | min(32(F+x),50M/R_y), **paper-proposed year-0 ratio/cap** |
| C2 | max(0,35M/R_y−x), **registered starting-mint reading**; zero floor illustrative; F_0=F |
| C3 | Participation fixed within round; pool calibrated to C0, **illustrative**; not an inferred participation function |

C1's cap begins at illustrative x/F=0.420455; C2 reaches its illustrative zero floor at 31.818182. C0/C1 start at $35.2M annual equivalent rather than rounding to the table's $35M; C2 starts at $35M. The literal C2 combined-ceiling reading is carried without computing it. Other windows, prices, later claims and redistribution are not calculated.

Analytic derivatives report ∂Δ/∂x beside Δ/x. At the MFS threshold or C1 cap, left/right slopes are distinct; the derivative there does not exist when they differ. Break-evens solve the exact piecewise linear/quadratic identities, excluding the trivial zero-job root. Signs are checked between roots across 0<x/F≤64. The generated Markdown tables include every concept, reading, stake/start and choice.

## Illustrative results

For SC-07, q=0 and the above controls, each numeric cell below is a nonzero break-even x/F: return is positive below it, zero there and negative above it through 64. “Negative throughout” means no sign change in the swept range. Values are rounded; scripts retain full arithmetic precision.

| Concept / reading | s=.01, b=s/2 | s=.01, b=2s | s=.05, b=s/2 | s=.05, b=2s | s=.20, b=s/2 | s=.20, b=2s |
| --- | ---: | --- | ---: | --- | ---: | --- |
| C0 / MFS | .188000 | Negative throughout | .940000 | Negative throughout | 3.760000 | Negative throughout |
| C1 / MFS | .301282 | Negative throughout | 1.730455 | .790455 | 6.921818 | 3.161818 |
| C2 / MFS | .184761 | Negative throughout | .882795 | Negative throughout | 3.027236 | Negative throughout |
| C3 / MFS | .188000 | Negative throughout | .940000 | Negative throughout | 3.760000 | Negative throughout |
| C0 / appendix | 36.412000 | 35.848000 | 35.660000 | 32.840000 | 32.840000 | 21.560000 |
| C1 / appendix | 52.222605 | 51.663211 | 51.476769 | 48.681565 | 48.681565 | 37.537553 |
| C2 / appendix | 16.640716 | 16.374775 | 16.286129 | 14.956426 | 14.956426 | 9.637618 |
| C3 / appendix | 36.412000 | 35.848000 | 35.660000 | 32.840000 | 32.840000 | 21.560000 |

**Illustrative interpretation of the appendix roots.** Under C0, with z=x/F and b=f/F, Δ/x=(0.94·32)(1−b)/(1+z)−0.8, so z*=37.6(1−b)−1. At every C0 root the organization's fee share a=(b+z)/(1+z)=1−0.8/(0.94·32)≈97.34%. Its absence of a stake term leaves loss boundaries only after added fees dominate the stated outside-fee baseline: 21.6–36.4 times F for C0/C3, 37.5–52.2 times F for capped C1 and 9.6–16.6 times F for C2. Here F includes A's starting outside fees, not just other nodes' fees. The 97.34% share applies to C0/C3; C1's cap and C2's shrinking pool change the root share, to about 98.1–98.4% for C1 and about 94.4% for C2 across the six starts. These are exact algebraic results, not grid or rounding artifacts, and do not establish a practical job-size defense at this scale. The C0 root position scales nearly linearly with the paper-proposed year-0 ratio 32 and node share 0.94 (L134, L231, L234), relative to the unrecovered 0.8 per USDC (paper-proposed 50% network half plus illustrative κ=.3, with full ownership). Node cut, costs and ownership change it; the paper's later-year ratios are not computed here.

**Illustrative defenses and boundaries.** Above the MFS ceiling, fixed C0/C3 gives Δ/x=−0.8; positive C2 gives −0.8−0.94s. Below that ceiling, share-taking can cover costs. C1 before its cap gives Δ/x=0.94·32−0.8=29.28 while below stake, and 0.94·32s−0.8 when already above stake; the latter changes sign at illustrative s=0.026596. After the cap and stake ceiling both bind, marginal return is −0.8, even if average return remains positive from the earlier gain. Thus the network charge and costs work in the loss regions, the stake ceiling stops share growth, and the emissions cap stops pool growth, each with that reach. The appendix reading has no stake defense. At fixed f, changing s alone has no effect on its arithmetic.

For illustrative s=.20, b=.10 is below stake: the share reaches .20 at x/F=.125. Starting b=.40 has no room to increase the MFS share. This is arithmetic only, without validator participation or added-stake analysis.

At q=0, SC-01 and SC-23 (u=1) are positive for added jobs over 0<x/F≤64 in every concept, reading and start except C2 with the appendix reading at s=.20, f/F=.40: there both are negative between the illustrative break-evens x/F≈24.0128 and 59.8182, and positive before and after that interval. The C2 pool is zero from illustrative x/F≈31.8182, so the node's whole before-job reward is lost while cash from the node cut (and, for SC-23, use value) still accrues at 0.2x after execution costs and any payer expense. At x=0 the job is declined and Δ=0. For any other internal value, Δ23=Δ07+ux; the threshold is u*=−Δ07/x (already-positive SC-07 requires no positive minimum value). A negative SC-07 result therefore need not make useful internal testing unattractive. Its purpose does not appear in the reward formula.

**Illustrative score sensitivity.** E[Δ]=Δ(q=0)−q P_claim R_after_org, and q*=Δ(q=0)/(P_claim R_after_org) when base return is positive, otherwise “none.” Positive return with zero after-job reward has no finite q*: q cannot change it. The reward at risk includes outside-fee reward. At x=0 there is no added-job event and q is not applied. At q=1 every positive-size SC-07 choice loses its before-job reward plus 0.8x. SC-23 loses the same whole-round reward, counted as a false-cut cost. The generated q* table covers both cases; q* above 1 for a useful job means no feasible q makes its expected return nonpositive.

For **illustrative** s=.05, b=.10, x/F=.01, all other inputs as above:

| Concept / reading | SC-07 q* | SC-23(u=1) q* | SC-23 lost reward at q=.05 (USDC) |
| --- | ---: | ---: | ---: |
| C0 / MFS | none | .001330 | 226.630137 |
| C1 / MFS | .004635 | .011218 | 228.896438 |
| C2 / MFS | none | .001023 | 225.271644 |
| C3 / MFS | none | .001330 | 226.630137 |
| C0 / appendix | .079376 | .082429 | 493.649803 |
| C1 / appendix | .088491 | .091514 | 498.586301 |
| C2 / appendix | .079073 | .082144 | 490.690709 |
| C3 / appendix | .079376 | .082429 | 493.649803 |

**Other nodes, holding their fees/stake/scores fixed.** Under MFS, another node with fees g and stake share t earns 0.94E min(g/(F+x),t). C0/C3 leave a still-stake-limited reward unchanged and reduce a fee-limited reward; A's gain need not all displace others because the MFS remainder can change. Uncapped C1 leaves fee-limited rewards unchanged and can raise stake-limited ones. Capped C1 makes them unchanged or lower; positive C2 lowers them. At the C2 zero floor all node rewards are zero. Under the appendix reading at median 1, other nodes collectively receive N(1−a): C0/C3 and C2 reduce that amount, while C1 preserves it before the cap and reduces it after. A zero median does not redistribute MFS withholding; appendix normalization reallocates the envelope to other nodes. Mint targets do not establish actual minted supply or net supply after burn.

## Limits and reproduce

No conclusion about a missing intended contribution or an obtainable dishonesty finding follows from these returns. The claim delay is respected, but actionable evidence and the feasibility of q are untested. Locked principal is not lost. Validator receipts to this organization are zero despite the separate paper-proposed envelope. Outside delegation, higher cost, later ratios, 28.8 baseline, lagged windows, price differences, financing, buyback effects and added stake are outside the pilot comparisons. Verification includes one ownership fixture solely to check that the code excludes outsider receipts; it is not a pilot sweep.

Requires Python 3.10+ with only its standard library. From the repository root:

```bash
python3 experiments/m2/self-funded-return/build.py && python3 experiments/m2/self-funded-return/verify.py
```

Build writes generated `sweep.csv`, `break-even.csv`, `sensitivity.csv` and `tables.md` beside the scripts; these outputs are not committed. CSV rows are labelled illustrative; `sweep.csv` includes the before/after organization LPT, cash, Δ, Δ/x, left/right slopes, use-value threshold and q*. `break-even.csv` supplies signs and roots for all choices. `sensitivity.csv` supplies expected returns and SC-23 false-cut costs. `verify.py` checks hand constants EX-03.F1–F8 and four distinct additional branches (C1 cap, C2 floor, fractional appendix median and outsider receipts), plus analytic roots, derivatives and whole-round loss across the stated regions. It also asserts all 96 outside/testing sign regions, including the two-root C2/appendix exception for each case. It never reads the generated outputs.
