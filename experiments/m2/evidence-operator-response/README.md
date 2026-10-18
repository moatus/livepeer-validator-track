# EX-10 — Evidence and operator response

## Task and question

M2.8 E2 (#30), GT-01 correctness and GT-06: can evidence obtainable before claim support a specified adverse finding, and can an operator answer inside predeclared error, effort, disclosure and timing limits? Stop after four bounded pair dispositions, six access inventories, both response paths and two conditioned Slice 3 inputs. No economic model or new purpose matrix.

## Source versions

October extraction SHA-256 `3e4a385ec19837f4b506b01989fac62cc33f99f28411bc1258f10c065e29240e`, PDF `b438da2b7d25d3043a3387b9db262293c2a0ec7801a765e5a3a249759b41569a`. [Paper](../../../docs/litepaper-2.0.md): PDF p4 L193–208 incorrect results/dishonesty, p5 L218–221 shared investigation, p6 L271–278 delay/current median and L282–284 USD prices/USDC. EX-01's September SHA `5fc153408fb636d9750788ae987ada6daaa9fc3df3e44f70cadde51a6158fb71` stays historical. SPEC 0.13 / RUNBOOK 0.12 and [DECISIONS](../../../docs/DECISIONS.md)' 2026-10-15 M2 research premise govern. Rewards are treated as owed to real, correctly executed, honestly represented paid work; reward-only self-purchase is treated as dishonest. This is a research premise, not adopted policy; beyond-paid-work contribution stays conditional where eligibility changes.

Unchanged [source-manifest.json](source-manifest.json) pins inherited sources and eight full code files/excerpts: go-livepeer `9d4f55ecb183b969dbdf1caf0ac25f9c386530fd`, protocol `46c24fef8c7ccccfb4a55038bd80af7799c904c7`. They establish source bytes, not deployment/operational access. [outcome-source-manifest.json](outcome-source-manifest.json) pins the authored fixtures and new research slices without rewriting earlier identities. P1 extract file/content hashes and exact window/ETH boundaries are in [fee-delay.md](fee-delay.md). P1 ancestry `229bb1a` remains unpublished and pending owner review.

Prospective tolerances SHA-256 `3a9a8d968b6ba77e4e8342ca4b9fb630086b323bd1e0f9432eaf6e90d9d77176` were committed alone at `b9c41b63db9fcdd038925347677a7b9b5cee5174`, before outcomes. Accepted reconstruction commit `fc6ce6e427003d100c9e75172dc31d33f9c818b1`. These pins do not imply owner acceptance of E2 or policy adoption.

## Inputs with their status

[tolerances.md](tolerances.md), [reconstruction.md](reconstruction.md) and [input-manifest.md](input-manifest.md) are preserved prospective criteria/source reconstruction. `fixtures/` contains **authored fixed synthetic fixtures**: valid PNGs, terms, input and stipulated identity/custody bundle. They are intended research inputs, not regenerated model outputs or actual jobs. Hashes check local bytes, not delivery authentication. EX-04/07 results are reused at their original boundaries; EX-08 supplies scope mapping only. Frozen P1 is observed public current-system settlement with its stated provenance.

## Method

Read [SC-10/11 packet](packets/sc10-sc11.md) in arrival order, legitimate variation first. Public complaint n+1; one notice/reasons n+2; one safe disclosed bundle n+5; possible same-byte evidence correction n+6; first claim n+7. All arrival/access/custody assertions are illustrative assumptions. Inspect the same fixed delivered-by-stipulation bytes using Pillow 12.3.0 with <=1 MiB input, <=2 seconds and <=256 MiB decoder address space enforced. No stochastic regeneration or general semantic test.

EX-04's `matrix.csv`/`verdicts.csv` columns, allowed claim states and reading=a/b verdict-note convention remain. Minimal extensions: seven claims including CL-04, correctness standards `term-breach`/`knowledge-required`, packet record IDs cross-linked to bundle and exact source manifest. [Inventory](record-inventory.csv) separates code existence, frozen public records and conditional disclosure. [Tolerance assessment](tolerance-assessment.csv) evaluates each limit separately, keeping actual median action unobserved. The public+disclosed SC-26 path names the requested evidence level; decisive bundle is unavailable by cutoff, so its preclaim state remains public-only.

## Results

- SC-10/11: public does not separate. With stipulated accepted-term/job/delivery custody and safe timely D1, locally decoded 512×512 SC-10 passes K1; 256×512 SC-11 fails the accepted term. This conditionally separates under term-breach only. Knowledge-required remains unknown for SC-11; no knowledge source is supplied. Passing K1 leaves full semantic CL-03 unknown. CL-02 depends on stipulated direct observation; no qualifying USDC settlement, general availability, independent demand or subsidy value is established.
- SC-17/16: [offline fee note](fee-delay.md) reproduces 15,263 redemptions / 58.547073107487179205 ETH, 100 complete of 102 intersecting rounds, median .342115455886838978 ETH and round 4317's 6.529159045912707051 ETH. Settlement shape does not separate genuine demand from arranged fees; extra rounds help only if actionable evidence and score updates arrive. No recipient is accused.
- SC-06/07: [inheritance disposition](inheritance.md) retains the does-not-separate purpose result under corresponding observations; a release plan cannot become an affiliate production-use record automatically.
- SC-25/26: [matched response paths](operator-response.md) hold merits fixed. Timely authorized receipt allows correction, while n+8 receipt cannot protect n+7. Evidence sufficiency never guarantees score submission/current median. Silence cuts can exceed strict false-cut tolerance. Preparation, metadata disclosure and income uncertainty persist even after a correct judgment; Defense burden remains a separate question for M2.3.

[Slice 3 inputs](slice3-inputs.md) are the inherited inconclusive purpose case and conditional sufficient K1 term-breach case. Evidence conditions feed later tested scores/costs into the existing shared ledger; E2 invents no score magnitude, payoff or economic value. [Practitioner dispositions](practitioner-dispositions.md) give concrete gateway/customer evidence requests to M4.2; detailed procedure remains M4.3. No outreach occurred.

## Limits

This compact verifier checks structure, coverage, source hashes/references and cross-links, plus actual local geometry/selected arithmetic. It cannot certify substantive research judgment, production custody, safe practical access, human effort, empirical error/detection rates, prevalence or incentives. The synthetic timing schedule is not a seven-round wall-clock guarantee. Reading a retains unsupported allegations as unknown; reading b's procedural cut is never evidence of misconduct. No appeal, confidential channel, individual-score visibility, correction, influence benefit or reward recovery is assumed.

## Reproduce

From repository root, Python 3.10+, Linux, the only added dependency is version-pinned Pillow:

```bash
uv run --no-project --with Pillow==12.3.0 python3 experiments/m2/evidence-operator-response/verify.py
```

This reads committed/fixed inputs offline; no extractor/network call or Git metadata is used. `check_k1.py` and `fee_summary.py` may be run individually with the same environment. They print regenerated observations/summaries to stdout; do not commit these outputs. All Markdown/CSV judgments, JSON manifests and PNG fixtures are authored fixed inputs. No generated files need a repository ignore rule.
