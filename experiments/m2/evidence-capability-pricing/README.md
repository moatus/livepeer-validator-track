# EX-07: evidence for capability, pricing and self-funded traffic

Status: **Drafted; technical checks passed, owner research review pending.** This is a synthetic October evidence comparison for M2.2/GT-01, with substantive judgments checked by hand. It supplies neither approved scoring criteria nor measured detection performance.

## Question

Can obtainable evidence distinguish useful outside/internal niche work and ordinary discount routing from the specified knowing misrepresentation or reward-only circular-funding allegation by the first claim at n+7, within the fixed error, review and disclosure ceilings?

The allegations and individual tolerances were fixed first in [tolerances.md](tolerances.md), committed alone as `fc5d202501a413cb7b4009a12c49919f58c22500`. Its SHA-256 remains `df904d04e7bc2c94f789510d9922ca3c633f1ddb6a90f92eff17f1d2a99162ac`. Narrow allegations apply only to explicitly labelled S06-N/S08-N: an operator knowingly represents reward-only jobs as useful internal release tests to retain inflation eligibility. Original S06/S08 have no specified narrow conduct. Broad allegations require circular funding, reward-only purpose and absence of productive/testing use. Both are possible readings, with VD-19 retaining the reward-objective policy dependency. Common ownership, positive returns, low prices and unique capabilities alone do not establish misconduct.

## Sources and input status

