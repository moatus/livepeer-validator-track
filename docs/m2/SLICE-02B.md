# Slice 2b: strategic self-funding across network conditions

Version **1.1 · 2026-10-12**. Status: **defined; implementation pending**. Owner: Shane (@moatus). This definition records the requested follow-up to [Slice 2](SLICE-02.md); it is not a research result, human acceptance or protocol decision. Its three implementation workloads are in [SLICE-02B-IMPLEMENTATION.md](SLICE-02B-IMPLEMENTATION.md).

## 1. Question and precedent

How much additional retained value can a largest-, middle- or lower-stake operator obtain by deliberately funding real jobs, where would its one-round profit-maximizing spending stop, and which honest participants lose rewards across materially different network conditions? Short fixed-budget timelines additionally test spending pace and collection, not a multi-round optimal strategy.

The precedent is EX-06's all-pool accounting and EX-07's separation of economic outcomes from obtainable adverse evidence. EX-03 supplies historical threshold methods; EX-05 supplies the October source and schedule bridge. Extend that accounting with explicit network fixtures, bounded spending optimization and short cohort timelines. A second reward engine or a network simulator is unnecessary. The new scenario adapter is necessary because EX-06's loader and A/B comparisons are pinned to one configuration; its generic accounting function is reusable only through a checked interface.

The owner requested this design before implementation. M2.1 materializes and validates it; it does not choose a new study design. Preserve EX-03 through EX-07, their frozen configurations, historical sources, IDs and original results. Recalculate the scope of conclusions after the additional tests rather than retroactively changing what earlier experiments tested.

## 2. Settled interpretation and research boundary

- October is the active source. Main-text MFS is the primary rule: node entitlement is `0.94 E(r) min(f_i/F, s_i) m_i`. Unavailable MFS allowance is not minted; validator and treasury envelopes mint in full. Keep one matched appendix comparison for each actor rank. No September fee-linked schedule is a current rule.
- Calibrate `EmissionBase = E0` to the shared snapshot's completed-round ceiling, with hypothetical launch-relative `r=0`, and use `E(r)=E0 2^(-r/840)`. Deployed round 4364 is not rounds since launch. No launch date or approved calibration is inferred.
- The strategic actor's stipulated ground truth, known to the modeler and not observable by validators, is reward-seeking real work with no credited productive/internal use. The owner regards the selected behavior as dishonest for the scenario. Record this as a scenario premise; the paper's eligibility criterion remains VD-19 and an obtainable violation remains a separate claim. Common control, profit, price or capability uniqueness alone establishes neither.
- Honest outside service and useful internal work remain legitimate references. Each strategic spending choice has a matched useful-internal reference with identical fees, costs and rewards and declared use value `1 USDC-equivalent/job`.
- Hold fair validator behavior and full median scores in the core. Hidden purpose is unavailable to validators. Do not invent validator income for the strategic operator or treat a score sensitivity as a warranted sanction.
- One strategic operator at a time. Others initially keep their outside jobs, prices and stake. No collusion, ownership discovery, endogenous LPT price, equilibrium, prevalence or automatic customer departure is inferred.
- This is finite worked accounting and optimization, not agent-based simulation. Original E2, P1 and studies 3–8 retain their identities and pending practical inquiries. Existing EX-07 evidence judgments are consumed, not silently extended into new evidence packets or detection statistics.

## 3. Sources and reproducibility

Use the [shared snapshot reader](../../experiments/m2/network-snapshot/README.md), ID `livepeer-arbitrum-2026-10-09-v1`, content SHA-256 `b879cc73be95d0e5bdcd5c5bc2f2bc342a7319eb27cb6ffdd2ee6c25f4bb60e8`. Completed round 4364 supplies measured fees, stake, cuts and ceiling; capture-time ownership fractions and token price have their separate observation times. Retain all 100 pools in denominators. Indexed USD replayed as hypothetical USDC is a conversion assumption, not a payment observation.

