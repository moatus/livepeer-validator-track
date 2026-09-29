# M1.1 baseline accounting workbook

Version: **v0.3 · 2026-09-26**. Status: **Draft, not reviewed**. Automated QA is reported below; human milestone review and acceptance are pending. This workbook supports workbench step M1.1; it is not an accepted economic rule or an empirical finding.

## Source and scope

Primary source: Doug Petkanics, *Livepeer 2.0 Litepaper* (Sept 2026), the snapshot in this repository at [`docs/litepaper-2.0.md`](../../../docs/litepaper-2.0.md). SHA-256: `5fc153408fb636d9750788ae987ada6daaa9fc3df3e44f70cadde51a6158fb71`. The workbook's **Source & decisions** sheet gives headings and line references to that snapshot. Source provisions, accounting interpretations and research hypotheses are distinguished explicitly.

The modeled identity is a **reconstruction** from **Node operators: permissionless entry, rewards capped by stake (MFS)**, lines 51–63; **The top nodes by stake can register as validators**, lines 79–90; and **Appendix → Accounting Identities / Parameters**, lines 207–233:

`node LPT entitlement = entered LPT emission envelope × node emission share × min(node fees / network fees, node stake / network stake) × honesty multiplier`

There is no normalization of MFS shares. The node emission envelope left unassigned by MFS and the separate amount withheld by scores are shown separately, with **no assumed redistribution**. The paper does not specify their final mint, burn, or rollover treatment. If network fees or network stake are zero, MFS and node reward outputs are `undefined/needs rule`. An individual zero-stake operator still gets its ordinary fee share when network stake is positive. The multiplier is about **dishonesty**, not an uptime grade. Validator voting and validator/treasury distribution are not modeled.

The entered LPT budget is an **authorized/entered emission envelope**, not an established amount actually minted. Holding it fixed isolates the litepaper's allocation arithmetic; it is not a recommendation to adopt a fixed-budget emissions policy. The litepaper explicitly leaves emissions choices open (**Emissions schedule**, lines 128–140); this M1.1 sheet does not implement the draft 32× fee-linked rule. The starting 50/50 USDC fee split and 94/1/5 LPT emission envelopes are editable proposals from **The node/network split**, lines 117–121, and Appendix lines 226–233. The 50% network fee funds a separate purchase and 100% burn of purchased LPT. An explicitly illustrative USDC/LPT price converts that funding into a displayed burn quantity. LPT and USDC are never added or treated as equivalent. The burn result is not a forecast of execution.

## Reproduce and use

`build.py` generates the workbook from `docs/litepaper-2.0.md`, and `verify.py` checks it. The build writes `experiments/m1/baseline-accounting/litepaper-baseline-accounting.xlsx`; the generated file is not committed, so build it before verifying or opening it.

Requires Python 3.10+ and `xlsxwriter==3.2.9`; verification also uses `openpyxl==3.1.5`. No system software installation is needed. From the repository root, with `uv` available:

```bash
uv run --no-project --with xlsxwriter==3.2.9 python3 experiments/m1/baseline-accounting/build.py
uv run --no-project --with xlsxwriter==3.2.9 --with openpyxl==3.1.5 python3 experiments/m1/baseline-accounting/verify.py
uv run --no-project --with xlsxwriter==3.2.9 --with openpyxl==3.1.5 python3 experiments/m1/baseline-accounting/recalculate.py
```

The third command is an **optional spreadsheet recalculation regression check** and requires LibreOffice on `PATH`; the workbook and normal generator do not. It edits copies in an isolated temporary directory, uses a timeout, and leaves the generated workbook unchanged. The build refuses a changed source SHA so citations can be reviewed first. Open `experiments/m1/baseline-accounting/litepaper-baseline-accounting.xlsx` in a spreadsheet application. Blue cells on **Inputs**, **One-variable** and **Pass-through margin** are editable. Invalid types, missing values, negative amounts and out-of-range shares display `check inputs`; valid zero network denominators display `undefined/needs rule`. A zero fee cut or retention with positive pass-through costs displays `no finite break-even`. The saved file includes formula caches for the default case and requests recalculation on open; `openpyxl` itself does not recalculate edited formulas.