| Source | Identity and scope |
| --- | --- |
| October extraction, [SRC-LP20-OCT](../../../docs/litepaper-2.0.md) | SHA-256 `3e4a385ec19837f4b506b01989fac62cc33f99f28411bc1258f10c065e29240e`. Discovery/terms PDF p3 L125–127; honesty scores p4 L203–208; mutual accountability p4 L193–196; votes on published observations p5 L218–221 (O-OBS supports that role only, not observation formats, authentication or correctness methods); claim-time median p6 L271–278; USDC pricing p6 L282–284. |
| [October PDF](../../../docs/sources/litepaper-2026-10.pdf) | SHA-256 `b438da2b7d25d3043a3387b9db262293c2a0ec7801a765e5a3a249759b41569a`. These locators refer exclusively to this extraction/PDF pair. |
| Shared frozen definitions | `inputs.json` SHA-256 `bf518c99987c042821438b4ceea3689aae2122dd7956032b7a1efe2b03b8524f`; `scenarios.json` SHA-256 `7bf3f949d45570387674efe08f29f4ef47b8f7a7121f2ad9f606147d40a81aa5`, both in the [shared configuration](../capability-pricing/). Only allegation, family, control, timing and tolerance definitions are used; no computed economics supplies evidence. |
| [Historical EX-04 tolerances](../evidence-self-funded/tolerances.md) | SHA-256 `da37fa01ac0252792e2dd365219f7996ff2d7ca43c63e2c1abeb6cd0d4869681`. Error/effort/disclosure ceilings and keyed judgment pattern adapted in substance; its September locators and original outcomes are historical. |
| [SRC-GOLP ticket fields](https://github.com/livepeer/go-livepeer/blob/9e68815adf5e72b9c285f178bcdd25b42211efbb/pm/ticket.go#L102-L110) and [AI dispatch](https://github.com/livepeer/go-livepeer/blob/9e68815adf5e72b9c285f178bcdd25b42211efbb/server/ai_http.go#L326-L333) | Pinned commit `9e68815adf5e72b9c285f178bcdd25b42211efbb`; cited originals are byte-identical to that commit. Bounded exact excerpts and their original file/excerpt hashes are retained in [source-index.csv](source-index.csv). ETH ticket fields and dispatch are counterparts, not actual packet settlement or correctness evidence. |
| [SRC-PROTOCOL winning-ticket validation](https://github.com/livepeer/protocol/blob/e02052a04bde9ba1b3bb187d84209e4592e74cad/contracts/pm/mixins/MixinTicketBrokerCore.sol#L298-L302) | Source content matches the 95-file Solidity-tree SHA-256 `168030ca5c7081d4fa3856b14959360735024df84ddc64953ed0fa05525e6ff5`, identified with commit `e02052a04bde9ba1b3bb187d84209e4592e74cad`. Exact bounded excerpt/original identities are in the source index. Ticket checks do not establish productive purpose or the proposed USDC record. |

All actual packet records, control disclosures, competent observations, authentication, source access, adequacy, safe redaction and arrival times are illustrative premises. Particular record formats and internal source bundles are **not specified by the paper**. Code inspection establishes source content, not deployed behavior or public access.

## Method and bounded packets

Read [niche](packets/niche.md) and [discount](packets/discount.md) in arrival order. Each family starts with legitimate outside work (S04 or S02), then useful internal work (S05 or S07), then the matched no-use case (S06 or S08) and its labelled `-N` overlay. Ground truth is kept separate from obtainable evidence. The overlay changes no economic input; real payment, execution and correctness remain accurate.

Public listing/quote/payment, accurately disclosed control/funding and any purpose representation arrive at illustrative n+1. Job terms and authenticated execution/correctness observations arrive at illustrative n+2. One focused question may follow that public review; it adds no purpose evidence or new response deadline. At illustrative n+5 the disclosed level adds one voluntary redacted niche production/test-plan/output-use bundle from S05, or one selection-rule/routing-log/internal-test-plan bundle from S07. No no-use case supplies that productive/testing bundle before the paper-proposed first claim at n+7. Absence is evidential uncertainty, not affirmative adverse evidence.

[matrix.csv](matrix.csv) uses EX-04's columns, keyed by family (`pair`), case, standard, level and claim. It contains **192 illustrative judgment rows**: two families, four cases each, two standards, two levels and six claims. The claims keep payment, execution/delivery, correctness, independent demand, subsidy value and the selected dishonesty allegation separate. Availability remains outside the honesty finding. S04/S02 narrow CL-07 is `unknown` because no narrow conduct is specified, while broad CL-07 is `contradicted` by accurate outside funding. Unmodified S06/S08 likewise have no specified narrow conduct. S05/S07 narrow CL-07 is unknown at public-only, where the true testing assertion lacks linked substantiation, and contradicted at disclosed level by the authentic useful-work bundle. Unknown is not a general innocence finding or a silently added representation.

[verdicts.csv](verdicts.csv) contains **64 illustrative case/consequence rows**, adding `case`, `reading` and `procedural_note` to EX-04's family-verdict pattern. Every family/case/standard/level has one row under evidence-required `a` and one under non-explanation `b`, with a disclosure controller and burden. The family separation verdict is repeated for traceability; its case row records that case's procedural exposure. It is never computed from a payout difference. [config.json](config.json) declares coverage, evidence/source IDs and permitted disclosed cases; it is not a purpose classifier.

## Results and retained counterevidence

Every family/standard/level verdict is **does not separate**, under both readings: no obtainable source establishes the paired violation. Public observations support payment and the job-specific execution/correctness checks. Disclosed common control contradicts independent demand for internal cases. Accurate outside funding/control explanations are available, but downstream own use is not independently authenticated, so the complete independent-demand claim stays unknown for outside cases. Under the broad standard, outside funding/control excludes the circular-funding element for S04/S02; this protects an outside reference without proving misconduct in a controlled case. No source establishes subsidy value.

For S06-N/S08-N, matrix CL-07 notes assess all four narrow elements individually at both standards and levels: representation **established** at n+1 (P-REP; U-REP); falsity **unknown**; knowledge **unknown**; eligibility purpose **unknown** (U-REP; U-CLOSE; not specified by the paper). The whole narrow allegation remains unknown, and the broad purpose assessment stays separate.

The one authentic, adequate, linked disclosed bundle contradicts the selected allegation against useful S05/S07 under both standards. It provides no evidence of the paired case's falsity, knowledge or eligibility purpose, and no evidence of reward-only purpose or absence of use. Those claims remain unknown. Neither source delay nor undisclosed ground truth completes that evidence.

Reading `a` supports no adverse finding on unresolved cases. Reading `b` may permit a non-explanation cut on unexplained internal jobs, including useful work at the public level. Timely safe adequate disclosure can protect S05/S07 in the disclosed branch; the unproved paired case may still face a procedural cut. Such a cut is not violation detection. Applying a narrow silence-based cut to original S06/S08 would penalize cases containing no specified narrow act. Accurate public outside explanations remain available in both levels; no non-explanation cut is assigned to those branches. Consequences depend on a changed median at claim, with neither an individual-score-to-median response nor correction assumed.

## Each fixed tolerance assessed

These are logical tolerance outcomes and procedural exposures, not error frequencies or observed costs. Both families receive the same ceilings. Where the packet fits a ceiling by construction, feasibility remains unmeasured.

| Tolerance | Outcome in both families |
| --- | --- |
| T-FC-N-a | Met under the evidence-required reading: no cut solely for control, rewards or silence; no specified narrow act is added to original S06/S08. This is a conditional judgment rule, not demonstrated error-free operation. |
| T-MV-N-a | Accepted limitation: the alleged `-N` violation remains unproved within the source/burden boundary. No establishing evidence is ignored; effective detection is not demonstrated. |
| T-FC-N-b | **Not met.** Reading b permits a silence cut on nonviolating useful S05/S07 at public-only and original S06/S08 under narrow at either level. The disclosed level protects S05/S07 when the bundle is authentic, adequate, safe and timely; the original-case exposure remains. No correction is assumed. |
| T-MV-N-b | No established violation is ignored in these records; the alleged `-N` violation remains unresolved. A permitted non-explanation cut does not demonstrate detection of representation/falsity/knowledge/eligibility purpose. |
| T-FC-B-a | Met under `a`: no control/reward/unused-output/absent-public-use-proof cut is made. Useful and mixed-purpose work remain protected; accurate outside funding contradicts the circular-funding element. |
| T-MV-B-a | Accepted limitation: reward-only purpose and absence of use remain unknown within the one-bundle boundary. No established broad violation is ignored; the hidden violating premise is not detected on evidence. |
| T-FC-B-b | **Not met at public-only:** reading b permits a silence cut on nonviolating useful S05/S07. **Met for S05/S07 at public+disclosed** on the stated authentic, adequate, safe and timely bundle premises; this protects that useful case without proving the paired violation. Inability to disclose retains false-cut exposure; no empirical protection is demonstrated. Outside explanations remain available. |
| T-MV-B-b | No established broad violation is ignored in these records; purpose stays unresolved. Procedural cuts do not prove reward-only purpose or absence of productive/testing use. |
| T-ER | Within the ordinal ceiling by construction: one public-source/arrival review at public level; six claims kept distinct. Review time, source-access effort and actual competence are unmeasured. |
| T-EC | Within the declared ceiling by construction at the disclosed level: routine review plus one question, one response and one linked family bundle. Feasibility before n+7 and adequate response opportunity are assumed, not demonstrated. |
| T-EX | Respected in the bounded inquiry: no repeated demands, unrelated audits, interviews, identity tracing or reconstruction is used. This does not establish that a real investigation can finish without them. |
| T-DP | Within the ceiling by construction: only relevant redacted family metadata is inspected; unrestricted code, payloads, credentials, accounts, unrelated histories and a full roadmap are excluded. Safe adequate redaction is assumed; inability to disclose under `b` remains exposure, and eventual explanation does not erase preparation/privacy burden. |

## Verification and limits

The standard-library verifier checks exact columns, allowed values, complete configured keys, source IDs on every evidence record/row, chronological arrival and disclosure scope, existing source files and line bounds, exact quoted text after whitespace normalization, snapshot and excerpt hashes, and unchanged tolerance content. In a Git checkout it also compares tolerance bytes to the recorded commit; without Git it checks the same pinned content hash. Small current-system excerpts retain original upstream path, revision, line coordinates and full-file hash, so repository-only copies can verify the cited content. Optional explicit source roots additionally compare excerpts and full-file hashes to the originals. Excerpt validation alone does not refetch or independently authenticate the upstream repository.

The verifier validates structure and recorded provenance, not the substantive judgments, practical evidence access or the truth of purpose. It writes no outputs. These synthetic packets measure neither accuracy, reviewer effort, prevalence nor beneficial ownership. Privacy cost, safe disclosure, timing, authentication, general availability, contested-case incidence and validator incentives remain unmeasured. The two families do not establish universal impossibility. E2's original pairs remain pending, and GT-01 remains proposed. Whether any different treatment is needed remains VD-19/GT-03; no successor mechanism, economics or adoption decision is supplied here.

## Reproduce

From the repository root, Python 3.10+ and its standard library:

```bash
python3 experiments/m2/evidence-capability-pricing/verify.py
```
