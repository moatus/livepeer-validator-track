# EX-05: October Slice 1 reconciliation

Status: **Reviewed by the owner, 2026-10-14; technical checks passed.** This bounded rerun asks whether an additional real, self-funded job can increase retained operator receipts under October's scheduled emissions. It also checks whether proportional fee compression leaves mint unchanged while reducing burn. It prepares the accounting boundary for Slice 2; it does not model capability entry, demand, price competition or equilibrium.

## Sources and rule interpretations

The [October PDF and page-labelled extraction](../../../docs/sources/README.md) replace September as the active paper. The calculation pins extraction SHA-256 `3e4a385ec19837f4b506b01989fac62cc33f99f28411bc1258f10c065e29240e`. Source locators: MFS, PDF p3 / L123–150; scores, p4 / L198–213; 50/50 fee split, p6 / L298–307; scheduled emissions, p7 / L388–395; unused node allowances never minted and validator/treasury minted in full, p8 / L413–416; 94/1/5 allocation, p13 / L646–670.

**Explicit base reading:** scheduled LPT ceiling; non-normalized MFS node allocation; full scores; unused node allowance never minted; separate validator and treasury allocations minted in full. This follows the emissions prose and main-text/appendix MFS formula. It does not resolve the PDF's conflicting statements: the p7 diagram still describes fee-ratio emissions and a $50M ceiling; p13 describes node distribution proportionally to work and score. Schedule governance also remains open in p9's prose while p13's appendix says ratchet-only. There is no fee-linked mint rule or USD ceiling in this base run. Alternative interpretations require an explicit new case, not silent switching.

October's launch formula is `EmissionBase × 2^(-r / 840)`. Here `r=0` is an **illustrative calibration**, not a launch date: EmissionBase is set equal to the captured current-system round 4364 ceiling, **29,288.551807 LPT**. The ceiling is held fixed within this single-round comparison. No schedule extrapolation or claim about a chosen launch snapshot follows.

## Inputs and their status

The shared [network snapshot reader](../network-snapshot/read_snapshot.py) loads `livepeer-arbitrum-2026-10-09-v1`, content SHA-256 `b879cc73be95d0e5bdcd5c5bc2f2bc342a7319eb27cb6ffdd2ee6c25f4bb60e8`. It verifies source integrity and supplies the completed round **4364**. All **100 pools**, their same-round stakes, fees and cuts are included; sums must exhaust the network denominators or the build fails. Ranking in the small table is by that round's stake.

- **Measured:** redeemed ETH fees, round stake and commissions, current-system mint ceiling, and separately timed capture-price and operator-address stake observations. Twenty-seven pools received fees in this round. These are today's system, not an October deployment.
- **Conversion assumption:** distribute the round's indexed **$820.960664** fee valuation across pools using their same-round ETH fee shares, and treat those dollars as gross hypothetical USDC invoices at USD≈USDC. This preserves observed fee shares; it is not an actual USDC payment history.
- **Ownership assumption:** hold the capture-time `operator_address_fraction_of_own_pool` fixed for round 4364. It is measured later than the round boundary and is only that address's fraction, not identified organization-wide ownership. Other-address stake is not proven independent.
- **Behavior assumptions:** full validator scores; no changes in stake, cuts, LPT price or other pools' behavior; one added real job priced at **1 USDC**, with separately specified **0.30 USDC/job** execution cost. Neither price nor cost is measured. Cost remains unchanged when the invoice price changes.
- **Valuation assumption:** added retained LPT valued at the snapshot price **$1.71765/LPT**, also used for idealized buyback. No claim-price forecast, slippage, time discount, transaction cost or tax is included. Seven-round claim delay remains a timing/evidence provision, not an automatic detection result.

## Method

For every pool, `reward = ceiling × 0.94 × min(pool fees / network fees, pool stake / network stake)` at score 1. There is no renormalization of eligible MFS shares. Total modeled mint is the sum of node rewards plus `ceiling × (0.01 + 0.05)`. Unused node allocation is never minted. The 50% network fee is burned after a frictionless purchase at the declared LPT price.

**Claim horizon convention:** every eligible node claims its round-n entitlement at n+7, with its score still 1. The tables' `node_minted_lpt` and `total_minted_lpt` are eventual issuance attributed to round n under that full-claim assumption, not issuance immediately observed in round n. The validator/treasury 6% is the round's separate allocation; summing it with delayed node claims is cohort accounting, not a claim that all tokens mint at the same time. Pending or never-claimed entitlements are not modeled here and must be separated from permanently unminted MFS allowance in Slice 2.

Let `w` be operator-address stake fraction, `c` reward commission, and `d` fee fraction paid to delegators. Retained fractions are `c + (1-c)w` of node rewards and `1-d+dw` of node-side fees. Remaining receipts are explicitly assigned to other addresses. Validator distribution is outside this test; its allocation is unchanged and cannot affect the one-job delta under fixed stake and scores.

Compare, in order: cooperative outside-customer job; ordinary proportional price compression; self-funded job alongside a legitimate internal-use job. The same paid execution produces identical fee and reward accounting for both motivations. Internal utility is excluded because it is unmeasured. For the self-funded job, incremental retained return, valued in USDC, is:

