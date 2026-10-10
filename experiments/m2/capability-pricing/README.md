# EX-06: connected capability, price and network reward comparison

Under October's scheduled ceiling and network-wide fee share, when do ordinary competition, capability entry and real self-funded jobs change participant receipts, net cash, burn and issuance? This finite ledger connects those choices on one measured network scale. The paper's intended contribution is real, honest work during bootstrapping (October L81–84); the accounting imposes no independent-customer or use-value eligibility criterion. A reward-objective definition remains VD-19.

Addresses are used only to take measured round-4364 fee and stake shares. The roles in the scenarios are synthetic. Nothing here describes what any address owner did or intends; address stake is a proxy and no beneficial owner is identified.

## Sources and input status

- **October authority:** [extraction](../../../docs/litepaper-2.0.md), SHA-256 `3e4a385ec19837f4b506b01989fac62cc33f99f28411bc1258f10c065e29240e`; [PDF](../../../docs/sources/litepaper-2026-10.pdf), SHA-256 `b438da2b7d25d3043a3387b9db262293c2a0ec7801a765e5a3a249759b41569a`. MFS L123–150; dishonesty multiplier L203–208; claims L271–278; fee split L298–307; schedule/non-minting L388–416; share-capture discussion L467–470; appendix L646–670.
- **Measured scale:** [snapshot reader](../network-snapshot/read_snapshot.py), `livepeer-arbitrum-2026-10-09-v1`, content SHA-256 `b879cc73be95d0e5bdcd5c5bc2f2bc342a7319eb27cb6ffdd2ee6c25f4bb60e8`. Raw redeemed ETH, completed round 4364, UTC 2026-10-08 13:13:02 through 2026-10-09 10:33:55 exclusive; all 100 pools. No 30-day averaging. Indexed USD fees are 820.960664; the measured ceiling is 29,288.551807 LPT (display-rounded).
- **Frozen configuration:** [inputs.json](inputs.json), SHA-256 `bf518c99987c042821438b4ceea3689aae2122dd7956032b7a1efe2b03b8524f`; [scenarios.json](scenarios.json), SHA-256 `7bf3f949d45570387674efe08f29f4ef47b8f7a7121f2ad9f606147d40a81aa5`. Each input retains its status, units and locator. The adapter handles this hash-pinned natural-language grid; a changed grid requires an explicit adapter review.
- **Reader interface:** `read_snapshot.py` source SHA-256 `56fbc40ddfd61a424c1cfe5e34e7a8418ff9146d3cc79f4b8ba8f00286373777`; identity/content validation and matched-round access are checked before accounting.
- **EX-05 dependency:** explicitly import [build.py](../october-reconciliation/build.py), SHA-256 `1b5f472cf255104bb4b1216cb48c947502f010023dc8bddc92752a9a3ac3c695`. Check `inputs()` fee/stake/ownership mapping and `retention()` against equivalent Decimal formulas; independently compare baseline accounting with `account()`. No generated table is an input. Zero fees, scores and claims use the separate EX-06 function.

**Measured inputs** are same-round stake, fees and cuts, plus later capture-time address fractions and LPT price. **Illustrative application:** replay indexed USD 1:1 as hypothetical USDC; apply those fractions backward as organization ownership proxies. A starts below its stake cap (fee share 3.073045%, stake 14.639488%); B above (6.384073%, 1.178598%). Selection uses stake rank within those positions, never modeled returns. The documented grants/community pool remains in totals.

**Illustrative service inputs:** divisible normalized completed-job equivalents; baseline generic outside volume equals each pool's replayed fees / 1 USDC. Generic price 1, independent cost 0.30 USDC/job, zero setup, capacity 1,000/pool. A discount is 0.5; routing moves 25% of B's baseline volume under stipulated visibility and matching capability/region. A alone adds niche price 1, cost 0.20, setup 2 USDC once, capacity 20, volume 10. Controlled additions are 10 jobs, invoice budget 20; useful internal value is 1 USDC-equivalent/job, no-credited-use value zero. Costs never follow price.

**Paper-proposed rules and declared readings:** 94/1/5 emissions shares, 50/50 fee split and full burn. Calibrate hypothetical EmissionBase at r=0 to the measured round ceiling under `E(r)=EmissionBase×2^(−r/840)`; keep that cohort fixed through all horizons. Main-text MFS, full median 1 and all claims at n+7 are the baseline. No selected validator/treasury receipt is invented. Validator distribution, score-withheld finality, ownership, reward policy and live capability demand remain unresolved.