October extraction SHA-256: `3e4a385ec19837f4b506b01989fac62cc33f99f28411bc1258f10c065e29240e`; PDF SHA-256: `b438da2b7d25d3043a3387b9db262293c2a0ec7801a765e5a3a249759b41569a`. Relevant extraction locators: honest work L81–84; MFS L123–150; scoring L198–213; claim/split L271–307; schedule/non-minting L388–416; share capture L462–470; appendix L646–670. Check hashes before using locators.

Label every input paper-stated, measured, illustrative or unresolved. Explicitly record which source quantities each synthetic fixture replaces. A constructed network is illustrative even when it uses measured scale. No new empirical dataset is required; historical fee series may contextualize the baseline but do not supply unmeasured capability demand, costs or routing. Do not average monthly fees into the matched round.

## 4. Network and actor definitions

### 4.1 Stable identities and three structures

Order the 100 source pools by completed-round stake descending, breaking ties by address. Keep those source keys stable; display anonymous modeled roles, not allegations about address owners. Synthetic ranks follow that stable ordering and their declared synthetic stake vector. Strategic actors are rank 1 (largest), rank 50 (middle) and rank 90 (lower), selected before outcomes. Report actual shares; rank is not a fixed ownership percentage.

| Structure | Stake vector | Initial outside-fee weights before actor override | Question isolated |
| --- | --- | --- | --- |
| R — measured distribution | Same-round measured stake shares | Same-round measured fee shares | Does the result survive the network-grounded reference distribution? |
| D — distributed mismatch | At rank `k`, stake share `(101-k)/5050` | Fee weight `k/5050` | How does broad misalignment of stake and paid business expose different participants? |
| C — concentrated mismatch | Rank 1: `.20`; ranks 2–10: `.04` each; ranks 11–100: `.44(101-k)/4095` | The same fee weights as D | What changes when stake concentration changes with the pre-override fee weights held fixed? |

All vectors are positive in D/C and sum to one. R retains zero-fee pools. D/C are stress fixtures, not measured populations or predictions. Record normalization with Decimal residual handling at one deterministically selected non-actor pool. Never drop pools to create a desired result.

### 4.2 Outside business and economic market scale

For each actor with stake share `s`, set its initial outside-fee share to `a=h s`, with `h=.25` (substantial reward headroom) or `.90` (near its stake limit). Preserve non-actor relative fee weights by multiplying their weights by `(1-a)/(1-original_actor_weight)`. Record the complete changed vector and differences from the parent. For each fixed actor/start/market, D versus C changes only the declared stake vector and the mechanically required fee reallocation; report those accompanying changes, not a pure causal stake effect.

Let `V0=.94 E0 P0`, where `P0` is EX-06's declared token valuation. Use two illustrative outside-fee totals: reward-leaning `F=V0/8`, and fee-leaning `F=V0/.5`. These ratios refer to the **scheduled node envelope's valued allowance**, not actual mint or an adopted emissions-to-fees target. They are selected stress controls; 8 is not a transfer of September's year-four rule. The measured round-4364 ratio is approximately 57.6, above both stress values; report its exact recomputed value separately and do not describe 8 as more reward-rich than that reference. The zero-setup full-retention fee-leaning profiles have zero optimum by the marginal-payoff identity; they are defense controls, not 18 independent discoveries.

For each below-cap, zero-setup profile report the critical ratio `Rcrit=L/[t(1-a)]`, where `R=.94 E P/F`, `a=f/F` and `t` is organizational reward retention. Positive infinitesimal spending pays only for `R>Rcrit`; equality gives zero first-order gain and no positive optimum because of concavity. This locates the regime boundary without adding scenarios. A capped actor or zero reward retention has no finite profitable ratio under the primary fixed-stake rule. Report the corresponding boundary under overrides where applicable; a setup charge requires separate break-even accounting.

The core is **3 structures × 2 market scales × 3 actor ranks × 2 outside-business starts = 36 profiles**. Changing only total fees tests economic scale; D/C and actor overrides test distribution. Do not call 36 profiles 36 observed networks.

### 4.3 Controls against a favorable starting configuration

