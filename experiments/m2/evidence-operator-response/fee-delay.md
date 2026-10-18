# SC-17 beside SC-16: settlement shape and delay

This is an offline selected-summary reproduction of **today's system**, not an observation under proposed rules or a forecast. P1 is locally technically complete and pending owner review. Reuse its frozen Arbitrum One extract, file SHA-256 `b69e2b0949953b348470c772b4fc46f9c6510e37e3fb17b5f959a9fc7529d1c8`, content SHA-256 `9f1a8e13b628f68ab65a2a796bc344e455cbbadc55f68221daf39bf75c49c414`. Window 2026-07-17T00:00:00Z inclusive to 2026-10-15T00:00:00Z exclusive; L2 blocks 484622260..514893852. Exact raw redeemed winning-ticket face values, all recipients, grouped by **redemption round**, ETH from wei/10^18. No USD/USDC conversion, per-job invoice, losing-ticket total or creation/job-time inference.

`fee_summary.py` checks the exact frozen file and canonical content hashes, materializes P1 offline and sums integer wei converted from exact ETH decimals. It reproduces selected FR-73/EX-09 summaries; it does not call online extraction or rerun the full 90-day analysis/collection. The existing P1 integrity and source checks are reused as provenance evidence; this selected reproduction is additional arithmetic, not a new independent network observation.

| Selected measured summary | Reproduced value |
| --- | --- |
| Redeemed tickets / ETH | 15,263 / 58.547073107487179205 |
| Intersecting / complete rounds | 102 / 100 |
| Partial edges excluded from ranking | 4270, 4371 |
| Median complete-round ETH | 0.342115455886838978 |
| Round 4317, 8 redemptions | 6.529159045912707051 ETH; 19.0847× median |
| Round 4321 | 3.558239353139740501 ETH; 10.4007× |
| Round 4322 | 2.883617353420 ETH; 8.4288× |
| Round 4320 | 2.532545583654425332 ETH; 7.4026× |
| Round 4323 | 2.395241069493389806 ETH; 7.0013× |

Complete-round ranking includes zero-fee rounds. Edge rounds are partial relative to this window, not incomplete chain rounds. Settlement spikes can arise from redeeming previously created winning tickets; neither the totals nor their recipients establish job time, independent customers, useful demand, purpose or dishonesty. No real sender or recipient is assigned SC-16 or accused of misconduct. SC-17's genuine demand and SC-16's arranged spike are contrasting case premises, not empirical labels attached to round 4317.

October PDF p6, SRC-LP20-OCT L271–278 proposes earliest earning-round-n claim at n+7 with the then-current median. Delay can permit later redemptions/log indexing, a bounded linkage question, voluntary job/terms/use disclosure, independent same-byte checking, evidence correction and individual submissions. It cannot make private records obtainable, authenticate custody, prove purpose from a fee shape or ensure enough scorers act. Job creation, ticket creation, redemption, investigator access and score submission have different times; seven rounds gives no wall-clock response service guarantee.

Under evidence-required a, this settlement-only boundary does not separate SC-17/16 on CL-07. ETH settlement supports today's payment counterpart, not CL-01's qualifying USDC job claim, execution, correctness, availability, independent demand or subsidy value. Under explanation-burden b, a silence cut remains procedural and can cut a genuine surge, exceeding strict false-cut tolerance. It demonstrates no detection. No new purpose matrix, detection rate or median value is supplied.

The extra interval has **conditional observation reach**: D1 arriving n+5 and correction n+6 can inform a first claim; response arriving n+8 cannot protect n+7. Later claim uses its actual median with VD-11 persistence/finality unresolved. Shared published investigation may reduce duplicate collection if evidence is trustworthy and safe. T-ER/T-EC are bounded one public pass/one exchange by construction, not measured effort; T-DP forbids assuming private customer bytes can be disclosed. Missing actionable evidence remains a limitation under T-MV-a; ignoring later obtainable decisive evidence would fail it. Under b a full reward for a hidden violation may miss it, and a cut for silence does not establish that a violation was caught. T-T is unresolved for settlement-only evidence rather than a demonstrated delay defense. Practical gateway/customer requests go to M4.2.

Individual inherited/settlement-only limits: **T-FC-a** permits no unsupported cut; **T-MV-a** accepts unknown as an inquiry limitation and forbids ignoring obtainable decisive evidence. **T-FC-b** fails if a procedural silence cut reaches useful nonviolating work; **T-MV-b** is not satisfied by silence as detection and may miss a hidden violation paid in full. **T-ER** is one public pass; **T-EC** is at most one focused exchange, with feasible cost unmeasured; **T-DP** requires one safe selectively redacted linked source and forbids assuming private payload access; **T-T** depends on actionable arrival and the median at first claim, with no demonstrated settlement-only adverse evidence or guaranteed timely update. These limits apply separately under narrow/broad inherited standards and both evidence levels; no new purpose outcomes matrix is created.