**v0.2 automated QA:** seven independent arithmetic fixtures, 222 saved formulas with nonempty caches, default accounting and 14 sensitivity rows, and 25 LibreOffice recalculation cases passed. The recalculation cases cover text, blank, negative and formula-error inputs; invalid fee/emission shares and scores; invalid sensitivity and pass-through inputs; zero fee retention/cut; and valid zero network denominators. This automated result is **not human review or milestone acceptance**.

**v0.3 scope revision:** wording is confined to the litepaper baseline and its unresolved questions. The fixed input budget is an analytical control, not a proposed replacement rule. Accounting formulas and scenarios are unchanged.

**2026-09-29 source path:** `build.py` reads the litepaper from `docs/litepaper-2.0.md` (same SHA-256) and writes the workbook beside the scripts. Formulas, inputs and results are unchanged.

## Default one-round example

With a 1,000 LPT **entered emission envelope**, 94% node envelope, 50/50 USDC fee split, 2 USDC/LPT illustrative buyback price, and fully eligible scores:

| Item | Node A | Node B | Total |
| --- | ---: | ---: | ---: |
| Gross customer fees (USDC) | 600 | 400 | 1,000 |
| Node-side receipt **before** delegator fee sharing (USDC) | 300 | 200 | 500 |
| Operator retained fee (USDC), with 80% illustrative retention | 240 | 160 | 400 |
| Delegator fee share (USDC) | 60 | 40 | 100 |
| Operator fee net after illustrative costs (USDC) | 60 | 30 | 90 |
| Fee share / stake share / MFS | 60% / 60% / 60% | 40% / 40% / 40% | 100% MFS |
| Modeled node entitlement (LPT) | 564 | 376 | 940 |
| Operator share (LPT), with 30% illustrative reward cut | 169.2 | 112.8 | 282 |
| Delegator share (LPT) | 394.8 | 263.2 | 658 |

Separately, 500 USDC funds BME; at the illustrative 2 USDC/LPT, it purchases and burns 250 LPT. The validator and treasury emission envelopes are 10 and 50 LPT, respectively; actual minting, validator distribution and treasury spending are outside this model. MFS-unallocated and score-withheld node amounts are both zero in the aligned default.

Hand-checkable independent fixtures in `verify.py` include aligned shares; 90/10 fees against 10/90 stake (only 20% of node budget MFS-eligible, 188 LPT modeled entitlement, 752 LPT MFS gap); A's 0.5 score (282 LPT withheld); a zero-stake A with 600 USDC gross fees (300 USDC node-side receipt, zero A MFS reward); and zero network fee or stake totals (undefined reward). Saved formula caches, source-linked formula structure, and both sensitivity tables are checked. In the fee sensitivity, A=1,000 USDC makes total fees 1,400 USDC, so A's fee share is 5/7 rather than 100%; the entered envelope remains 1,000 LPT. In the stake sensitivity, changing A stake recomputes total stake with B fixed.

The **Pass-through margin** sheet gives an illustrative outsider's one-job cash case: at a 1 USDC customer price, 0.4 USDC upstream API cost, 0.02 USDC other cost, 50% node cut and **80% assumed operator fee retention**, the operator receives 0.4 USDC and loses 0.02 USDC per job. Break-even customer price is 1.05 USDC. An undelegated fee-only operator may set 100% retention; this example does not imply mandatory fee sharing for a zero-stake seller. It is a conditional margin calculation, not observed market access or an adoption forecast.

## Limits and decisions

Payment, execution, correctness/quality, availability, independent demand, and economic value are separate claims. This workbook measures none of the latter four. Nondeterministic work may require evidence and judgment that a spreadsheet cannot supply. The litepaper permits no-bond sales and uncapped ordinary fees; it limits **inflation**, not sales. It specifies reward reduction and delayed access to delegated stake, **not principal slashing**; no principal loss is modeled. Operator costs are illustrative and exclude fixed costs, delegator costs, taxes, buyback slippage, LPT sale liquidity, validator costs and appeals. It makes no claim about empirical adoption or observed exclusion.

Before protocol use, governance or implementation must settle the emissions rule, measurement windows and eligible-fee denominators, zero-denominator behavior, disposition of MFS and score gaps, validator evidence and dispute criteria, and buyback execution. This M1.1 accounting aid identifies those missing decisions; it does not resolve them or propose replacement mechanisms.