- Replay the unmodified EX-06 baseline and original cases with their original costs, cuts, ownership, score, claim and valuation inputs. Keep these separate from standardized core comparisons.
- Six aligned controls: R stakes with fee shares exactly equal to stakes, each actor rank in each market. No artificial low-traffic override applies. They test the fixed-stake, no-headroom defense.
- Three unmodified measured-profile actor references at actual snapshot fee scale and native cuts/ownership proxies. No synthetic fee reallocation. Each uses the same one-round bounds `B=.10 F`, `Qmax=.25 F/p` at actual F and the same optimum/progression/all-pool outputs as the core. Their ownership application remains an assumption. Derive each native actor's reward headroom, including zero-fee or already-capped positions, from the matched source; do not impose the core's low/high-business override.
- Independent arithmetic fixtures include an above-cap actor, zero fees, and zero initial victim reward; undefined ratios must be displayed explicitly.

## 5. Choices, retained payoff and finite bounds

### 5.1 Standardized core and feasible action

Outside and controlled jobs use a divisible normalized job unit: price `p=1 USDC/job`, execution cost `c=.30 USDC/job`, setup zero. Baseline outside volumes are each pool's fees divided by price. Additional controlled work is real. The core strategic actor assumes full organizational fee/reward retention for a transparent upper-bound comparison; it is not inferred ownership. Honest non-actors keep their source pool's native fee/reward cuts and ownership proxy in every structure so organizational and external-delegator effects remain visible; applying those observations to synthetic roles is an assumption. Do not automatically lower costs when price changes.

For each evaluated state, non-actor service capacity equals its assigned outside jobs and is non-binding by construction. The actor's generic total capacity equals its assigned outside jobs plus the declared additional capacity Qmax; in a niche state, allocate that additional capacity to the niche offer rather than counting it twice. Recompute baseline outside capacity when stipulated demand/routing changes, while preserving the actor's additional Qmax. These capacity premises do not establish observed spare capacity or the feasibility of real expansion.

Each profile has a **one-round** incremental net cash-loss allowance `B=.10 F` and additional capacity `Qmax=.25 F/p` jobs per earning round. B is a net-loss allowance with immediate fee-side recovery, not a gross-invoice funding limit; intra-job advance liquidity and financing are unmodeled. Report gross invoices and recovered fees separately. Under the declared costs and retentions, budget binds before additional capacity; no capacity-limited optimum is claimed. Capacity is still checked for landmarks and diagnostics. Unconstrained opportunity is diagnostic; affordable opportunity must obey these bounds.

For organization reward retention `t`, node-side fee retention `z`, and added gross invoice fees `x=p q_self`:

```
leakage per invoiced USDC L = 1 - .5 z + c/p
cash delta = -L x
value delta = P .94 E t [min((f+x)/(F+x),s)-min(f/F,s)] - L x
```

Use explicit accounting for setup, useful-use value, scores and claims outside this simple core. Outside delegators' receipts are excluded from organizational payoff and separately reported. Net value includes received unsold tokens at stated valuation; it is not realized cash profit.

The stake-cap boundary for an initially below-cap actor is `xcap=(s F-f)/(1-s)`. A capped actor has zero reward headroom. Find the continuous one-period optimum on `[0, min(B/L, p Qmax)]`, including zero, the stake-cap kink and relevant stationary point. On the uncapped segment the candidate is `sqrt(P .94 E t (F-f)/L)-F`. Check all eligible endpoints; never report a sampled-grid maximum as the optimum. Once the cap binds, additional purchases lose cash without adding node reward.

Report the unconstrained one-round profit optimum, feasible one-round optimum, gross reward headroom, critical reward/fee ratio, nonzero break-even spending where it exists, budget/capacity reachability, and marginal versus accumulated return. A zero-return optimum is a required result. Use piecewise roots or bracketed verified roots where a closed form is inconvenient. Closed forms locate action points; every reported payoff is evaluated through EX-06's checked accounting function and independently cross-checked against the algebra.

### 5.2 Progression and impacts on honest participants

For each core profile report at most eight distinct spending points: zero; `.01 F`; `.10 F`; feasible optimum; feasible endpoint; stake-cap boundary; unconstrained optimum; and `x=F` as a harm-only diagnostic. Deduplicate ties. Infeasible points remain explicitly diagnostic and cannot establish affordable conduct. No profitability claim is attached to spending beyond the player's optimum merely because it harms others.

