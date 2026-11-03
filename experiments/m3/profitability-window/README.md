# Where self-funded work can increase retained rewards

Exploratory analysis under proposed rules, not an accepted M2 finding, forecast, live prevalence estimate or allegation of misconduct.

The study extends the accepted [October reconciliation model](../../m2/october-reconciliation/README.md) across 100 pools in the frozen network snapshot. Under the declared hypothetical October rules, 79 pools representing 88.17% of stake have some positive modeled opportunity; 78 profit from the particular $1 purchase and 60 have an unconstrained maximum gain above $10. These are different measures.

## Assumptions and limitations

Main-text non-normalized MFS; illustrative launch ceiling calibrated from observed round 4364 issuance; 94% node allowance; 50% node fee share; $1 invoices with $0.30 execution cost; LPT at $1.71765; full unchanged scores; address-owned stake proxies, not beneficial ownership. Each pool acts alone with the other 99 fixed. Fractional work is allowed, with no setup, funding or capacity limit and no financing, price-impact, claim-discount or opportunity cost. Sixty-seven of the 79 pools had no redeemed fees in that single round; uneven settlements limit interpretation. Proposed rules are not today's deployed economics. Profitable self-use does not establish dishonesty; a capped actor may already have filled headroom through prior activity.

## Files and reproduction

- [All-pool results](results.json), [per-pool table](pools.csv), [interactive view](window.html), [calculation](analyze.py).
- [Growth scenarios](growth/scenarios.csv), [growth calculation](growth/analyze_growth.py).
- [Lever results](levers/results.json), [lever calculation](levers/analyze_levers.py).

From the repository root, using Python 3 standard library:

```sh
python3 experiments/m2/october-reconciliation/build.py
python3 experiments/m3/profitability-window/analyze.py
python3 experiments/m3/profitability-window/growth/analyze_growth.py
python3 experiments/m3/profitability-window/levers/analyze_levers.py
```

These regenerate local result files. The M2 command generates the reference CSV used for ten-pool reconciliation; it does not change the M2 model. The all-pool calculation checks 200 payoffs against that engine. Other scripts retain their original assertions. Only the study code and result assets were imported, not M2 orchestration logs or private briefs. Path discovery was adapted to this checkout; numerical logic is unchanged. Git/package import does not establish fresh network measurements.

Interpret fee growth, token value, reward retention and unused headroom together; report gain size and feasibility as well as the count with any positive opportunity. These findings inform [M3.1’s economic gap](../../../validator-track-workbench.html#M3.1) and [M3.2’s incentive evaluation](../../../validator-track-workbench.html#M3.2), not an automatic scoring rule.