## Method and ledger

Instantiate each parent independently; parent links are comparisons, not cumulative history. With pool invoice fees `f_i=Σ p(q_out+q_self)`, full network `F=Σ f_i` and stake share `s_i`, pre-score node entitlement is `R_i=.94E min(f_i/F,s_i)`. Apply the current median once, then separate claimable, minted and pending. At zero fees the explicit MFS boundary sets fee shares zero. The single matched appendix control reads work as fee share and normalizes those weights at full scores, without a stake cap; zero normalization is undefined.

For reward cut `k`, delegator fee fraction `d` and owned fraction `w`, organization retention is `k+(1−k)w` of minted node LPT and `1−d+dw` of node-side fees. Commission, owned delegator and outside delegator receipts are separate. Net cash deducts controlled invoice outflow, execution and setup once from retained fees; the recovered internal receipt cancels only its own portion. The network half and outside owners' portion remain leakage. Net value adds received unsold LPT at explicit valuation plus declared internal use. Pending LPT and its value remain separate, excluded from collected income. Absolute net cash uses illustrative costs and is not observed profit.

Every row reconciles `E = node minted + MFS-unused + score-withheld + pending + full validator mint + full treasury mint`. Pending never expires in this control; score-withheld non-minting is a declared interpretation. Burn is fees/2 divided by 1.71765 USDC/LPT; total actual mint minus burn gives net supply change. Timing is cohort attribution, not simultaneous minting.

## Results

All numbers below are illustrative results using the stated inputs. Net value includes unsold received LPT at 1.71765 USDC/LPT; cash already deducts controlled payments and execution/setup. Useful/no-use pairs have identical fee/reward ledgers and differ only in the credited 10-USDC internal value.

| Case | Comparison | Actor cash delta USDC | Received LPT delta | Net value delta USDC-equivalent |
| --- | --- | ---: | ---: | ---: |
| S00 cooperative outside service | self reference | 0 | 0 | 0 |
| S01 A discount, fixed demand | S00 | −3.090942 | −16.713019 | −31.798059 |
| S02 discount with rerouting | S01 | −2.325492 | 9.169343 | 13.424231 |
| S03 uniform half prices | S00 | −3.090942 | 0 | −3.090942 |
| S04 outside useful niche | decline S00 | −1.549642 | 12.888746 | 20.588712 |
| S05 useful internal niche | decline S00 | −11.549642 | 12.888746 | 20.588712 |
| S06 no-credited-use niche | decline S00 | −11.549642 | 12.888746 | 10.588712 |
| S07 useful internal discount | decline S02 | −6.774821 | 6.684149 | 14.706208 |
| S08 no-credited-use discount | decline S02 | −6.774821 | 6.684149 | 4.706208 |
| S09 B outside addition | decline S00 | 1.750190 | 0 | 1.750190 |
| S10 B controlled addition | decline S00 | −8.249810 | 0 | −8.249810 |
| S11 B matches price once | no-response S08, A consequence | 2.325492 | −8.370155 | −12.051506 |

Against undiscounted S00, A remains below baseline at every discount state (S02 −18.373828; S08 −13.667620; S07 −3.667620); the positive deltas are against the matched discounted reference only.

S06 versus parent S05 and S08 versus parent S07 each lose exactly the declared 10 use-value units. Those paired differences are distinct from the added-job returns against decline shown above. S11 restores baseline outside A/B quantities at tied prices and retains A's controlled jobs; it reports one response consequence, not a fresh added-job return. S11 is compared against its parent S08; the column named decline here means the parent, and the sign flips below an LPT valuation of 0.2778 USDC/LPT.

Baseline node mint is 5,231.546420 LPT; MFS-unused is 22,299.692279; validator/treasury mint totals 1,757.313108. Uniform compression leaves those unchanged and halves burn from 238.977866 to 119.488933 LPT. Adding A niche work increases node mint by 285.356247 LPT while reducing other-98 mint by 35.780390. A discounted additions increase node mint by 147.676103, reducing other-98 mint by 18.866496. B's capped addition leaves B reward unchanged, reduces total node mint by 45.961947 and other-98 mint by 35.780390. Thus a fixed ceiling does not fix actual issuance or every recipient's share.

