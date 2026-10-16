# P1: current-system data notes

Status: drafted. Task: [M2.7, issue 29](https://github.com/moatus/livepeer-validator-track/issues/29). Question: how fast does stake move, how concentrated is it, what stake would seat a majority of validators under stated assumptions, what shape do redeemed-fee spikes have, and how does gateway selection work?

Every measured result here describes **today's system (Arbitrum One, pinned window), not a forecast for the litepaper**. No model or simulation is included. HQ-01 and HQ-03 receive measured inputs; GT-04, GT-07 and GT-09 receive calibration and code evidence, rather than final dispositions.

## Source versions

- October litepaper extraction `docs/litepaper-2.0.md`, SHA-256 `3e4a385ec19837f4b506b01989fac62cc33f99f28411bc1258f10c065e29240e`. PDF p.3, “Node operators: permissionless entry, rewards capped by stake” (extraction L123–142) and “Delegation secures nodes and elects who validates” (L150–151); p.4 stake-ranked opt-in validators (L176–189); p.5 “21 Round unbonding” (L229–258); p.10 gateway preference and transferBond open question (L488–493, L525); p.12 parameter table, proposed starting N=33 with declined seats passed down (L578–584).
- Frozen baseline `livepeer-arbitrum-2026-10-09-v1`, content SHA-256 `b879cc73be95d0e5bdcd5c5bc2f2bc342a7319eb27cb6ffdd2ee6c25f4bb60e8`. It supplies the overlap comparison, not movement history.
- Official Livepeer subgraph `FE63YgkzcpVocxdCEyEYbvjYqEf2kb1A6daMYRxmejYC`, deployment `QmRX3dyH6DgftucraNNQ8szgP625VhVP7XCubFbchQuJDw`. Endpoint: `https://gateway.thegraph.com/api/subgraphs/id/FE63YgkzcpVocxdCEyEYbvjYqEf2kb1A6daMYRxmejYC`. Schema introspection and both head and pinned `_meta` responses are retained and hashed. Historical `_meta.block.hash` is null; RPC supplies pinned hashes.
- Raw logs and pinned block headers: `https://arb1.arbitrum.io/rpc`. Historical state: `https://arbitrum-one.public.blastapi.io`. Both cross-check endpoints are keyless.
- [Protocol `46c24fef8c7ccccfb4a55038bd80af7799c904c7`](https://github.com/livepeer/protocol/tree/46c24fef8c7ccccfb4a55038bd80af7799c904c7), branch delta. [go-livepeer `9d4f55ecb183b969dbdf1caf0ac25f9c386530fd`](https://github.com/livepeer/go-livepeer/tree/9d4f55ecb183b969dbdf1caf0ac25f9c386530fd). Pinned source trees were read outside this repository. The workspace go-livepeer copy was not used.

## Inputs and interpretations

| Input | Status and boundary |
| --- | --- |
| Observation window | Fixed 90 whole UTC days, `[2026-07-17T00:00:00Z, 2026-10-15T00:00:00Z)`, timestamps `[1784246400,1792022400)`, L2 blocks 484622260–514893852 inclusive. |
| Checkpoints | Measured headers for L2 blocks 484622259, 494961555, 505240413 and 514893852; respectively just before the window, then 60, 30 and 0 days before the end. The separate start block 484622260 is also checked. Exact hashes are fixed in `extract.py` and in the extract. |
| Today's delegation rules | Measured end-block `unbondingPeriod()` is checked against 7 rounds. Code permits instant redelegation through `bond()` and instant ownership transfer through `transferBond`; earning/active-set eligibility can start next round. The paper's proposed 21-round lock and MFS do not apply to the observations. |
| Validator seats | Stated premise applied to measured stake: top N=33 by total stake, opt-in, declined seats pass down the rank; majority=17 seats. This is not a deployed validator-selection rule. |
| Ownership and costs | Unknown. Addresses are not organizations. No purchase price, coalition ownership, available liquidity or acquisition-cost inference is supplied. |
| Reward purpose | VD-19 research premise is not used. These observations do not judge what rewards are owed for. |

The paper expects an active delegation market and stake to make validator takeover expensive. Those are the intended relationships examined; a present-day transfer or stake threshold cannot confirm them under changed rules.

## Method

`extract.py` introspects the schema, rereads every fixed header and fails on a changed hash. At end-block state it pages all six event collections by `id_gt`, ordered by id with `first:1000`, using timestamp bounds. Rounds overlap the window; transcoders are paged at all four checkpoints. It records exact request bodies, retrieval UTC and a SHA-256 for **each raw response**, including failed large log requests that led to successful smaller chunks. The Graph key is sent only in the Authorization header and is never retained.

The extract stores raw response bytes losslessly as zlib/base64, parsed metadata subsets, source references under `data`, and decoded RPC integer fields as decimal strings. `materialize()` reconstructs the raw collections offline. Compression avoids duplicating bulk responses; it drops no response fields. The extract contains source observations, not the derived tables. Integrity is SHA-256 over sorted-key, compact UTF-8 JSON with `ensure_ascii=False`, excluding `integrity`.

All five BondingManager topics are OR-ed in one filter; tickets have a separate contract filter. Log ranges start at no more than 1,000,000 blocks and bisect on errors. The six topics are independently recomputed with Ethereum Keccak-256 and checked against ERC-20 Transfer. Subgraph event ids encode the transaction hash plus decimal block-wide log index. Matching uses `(transaction hash, log index)`, with no reorganization margin. Every shared decoded ABI field is checked; token amounts require exact `Decimal(subgraph) × 10^18 == raw uint256`. No floating-point token arithmetic is used.

`Round.startBlock`, `endBlock` and `length` are **Ethereum L1** numbers. Pinned headers, transaction blocks, log ranges and historical calls use **Arbitrum L2** numbers. They are never compared across chains.

Stake movement follows the contract's event semantics:

- Bond to a null old delegate is classified as new bond, not necessarily a new participant. Same old/new delegate is a top-up. A changed nonzero old delegate is instant `bond()` redelegation only: existing moved stake is `bondedAmount − additionalAmount`; added capital is separate. Source: `contracts/bonding/BondingManager.sol:568–659`.
- TransferBond first emits Unbond, then TransferBond, then Rebond (`:711–774`). The receiver's existing delegate gets the stake, or the old delegate is inherited if the receiver was unbonded. Attribution uses matching delegator/lock ids and ordered logs in that transaction, checked against RPC. It never reads today's delegation to attribute history. Previous-block old-delegator state is checked by `verify.py`: 1,382 transfers compare exactly; nine are excluded because another earlier same-block event touches the old delegator, apart from the transfer's own Unbond. There are zero mismatches. Withdrawal counts are attributed to a historical delegate only when their matching unbond is in the window; other withdrawals are labelled unattributed. They create no additional active-pool outflow.
- Raw Unbond/Rebond counts include transfer components, marked separately. Transfer ownership, cross-delegate transfers, standalone unbonds/rebonds and redelegations are separate movement measures; they must not be added into one turnover total. Orchestrator flow includes each transfer's component unbond/rebond once; the separate transfer-flow table is not additional flow. Withdrawal releases a lock after its eligibility round (`:262–281`), rather than removing active stake a second time.
- Other delegate-change sequences involving unbonding are separate measures in `slow-path-delegate-changes.csv` and `slow-path-summary.csv`. A standalone Rebond is matched to its in-window Unbond by delegator and lock id. A later new-bond-class Bond is compared with that delegator's latest preceding in-window Unbond; this sequence does not establish where its funds came from. Both require a different old/new delegate. Ordering uses L2 block and log index. `rebondFromUnbondedWithHint` can select a new delegate (`contracts/bonding/BondingManager.sol:861–879`); `processRebond` does not require withdrawal eligibility (`:1632–1659`). The seven-round unbonding wait applies to withdrawal of locked tokens, not necessarily to rebonding or a later Bond using other funds. Actual elapsed rounds and withdrawal-eligibility comparisons are retained instead of assuming that either sequence pays that wait.
- Rate denominators use measured `getTotalBonded()` at start-minus-one and at end. The function returns current-round active stake (`:1213–1219`), which differs in accounting time from summed live pools. Thirty-day/day/round rates are arithmetic averages of this window; per-round averages include the two partial edge rounds. Matched unbond/withdraw lags require both events in the window.

Concentration ranks **all indexed transcoder entities** by live `totalStake`, with active and registration flags retained. Shares use their summed pool stakes, not the active-round denominator. Historical `getDelegator(address).delegatedAmount` checks the top five at end and top two at each earlier checkpoint. `getTranscoderPoolSize()` and maximum size are read at each checkpoint.

The seat table holds incumbents' stakes fixed for added-capital variants. If `k` largest incumbent seats are already coordinated, `17−k` newcomers each must exceed original rank `17+k`; if the largest `d` decline, the relevant original rank becomes `17+k+d`. Adding one wei to each newcomer implements the strict inequality. Declined variants use d in {0,5,10,16}; existing-holdings variants use k in {0,1,3,5}. The redistribution variant finds the smallest j for which the existing stake of the j largest pools exceeds `17 × (stake of original rank 17+j + 1 wei)`. The donor is assumed to control and be able to move all stake behind those j pools; those pools are emptied, other incumbents stay fixed, 17 new registered nodes receive equal stake, and unused donor stake stays outside eligible nodes. Measured j is two at every checkpoint, so this premise does not start with a donor already holding a majority of seats. The assumed control includes delegated stake and is not measured ownership or evidence of its availability. New capital and recycled existing stake are distinct columns. Every row states: **This is a stake threshold under stated assumptions, not an acquisition cost. The cost of acquiring control stays unknown unless evidence supports it.**

Fee tables sum raw winning-ticket face values, with indexed USD secondary. Partial rounds are flagged and excluded from the top-five ranking and its median denominator. Recipient/sender dominance is measured within each ranked round. The overlap with the baseline is checked by individual event id and per-event values as well as aggregate totals. **Redemptions measure settlement, not jobs or independent customer demand.**

See [selection-rule.md](selection-rule.md) for the distinct discovery, ordinary weighted selection, session reuse and realtime-video AI paths at the pinned code version.

## Results

All numbers in this section are **measured for today's system (Arbitrum One, pinned window), not a forecast for the litepaper**, except the explicitly stated validator-seat premises.

Extract: `livepeer-arbitrum-p1-20260717-20261015-v1.json`, captured 2026-10-16 UTC, **14,394,077 bytes**. Content SHA-256: `9f1a8e13b628f68ab65a2a796bc344e455cbbadc55f68221daf39bf75c49c414`. It retains 2,412 request responses, including 33 Graph requests, 515 successful log chunks and 453 large-range error responses. The five-topic BondingManager filter required bisection below a reported 100,000-block limit; the single-ticket-topic filter accepted 1,000,000-block ranges. No source change or window change was needed. The 1,406 historical state calls include 11 exact pool-stake checks and 1,382 previous-block transfer anchors. Raw integers are losslessly compressed rather than dropped to stay below 15 MB.

**Coverage:** all **22,581 events** match RPC one-to-one. There are no missing/extra events and no non-exact shared amount or ABI-field matches. Per-type amounts below are event amounts, not a summed turnover measure; Bond uses additionalAmount. LPT and ETH are separate units.

| Event | Subgraph count = RPC count | Exact token amount on both sources |
| --- | ---: | ---: |
| Bond | 605 | 1,414,889.456074976714192096 LPT |
| Unbond | 2,670 | 4,405,338.102662090947735315 LPT |
| Rebond | 1,466 | 935,156.806003198947279603 LPT |
| TransferBond | 1,391 | 624,600.495439422751222768 LPT |
| WithdrawStake | 1,186 | 3,812,746.899560064253495034 LPT |
| WinningTicketRedeemed | 15,263 | 58.547073107487179205 ETH |

**Movement:** 104 instant `bond()` redelegations moved **1,061,494.613512182428993605 LPT** of existing stake, plus 3 LPT of additional bonding. Existing redelegated stake is **3.6207%** of start-checkpoint active stake or **3.5317%** of end active stake over this window. Arithmetic averages are 11,794.3846 LPT/day and 10,406.8099 LPT per intersecting round. Of 1,391 ownership transfers, 526 changed orchestrator, moving **79,292.984791111954777624 LPT** across delegates, **0.2705%** of start active stake or **0.2638%** of end active stake. All transfer attributions resolved. The other transfers retained the delegate. Raw transfer components are excluded from the standalone 1,279 unbonds and 75 rebonds. There were 76 new-bond-class events and 425 same-delegate top-ups; those labels do not identify new people or new capital purchases. Matched 1,059 unbond/withdraw pairs have a median lag of **7 rounds**, with observed range **7–82 rounds**; 127 withdrawals have no matching unbond in the window.

Separate measured paths involving unbonding, excluded from the instant `bond()` redelegation headline:

| Path | Events | LPT in the later event | Observed lag in rounds | Before withdrawal eligibility |
| --- | ---: | ---: | --- | ---: |
| Standalone rebond to a different delegate, same in-window lock | 3 | 339.525 | 0–35 | 2 |
| Later new-bond-class Bond to a different delegate after an in-window unbond | 7 | 320,278.299237065757191033 | 0–54 | 2 |

These counts agree with the independently recomputed history. Withdrawal of the locked stake pays the seven-round wait; the observed paths above do not all wait until withdrawal eligibility. The later-Bond amounts are sequence amounts, not proven recycling of the unbonded tokens. Event-level ids, matching rules and elapsed times are in the two separate CSVs.

**Concentration and conditional threshold:** shares below use all indexed live transcoder stake. End-block stake totals 30,587,167.809212658828853846 LPT across 272 entities, 233 with positive stake. Exactly 100 have active flags. The distinct RPC current-round active denominator is 30,056,420.251363377765842750 LPT at end and 29,317,201.302405724346755738 LPT at start-minus-one.

| Checkpoint L2 block | Entities for 33.3% / 50% / 66.7% | Rank 17 LPT | Rank 33 LPT | Rank 100 LPT | Base added-stake threshold LPT |
| --- | --- | ---: | ---: | ---: | ---: |
| 484622259 | 3 / 8 / 19 | 374,581.196796 | 227,647.146260 | 9,246.162075 | 6,367,880.345529 |
| 494961555 | 3 / 8 / 19 | 367,009.879026 | 233,907.330992 | 8,841.747655 | 6,239,167.943446 |
| 505240413 | 4 / 8 / 19 | 375,818.915228 | 239,678.744838 | 10,050.607517 | 6,388,921.558870 |
| 514893852 | 4 / 8 / 18 | 379,659.360604 | 246,617.159071 | 10,663.285196 | 6,454,209.130266 |

Base threshold is a **stated premise applied to measured stake**: all top 33 participate, no existing coordinated holdings, incumbent stake unchanged, and 17 equally staked new nodes each exceed original rank 17. Its exact end value including one wei per node is **6,454,209.130265542461741864 LPT**. It is not an acquisition cost. End thresholds under stated largest-rank declines d=5/10/16 are 5,810,475.133121 / 5,328,037.776441 / 4,192,491.704204 LPT. With stated existing largest holdings k=1/3/5, added-stake thresholds are 5,896,535.979500 / 4,963,702.420298 / 4,101,511.858673 LPT. All four checkpoints and the separately assumed redistribution case are in `seat-thresholds.csv`.

Under the separately stated smallest-j donor-pool redistribution premise:

| Checkpoint L2 block | Smallest j | Available top-j stake LPT | Required stake for 17 new nodes LPT |
| --- | ---: | ---: | ---: |
| 484622259 | 2 | 7,851,624.645131205901778800 | 5,982,439.064152629316144817 |
| 494961555 | 2 | 8,024,598.599296156280015153 | 6,109,874.948227325784525216 |
| 505240413 | 2 | 8,323,507.873818681411830247 | 6,222,222.583314030382978824 |
| 514893852 | 2 | 8,563,354.934939629961370029 | 6,206,912.316848201439881046 |

This is a stake threshold under stated assumptions, not an acquisition cost. The cost of acquiring control stays unknown unless evidence supports it. In particular, control and mobility of all stake of the two largest pools are premises, not observed facts.

The pool size and maximum are both measured as 100 at every checkpoint. **Global indexed rank 100 is not the admission cutoff**: eight end-block top-100 entities are inactive and NotRegistered. The lowest current active-flag entity is global rank 111 with 2,787.792661621665397669 LPT. The code tests the actual linked-list tail for next-round entry; P1 does not equate that tail to global rank 100.

**Redemptions:** 15,263 tickets settled **58.547073107487179205 ETH**, with secondary indexed USD **138,403.063692**. There are 102 intersecting rounds (4270–4371); 100 complete rounds enter the spike ranking. Their median is **0.342115455886838978 ETH**. Largest complete-round totals:

| Round | Round start UTC day | ETH redeemed | Ratio to complete-round median |
| --- | --- | ---: | ---: |
| 4317 | 2026-08-27 | 6.529159045913 | 19.0847 |
| 4321 | 2026-08-31 | 3.558239353140 | 10.4007 |
| 4322 | 2026-09-01 | 2.883617353420 | 8.4288 |
| 4320 | 2026-08-30 | 2.532545583654 | 7.4026 |
| 4323 | 2026-09-02 | 2.395241069493 | 7.0013 |

Round 4317 contains eight redemptions; its dominant recipient is `0x180859c337d14edf588c685f3f7ab4472ab6a252` (6.508093175913 ETH), and dominant sender is `0xca3331d67e87816adb30d9562a6e8c0623fb7fef` (4.173728629810 ETH). `fee-spikes.csv` gives each ranked round's dominant addresses and all redemption days, including rounds spanning two UTC days. The dominant recipient is NotRegistered and inactive at the end block; its indexed activationRound is 4319. End-block status is a settlement-context observation and does not establish its status or service at redemption time. These are settlement observations, not demand or misconduct findings.

**Baseline overlap:** all **4,947** frozen-window ticket identities match. The overlap totals **11.998719486500145860 ETH** and **31,127.7394837736766048862027292859291538 indexed USD**. Differences are exactly zero for both totals and every per-event value.

Generated tables under `tables/` cover movement events, day/round/address counts and flows, transfer attribution and ownership flows, separate rebond/later-Bond sequences, rates, matched withdrawal lags, concentration curves, threshold variants, fee series and spikes, RPC decoding/state checks, coverage by million-block bin and baseline overlap. They are rebuilt offline.

## Limits

- The redelegation headline counts instant `bond()` changes only. The separate rebond/later-Bond measures are bounded by in-window matches; a later Bond does not trace recycled funds. The seven-round withdrawal wait cannot be assigned to every such sequence: two events in each path occurred before withdrawal eligibility. Movement under today's incentives and instant transfer/redelegation rules does not establish movement under the paper's MFS and proposed 21-round lock. P1 calibrates the GT-04 example; the example still runs regardless of the measured rate. Event throughput does not measure a delegator's decision latency or the cost of attracting stake.
- A conditional seat threshold is **not an acquisition cost**. A low threshold relative to large address holdings can strengthen a concern conditionally; a high one can weaken it. Neither establishes cheap stake acquisition or enough controllable capital. The GT-03 reopen trigger remains an integrator assessment, not a P1 conclusion.
- A redeemed-fee spike measures settlement, not jobs, their causes, independent customer demand or economic value. The series supplies a reference for HQ-03 and E2, not a verdict about any spike.
- Reading selection code does not establish practical access for a new operator. It supplies GT-07 with code evidence beside existing rerouting controls; gateway production configurations, offers, selection outcomes and service performance are not observed.
- Addresses are not organizations. Common ownership and beneficial control are unknown, and common ownership alone is not misconduct. Token movement and sender concentration are not misconduct findings.
- This is one fixed 90-day window. Both edge rounds are partial; within-window lock matching censors long/edge-crossing withdrawal waits. Counts and amounts can reflect repeated movement of the same stake. Active-round stake and live pool stake use different accounting times. No prevalence, equilibrium, forecast, acquisition-cost or adoption claim follows. Social burdens of judgment are outside this inquiry.

- The deployed BondingManager implementation is not shown to have been built from protocol `46c24fef8c7ccccfb4a55038bd80af7799c904c7`; observed topics, event ordering and the `getDelegator` layout are consistent with that source, without proving deployed source identity.

## Reproduce

Python 3.10+ standard library only, from the repository root. Offline:

```bash
python3 experiments/m2/current-system-data-notes/analyze.py
python3 experiments/m2/current-system-data-notes/verify.py
```

`tables/` and Python caches are ignored. The committed extract is the only P1 data input; the frozen baseline is used only for the overlap check. No network or credential is needed for these commands. The verifier keeps checks active under `python3 -O` and uses constant event, round-boundary and threshold fixtures, all response hashes, exact event reconciliation and tamper rejection.

Online refresh of the **same fixed pins** needs a free Graph key; the keyless endpoints suffice for cross-checks. Export `GRAPH_API_KEY` in your shell (for example from an untracked local env file), then run the collector. It reads `GRAPH_API_KEY` from the environment, sends an explicit User-Agent and refuses to overwrite an existing extract. The command writes a separate destination to preserve the committed version. A re-run with the committed collector reproduces the decoded payload; an independent re-extraction confirmed an identical payload SHA-256. Retrieval metadata can change the extract hash even for the same pins; a published refresh needs a new versioned destination.

```bash
python3 experiments/m2/current-system-data-notes/extract.py --output ./p1-reextract-20260717-20261015-v1.json
```

Unset credentials fail with `GRAPH_API_KEY is not set; load the local env file`. No signup, other key or paid service is used by the collector. If source access fails without the allowed keyless fallback, reconciliation differs or a requested conclusion would exceed these limits, stop and report rather than changing sources, windows or claims.