For every point compute all 100 pools. Give each honest pool its baseline and changed node reward, absolute token loss and percentage loss, unchanged outside-fee receipts, net-income effect, fee/stake-limited status and any crossed threshold. Aggregate honest-pool losses and outside delegator effects without hiding individual concentrations. A pool with zero initial reward has an undefined relative loss, not zero or infinity.

At fixed scores, a fee-limited victim's reward ratio is `F/(F+x)`. A stake-limited victim is unchanged until its diluted fee share falls below its stake share. For each victim with positive baseline reward weight `w_j=min(g_j/F,s_j)`, a target fractional loss `d` requires `x=g_j/[w_j(1-d)]-F`. Report the 5%, 10% and 20% landmarks and whether each is affordable, capacity-feasible, before the actor's optimum and before/after its cap. Feasibility uses inclusive endpoints (`<=`), Decimal precision and the verifier's documented numerical tolerance. All fee-limited victims share `x=F d/(1-d)`; the 20% landmark equals `p Qmax` and must be labelled "at the capacity boundary", even though it exceeds the core cash-loss allowance. These landmarks are illustrative reporting thresholds, not tolerable-harm policy. Also compute collective honest-reward loss landmarks through monotone piecewise accounting; individual percentages are not the aggregate percentage.

Record total fees, node claimability/actual mint, never-minted MFS allowance, pending claims, validator/treasury mint, buyback, burn and net supply. An actor's reward increase need not equal others' loss: previously unavailable allowance can become claimable.

## 6. Bounded supplementary comparisons

These do not multiply every core factor. Fix the named selection rules before outcomes.

| Comparison | Fixed selection | Bound and purpose |
| --- | --- | --- |
| Retention, costs, valuation and later schedule | All 9 structure/rank profiles at low business in the reward-leaning market | Four independent overrides: ownership `.25` with zero reward commission and all node fees allocated to delegators (therefore `t=z=.25`); cost `c=1.20`; claim valuation `.10 P0` with burn price unchanged; earning round `r=840` with outside fees unchanged and the original schedule base. Reoptimize each; no Cartesian product. |
| Appendix entitlement | R, each actor rank, low business, reward-leaning market | Compare baseline and feasible optimum under normalized fee-work reading at full scores, same budget/capacity. Reoptimize; record the absent stake cap. Zero-fee normalization stays undefined. |
| Capability identity | R, each rank, low business, reward-leaning market | Relabel added work as a sole-provider niche capability at matched price/cost/setup/capacity. Identical accounting is the expected control. Then one niche cost `.20` and setup `2 USDC` comparison for rank 1 only. Setup retains EX-06's absolute 2-USDC amount, is charged once iff x>0, is included in the cash-loss allowance, and is absent from the zero-action reference. No separate capability reward pool. |
| Outside demand responses | R, each rank, low business, reward-leaning market | One proportional doubling of outside fees/jobs; one addition of the same total outside spending to the highest-stake positive-fee non-actor only. Costs follow added jobs. Hold the actor's original budget and additional capacity Qmax fixed; update baseline outside capacity for assigned jobs. Show old action and reoptimized action, and recompute all denominators. No observed elasticity is claimed. |
| Price/routing response | R, rank 1, low business, reward-leaning market | Highest-stake positive-fee non-actor halves the price of all its generic jobs, including its existing outside jobs, and receives 25% of the actor's original outside jobs, assuming capability/region compatibility. Preserve outside jobs; execution cost unchanged; controlled offer unchanged. Show fixed action and reoptimization. Route is stipulated, not an equilibrium. |
| Short funding timelines | R, all three ranks, low business, reward-leaning market | Four earning rounds `r=0..3`: constant desired spending `.25 xopt` and ramp `.25,.50,.75,1 × xopt`, where `xopt` is the frozen r=0 feasible one-round optimum. Here B is a single initial stock shared across all four rounds, not replenished each round. Truncate each action to remaining net-loss budget, period capacity and nonnegative funds. No replenishment or sale of rewards. Follow each cohort through n+7 and final horizon 10; unsold receipts do not finance invoices. Repeat rank-1 ramp with claim delay 14 through horizon 17 as one collection control. |