`added retained fee − gross payment − jobs × execution cost/job + added retained LPT × stated price`.

The generated CSV separates added fee receipts, payment outlay, execution costs, cash-only change, added LPT and its valuation. Valued returns include unsold claim-delayed LPT; they are not realized cash. The internal payment cancels only to the extent recovered by the operator address; the network half and other-address fees remain external outflows. Unknown costs of existing service are not inferred: reported deltas concern only the added job. Baseline tables report gross receipts and entitlements, not profit.

The top-ten rows are **ten independent $1 interventions**, each with the other 99 pools fixed. They compare one job with no added job; they are not optimal spending choices, simultaneous responses, a repeated game or an equilibrium. Never sum the rows as one network scenario. Full-population CSVs preserve reward dilution to the other pools.

## Results

| Modeled quantity | Round 4364 baseline | All gross prices halved |
| --- | ---: | ---: |
| Gross fees, USDC | 820.960664 | 410.480332 |
| MFS share of node allowance | 19.002220% | 19.002220% |
| Node mint, LPT | 5,231.546420 | 5,231.546420 |
| Validator mint, LPT | 292.885518 | 292.885518 |
| Treasury mint, LPT | 1,464.427590 | 1,464.427590 |
| Total mint, LPT | 6,988.859528 | 6,988.859528 |
| Node allowance never minted, LPT | 22,299.692279 | 22,299.692279 |
| Burn funding, USDC | 410.480332 | 205.240166 |
| Idealized burn, LPT | 238.977866 | 119.488933 |

This is counterevidence to treating the whole scheduled allowance as distributed: MFS substantially reduces realized node issuance on these inputs. Yet **9 of the 10** independent $1 self-funded comparisons have positive incremental retained return valued in USDC at the stated $0.30 execution cost, from approximately **$0.51 to $28.04**; the sixth-ranked pool loses approximately **$0.84**. All ten outside-customer comparisons are positive at these inputs. Higher execution costs or lower realized LPT prices can reverse those results. The generated table reports the per-row break-even execution cost, including a negative threshold for the pool already capped by stake.

These are operator-address receipts, not established private profit. In particular, the snapshot documents a community/grants role for the third-ranked address; its modeled retained receipts must not be described as personal gain or misconduct. ENS names, wallet links and stake provenance do not establish current common control.

**Compression conclusion:** at unchanged fee shares, stake, scores and LPT price, halving prices leaves mint unchanged and halves burn. This is an identity under those conditions, not evidence that competition will halve prices or preserve traffic. Actual price competition may shift fee shares, job volume and costs; those responses belong in Slice 2. Being the only provider of a capability creates no capability-specific reward pool under network-wide MFS.

## Historical transfer and limits

[EX-03](../self-funded-return/README.md) and [EX-01](../../m1/baseline-accounting/README.md) continue to load the exact September source; their arithmetic is unchanged. EX-03's fee-linked C1 pool-growth result is historical under October's fixed schedule. The distinction between pool size and share competition transfers; the September full-ownership assumption does not substitute for measured-address-plus-commission accounting. October expressly settles the non-minting of unused MFS allowances, which September left open.

[EX-04's evidence tabletop](../evidence-self-funded/README.md) remains historical. Real payment and execution still do not by themselves establish independent demand, worthwhile internal use or a violated rule. Its specific verdicts do not automatically transfer to a new constitution or score standard. Full scores here are an assumption, not a conclusion that validators must approve these jobs.

No capability prices, compute costs, customer routing or elasticity, service quality, private utility, beneficial ownership, validator performance or abuse prevalence were measured. The recorded current-system reward totals are not relabelled as October rewards. This one-round reconciliation does not test emissions decay, delegation movement, coordinated responses, liquidity or score changes. Slice 2 must use this same snapshot and extend the declared accounting with separate price, volume and cost inputs, demand/routing assumptions, legitimate lookalikes and system-wide outcome tables.

## Reproduce and hand-check

Python 3 standard library only; run from the repository root:

```bash
python3 experiments/m2/october-reconciliation/build.py
python3 experiments/m2/october-reconciliation/verify.py
```

`build.py` writes ignored `generated/results.md`, `baseline-pools.csv`, `network-cases.csv` and `top-ten-standalone.csv`; no live queries or external local paths are needed. The README table above is a reviewable summary of those outputs. The source extraction script has its own pinned Poppler requirement; ordinary model reproduction uses the already archived extraction.

`verify.py` checks two hand-computed states: with 100 USDC fees split 10/90, equal stake and a 1,000 LPT ceiling, MFS sums to 0.6, node mint is 564, total mint 624, and 376 LPT is unminted. Adding 10 USDC to the first pool gives it `940 × 20/110 = 170.909091 LPT`; the second retains 470 LPT. With 20% commission, 25% own stake, 60% delegator fee share, 2 USD/LPT and a separate 3 USDC job cost, the first operator's self-funded incremental retained return is **51.277273 USDC**. The outside-customer comparison is exactly 10 USDC higher. The checker also verifies full-population denominators, fee/reward conservation, non-minting and compression invariance.
