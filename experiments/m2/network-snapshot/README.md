# Shared measured network baseline for M2

The single authoritative artifact is **`livepeer-arbitrum-2026-10-09-v1.json`**.
Status: **drafted**, published with the M2 branch on 2026-10-14. It describes the deployed network;
it is not a litepaper deployment or an observed self-dealing finding.

Snapshot ID: `livepeer-arbitrum-2026-10-09-v1`.
Content SHA-256: `b879cc73be95d0e5bdcd5c5bc2f2bc342a7319eb27cb6ffdd2ee6c25f4bb60e8`.
The hash covers UTF-8 JSON with sorted keys, compact separators and
`ensure_ascii=False`, excluding the `integrity` object. Monetary quantities and
fractions are decimal strings. Use Python `Decimal`, not binary floating point,
for accounting.

## What is frozen

| Boundary | Value |
| --- | --- |
| Network | Arbitrum One, chain ID 42161 |
| Capture block | 513206238 |
| Block hash | `0x72c814416751eb16375d659b9c304625e64cd4cb71865967c30c8030af6c848b` |
| Original data retrieval | 2026-10-09 13:11:43 UTC |
| State | Current round 4365, incomplete at capture |
| One-round model baseline | Completed round 4364; same-round fees, active stake, cuts and issuance |
| Fee/mint history | 2026-09-09 00:00 UTC to 2026-10-09 00:00 UTC, end exclusive |
| Complete rounds wholly inside that history | 4331–4363, 33 rounds |
| Operator stake supplement | All 100 addresses read later through public archive RPC **at the original block and hash** |

The raw fee total is $31,127.74 of indexed ETH/USD value over 30 days; the
Explorer-adjusted total is $27,023.28. Gross protocol issuance is 985,454.63 LPT.
These are separate current mechanisms. No proposed MFS payout, fee burn,
validator score, execution-cost assumption or self-funded purchase is part of
this measured baseline.

## Contents and source meaning

| JSON section | Use |
| --- | --- |
| `capture`, `integrity`, `units`, `definitions` | Identity, windows, precision and field meaning |
| `current_state` | Supply, active stake, current incomplete round, deployed parameters and population counts |
| `window_30d`, `daily_fees`, `fee_senders`, `fee_recipients` | Redeemed fees, raw and Explorer-adjusted; actual gross inflation mints; preserve one fee recipient inactive at capture |
| `prices` | Separately captured Coinbase ETH/LPT USD spot quotes; no claim-price forecast |
| `latest_completed_round`, `rounds[].pools` | Matched round stake, fee shares, cuts, mint ceiling and actual rewards for all 100 pools |
| `orchestrators` | Current stake rank, live pool capital, measured operator-address stake, other-address capital, cuts and 30-day fees |
| `delegations` | All 3,126 positive indexed address links to active pools; indexed bonded amounts, not fully compounded balances |
| `identity_context` | Public grants-node identity and stake-transfer provenance; no current controller or common-ownership inference |
| `provenance.sources` | Embedded source responses, exact pinned GraphQL queries, archive RPC responses and source hashes |

The Explorer source is pinned at `169ac65bdc4f34a67aa791ddc0a43148a56773d2` and
the subgraph source at `c41182c798219f7faf3f1f6036d07eb7eda64ad5`.
The public Explorer is <https://explorer.livepeer.org>. The subgraph ID and query
text are embedded; its public frontend connection was used without retaining
API keys. Archive operator stake reads use
<https://arbitrum-one.public.blastapi.io>.

Winning-ticket redemption measures settlement, not every job or all independent
demand. Mint events select the protocol Minter and exclude bridge issuance.
The Explorer's two sender exclusions are preserved as a second fee series, not
treated as evidence of misconduct. The primary series remains raw receipts.
The 30-day network total includes a recipient inactive at capture. Summing
only current active operators would miss its historical receipts; the separate
`fee_recipients` table and window coverage field keep that difference explicit.

Pool `rewardTokens: null` in the source means no reward amount was reported:
normalized `actual_reward_lpt` is zero and `reward_tokens_reported` is false.
The original source value remains embedded. Round start/end block numbers are
L1 numbers; the capture block is Arbitrum L2.

**Ownership limit:** operator-address pending stake includes compounded rewards
and commission. It is not all capital controlled by an operator organization.
Other staking wallets may have common ownership; all organizational totals and
beneficial owners remain unknown. In particular, the grants node transferred
bonded stake to another wallet in January 2024 while keeping it delegated to
the same node. Its retained receipts are not established personal profit.

Current protocol active stake and current live pool stake use different
accounting times. Use the completed round's denominator with its pool stakes.
Applying current operator-address ownership fractions to the completed round
is a replay assumption, not an exact historical ownership observation.

## Use in every M2 model

### Agent access without loading the dataset into context

Agents should read this usage note and run `query.py catalog` first. Do not
`cat` the snapshot or ingest the generated HTML: both contain bulk data.
The query tool reads and verifies the JSON in the local Python process and
prints only the requested portion. It needs no external service or database.