Constant and ramp timelines are fixed illustrative schedules, not multi-round optima. Compare each with one-round deployment of the same initial B; concavity can make spreading a fixed stock more valuable than one-round spending. Also use a matched four-round no-purchase baseline with the same earning-round allowances to isolate the intervention. The one-round optimum is not the point where a repeated strategy rationally stops. Over r=0..3 the schedule changes by less than 0.3%, so these timelines test pacing, funding and collection; the r=840 override tests schedule decline. Optimal multi-round budget allocation, replenishment and reinvestment remain outside this finite study.

The supplement is at most 36 one-factor profiles, 3 appendix comparisons, 4 capability comparisons, 6 demand responses, 1 price response and 7 timelines. Useful-internal paired rows are references, not new optimizer dimensions. Do not add combinations to chase an expected sign. Bounds can be changed only by an explicit amendment before dependent outcomes, with the reason retained.

## 7. Evidence interpretation and conclusions

M2.2 maps the tested economic choices onto existing EX-07 claim distinctions and reports what public payment/execution observations and useful-case disclosure would establish on those existing premises. The reused results apply only to EX-07's packeted comparisons and stipulated accurate disclosure of control/funding at n+1. Undisclosed common control, generic full-price work at these volumes and other unpacketed claims are marked "not examined", with their E2/control-evidence dependency, and inherit no EX-07 verdict. No new evidence source, source arrival, false-cut rate or score-to-median response is assumed. A hypothetical score zero may appear only as an algebraic boundary with useful-work cost, never as an observed defense. Creating new packets would require a separate tolerance-first evidence brief; it is outside this defined workload.

M2.3 must distinguish arithmetic identities, conditional model results, scenario-ground-truth premises and empirical unknowns. For each consequential conclusion state which networks support it, which weaken/reject it, who benefits and pays, which defense works, and which practical dependency could change it. Preserve original findings under their source-scoped conditions; explicitly qualify any broader claim that additional conditions contradict.

The intended result is a listening-friendly account for each stake position: starting opportunity, affordable one-round profitable progression and stopping point, honest-party losses, bounded response and fixed-stock pacing. Explain which limits bind and which are only checked; do not present the fixed timelines as multi-round optimal strategies. Classify remaining matters as specification, evidence, incentive analysis or policy. M3 receives unresolved concerns and retained strengths, not a chosen expansion. Full M2 completion, observed dishonesty and owner acceptance do not follow from completing this study.

## 8. Required artifacts and acceptance

Planned experiment folder: `experiments/m2/strategic-self-funding/`, with README, machine-readable manifest/network definitions, a finite scenario schema, Decimal build/optimization code and an independent verifier. Committed `networks.json` holds construction rules plus SHA-256 hashes of each deterministically generated 100-pool input vector; freeze the serialization/precision convention in M2.1 and recheck hashes before accounting. Generated vector files remain ignored, along with profile/strategy summaries, spending progressions, all-pool effects, loss landmarks, sensitivity/response comparisons, cohort timelines and concise Markdown accounting. Every row identifies parent, structure, actor, source, override, units, horizon and feasibility.

Reserve experiment/record IDs from the actual registry during M2.1; EX-08 is a possible next ID, not a reservation. Use workbench M2.1 register rows, M2.2 findings and M2.3 dispositions, following the three sequential gates in the implementation spec. Prepare a new source-scoped listening guide; never overwrite historical guides.

Acceptance requires original-case reproduction, independently hand-checked optimum and dilution fixtures, all-pool conservation, feasibility and cash-ledger checks, correct cap/zero/undefined cases, aligned-network defense, identical matched capability/use accounting, correct schedule and cohort claims, and a clean-checkout rebuild. Verifiers check recorded evidence scope and provenance; they do not establish hidden purpose or practical reviewer performance.

Stop once the finite questions have conditional signs and boundaries. Any need for new behavioral rules, empirical control identification, a large simulation or a successor mechanism is reported as a dependency rather than silently implemented.