| Independent sensitivity | Conditional sign and boundary |
| --- | --- |
| Price 0.25 / 0.5 / 1 at fixed routing | S08 against symmetrically priced S02: +1.010877 / +4.706208 / +11.224178. All three positive; lower price does not increase reward here. At price zero the added jobs have cost but no fees; once both states reach the stake cap, reward gain is zero and controlled fee leakage remains. |
| Cost 0.10 / 0.30 / 0.70 | +6.706208 / +4.706208 / +0.706208. No sign switch in the grid; exact linear root 0.770621 USDC/job, with other assumptions fixed. |
| Whole-round median 1 / 0 | Useful S07: +14.706208 / −42.141813; no-use S08: +4.706208 / −52.141813. Median roots 0.741307 / 0.917214 against original full-score S02. A cut needs separate authority/evidence; useful work is exposed too. |
| Ownership proxy / 1, cuts fixed | +4.706208 / +280.561896; no sign switch. Full ownership removes outside-owner leakage but leaves the network half and execution costs. It identifies no actual owner. |
| Valuation 0.01 / 1.71765, burn price fixed | −6.707980 / +4.706208; root 1.013565 USDC/LPT. Token quantities and burn do not change. |
| A claims n+7 / n+14 / no claim | Full claim +4.706208; delayed at n+7 −52.141813, with 824.631411 pending node LPT; at n+14 returns to +4.706208. No claim remains negative at both horizons; pending is not permanently unminted. |
| Matched S10/S00 entitlement | Main MFS −8.249810; normalized fee-work appendix +125.243999. Appendix node envelope distributes fully and removes the tested stake-cap defense. Work definition and reconciliation remain VD-06. |
| Zero fees at fixed executed jobs | Node reward/burn zero, validator/treasury mint retained, execution cost retained. A's net value falls 64.506270 from S00. Appendix undefined; no guessed reward. |
| Matched-fee redistribution versus S03 | Moving 10% of B's original jobs to A at uniform 0.5 prices holds fees/burn fixed; node mint rises 175.761449 and A net value +11.186357. Other-98 mint unchanged. Equal total fees alone do not preserve MFS. |

Valuation break-even is `−(Δcash+Δuse)/ΔreceivedLPT`; direction follows the token delta. Token and cash/use deltas within 1e-18 of zero yield “undefined” for a tied comparison; a zero token delta alone yields “no finite threshold”. A root at or below zero is reported as “none (root ≤ 0)” and means the sign does not depend on that quantity within its feasible range. Added-job cost root is `(Δvalue+Δexecution cost)/added controlled jobs` for matched price/job states. Whole-round median root compares the intervention's entire retained pre-score reward with the original reference; a tied comparison is undefined, and roots above 1 are reported as “none (root > 1)” because a valid median cannot reach them. Zero potential reward is tested with the same 1e-18 tolerance. Under MFS, gross fees to the cap are `max(0,s×otherFees/(1−s)−ownFees)`: A S08 has 110.056834 USDC headroom; B S10 has zero. At zero network fees, cap headroom is undefined. A's remaining controlled invoice budget is only 15 USDC, so additional purchases cannot reach that cap in this state. The both-capped price boundary is algebraic and outside the frozen price grid; capacity and budget still constrain feasibility. These roots locate conditions without adding scenarios or sweep dimensions.

## Limits and reproduction

Positive returns, common ownership, low prices and unique capabilities establish no misconduct. Declared absence of use value establishes no intent or rule violation. Execution and payment are distinct from independent demand and economic value. No observed discovery, routing elasticity, new-address access, reviewer accuracy, market frequency or future outcome is inferred. Niche entry is at an existing pool; broader access, delegation movement and LPT-price feedback remain separate studies. September EX-03/EX-04 are historical. Claim finality, score evidence and reward objectives require their named specification/policy/evidence work. No liquidity, slippage, token-price response, taxes, financing, expiry or compounding is computed; zero transaction costs are analytical controls.

From the repository root, Python 3 standard library only:

```bash
python3 experiments/m2/capability-pricing/build.py && python3 experiments/m2/capability-pricing/verify.py
```

Generated `scenarios.csv`, `sensitivities.csv` and `accounting.md` live in `generated/`. CSVs preserve full-precision Decimal results, all required quantities, every selected receipt, other-98 aggregates, parent/decline deltas, complete sensitivity reference states and provenance. Tables above round for display only. The verifier uses independent hand constants, then checks every full-population ledger, sibling-interface agreement and all nine groups. No live query is needed to reproduce.