From the repository root:

```bash
python3 experiments/m2/network-snapshot/query.py catalog
python3 experiments/m2/network-snapshot/query.py summary
python3 experiments/m2/network-snapshot/query.py operator 4dbc
python3 experiments/m2/network-snapshot/query.py table orchestrators --top 10 --fields address,live_pool_stake_lpt,operator_reward_cut_fraction
python3 experiments/m2/network-snapshot/query.py round 4364
python3 experiments/m2/network-snapshot/query.py pools --round 4364 --top 10
python3 experiments/m2/network-snapshot/query.py table delegations --operator 4dbc --limit 10 --offset 0
python3 experiments/m2/network-snapshot/query.py get /definitions/own_stake
python3 experiments/m2/network-snapshot/query.py get /provenance/sources/operator_stake_rpc/data/operators/2
```

Use full addresses or exact ENS labels when possible. A hexadecimal prefix or
suffix such as `4dbc` must identify exactly one operator; ambiguity is rejected.
The catalog lists section paths, available fields, row counts and raw-evidence
paths. `get` accepts standard JSON Pointer paths, including `~1` for a slash
and `~0` for a tilde in a key. This provides exact structured retrieval rather
than a similarity search over monetary data.

Every result identifies the snapshot, its content hash, the capture block and
the selection. It also hashes the selected data. Table output has `columns`
listed once, followed by rows containing `values` in column order and a
`json_pointer` locating that row in the frozen source. The selection fields
identify projections of that row. Single-object output identifies its source
pointer directly.

Tables return at most ten rows by default. `page.total_matches`, `returned`,
`has_more` and `next_offset` make pagination explicit. Use `--limit` (1–100)
and `--offset` for later pages. `--top 33` still pages at ten rows unless
`--limit 33` is specified. Round-pool selection retains the original
whole-network fee/stake totals and shares; selecting ten pools does not
renormalize their denominator. Current operator-address ownership and indexed
delegation limits accompany those queries.

The default output budget is **12,000 UTF-8 bytes**, not a token estimate.
Oversized results fail with no partial data dump. Select fewer fields, a
smaller page or a narrower pointer. An explicitly chosen budget, for example
`query.py --max-bytes 5000 summary`, precedes the subcommand. Raw evidence is
available by exact pointer, but is never included by default in summary or
table queries.

For modeling over all 100 pools or thousands of records, write a local Python
calculation using the reader below and print only its results. The dataset
can be fully loaded into **program memory** without being loaded into the
**agent's context**. Keep the snapshot itself unchanged.

### Programmatic model inputs

Load this artifact through `read_snapshot.py`; record its ID, content hash,
chosen fee series and round/window in every network-grounded result. Keep all
100 pools in denominators when choosing a subset of operators. Keep synthetic
arithmetic fixtures labelled as such; they do not become measured data.

From a sibling experiment:

```python
import importlib.util
from pathlib import Path

reader = Path(__file__).resolve().parents[1] / "network-snapshot" / "read_snapshot.py"
spec = importlib.util.spec_from_file_location("m2_snapshot", reader)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
snapshot = module.load_snapshot()
observed = module.round_inputs(snapshot)  # completed round 4364, Decimal amounts
```

Each model separately declares its litepaper source/version and rule readings,
costs, scores, future currency conversions and price, ownership assumptions,
strategic actions and any overrides. Do not silently treat historical indexed
USD fees as paid USDC or the current mint ceiling as an approved future rule.
Copy inputs for a scenario; do not edit the frozen artifact.

The original September illustrative M2 tests remain reproducible as originally
specified. Network-grounded extensions use this baseline; this task does not
retroactively replace their historical results or mark them reviewed.

## Verify and view offline

Python 3.10+ standard library only, from the repository root:

```bash
python3 experiments/m2/network-snapshot/verify.py
python3 experiments/m2/network-snapshot/verify_queries.py
python3 experiments/m2/network-snapshot/read_snapshot.py
python3 experiments/m2/network-snapshot/build_view.py
```

Open generated `snapshot-view.html` in a browser. It shows all 100 pools,
searchable operator rows, delegation links, the measured totals and limits.
It is derived from the JSON and carries the same ID and hash; it is not a
second source of truth. The generated view is not committed.

Verification independently reconciles ticket/day/sender fees, mint events,
round pool totals, direct RPC stake and state, 100 address stake splits, source
hashes and hardcoded arithmetic anchors. It checks that the reader rejects a
changed snapshot and an incomplete round. A passing check is not owner review.

To reconstruct from the embedded sources, use `rebuild.py --output NEW.json`.
It needs no remote connection, credentials or original workspace paths and
must produce the same content hash. `collect_operator_stake.py` documents the
read-only archive calls used to supplement the original source capture.
Refreshes receive a new dated/versioned filename and hash; existing snapshots
must not be overwritten.
