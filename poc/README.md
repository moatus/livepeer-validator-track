# Work-verification proofs of concept

These are exploratory implementations and historical experimental results, not adopted protocol mechanisms or newly accepted milestone deliverables. The editable research narrative is in workbench [M3.1](../validator-track-workbench.html#M3.1) and [M3.2](../validator-track-workbench.html#M3.2); this directory supplies inspectable code and evidence.

| Area | Question | What the experiments established | Entry point | M3 connection |
| --- | --- | --- | --- | --- |
| Model fingerprinting | Can internal measurements distinguish models and bind individual jobs? | Strong discrimination in fixed configurations; replay and delivery counterexamples remain. | [Code and studies](model-fingerprinting/README.md) | [M3.2 §2](../validator-track-workbench.html#M3.2): model/job evidence; G02, with potential G05 service use. |
| Output judging | Can finished outputs expose model substitution? | Tested quality scores, image patterns and peer comparisons were insufficient for close substitutions. | [Studies and results](output-judging/README.md) | [M3.2 §3](../validator-track-workbench.html#M3.2): limits on output-based identity claims; G02. |
| Request/delivery receipts | Can signed assertions be checked against independently held job and delivery records? | Synthetic binding checks, including malformed and replay cases; no real inference or TLS claim. | [Corrected report](request-delivery-receipts/REPORT.md), [commands](request-delivery-receipts/README.md) | [M3.2 §4](../validator-track-workbench.html#M3.2): request/delivery linkage and custody; G02–G03. |
| TLS witnessing | Can a customer check a request/response exchange with a named external TLS endpoint? | Implemented exchange evidence, offline checking and bounded routing; privacy, custody and capacity limits remain explicit. | [Prototype](tls-witness/README.md), [limits](tls-witness/LIMITS.md) | [M3.2 §5](../validator-track-workbench.html#M3.2): external-route evidence; G02–G03, with potential G05 service use. |

Gateway data aggregation and combined economic-integrity/QoS scoring are **design work, not implemented PoC packages**. Their current evaluation is in [M3.2 §§1 and 6](../validator-track-workbench.html#M3.2). The [economic models](../experiments/m3/README.md) address G01’s profitability exposure separately. Fingerprints and TLS evidence can support particular service claims; neither is a complete QoS score or a solution to profitable real self-dealing.

## Package scope

Study IDs, model versions and numerical evidence identify each experiment. The packages contain source, results and usage documentation; development reviews and execution logs are maintained outside the repository. Original manifests describe fuller experiment bundles, including material not distributed here, and do not certify the edited documentation or this repository subset.

The TLS code is based on source revision `bc6cf76a3e1ecb15cf33c4156d706a9f6d43137a`, with pinned dependencies, patches and public checker fixtures. Its product documentation is the [usage guide](tls-witness/README.md), [evidence format](tls-witness/EVIDENCE-FORMAT.md) and [limitations](tls-witness/LIMITS.md).

Model weights, downloaded corpora, bulk generated images/audio, virtual environments, build outputs, raw provider transcripts, credentials, private signing material and operational logs are not imported. Numerical fingerprints, generated test receipts, public verification keys, aggregate results and selected non-sensitive illustrations are included. The upstream Vouch Studio reference clone is not vendored. Public distribution of third-party models/assets remains governed by their own terms.

## Reproduction scope

Run commands from the relevant package, using its dependency instructions. Some original GPU scripts and historical records still refer to their original host paths; they are preserved experimental sources, not a claim of turnkey GPU reproduction from this checkout. Full media/hash audits require omitted original media. Historical reports distinguish what actually ran from proposed work.

Useful offline checks, without paid calls or new GPU inference:

```sh
python3 -B poc/model-fingerprinting/job-consistency/bundle/verifier.py poc/model-fingerprinting/job-consistency/bundle --output /tmp/job-fingerprint-decisions.json
(cd poc/request-delivery-receipts && python3 -B -m unittest -v test_boundaries test_formats)
python3 -B poc/tls-witness/tools/cleanroom_check.py check --evidence poc/tls-witness/samples/evidence/body/package.json --client-request poc/tls-witness/samples/evidence/body/request.http --client-response poc/tls-witness/samples/evidence/body/response.http --trust-list poc/tls-witness/samples/evidence/body/trust.json
```

Python receipt checks require `cryptography`. Sample cases intentionally include PASS, FAIL and UNVERIFIED; use each `expected.json`, not process success alone. Full Rust builds need the pinned TLS/Noir dependencies and patch setup described by the prototype. A passed sample check establishes format/checker behavior, not independent witness control or a new live provider test.

## Relationship to M3

[M3.1](../validator-track-workbench.html#M3.1) identifies gaps using these findings and M2. [M3.2](../validator-track-workbench.html#M3.2) records the implementations, tests and lessons so far while comparing possible responses. M3.3 tests selected options through scenarios. M3.4 maps implementation into contracts, nodes and evidence collection. The current direction is to evaluate scoring that addresses both economic integrity and QoS. These PoCs inform that evaluation; specific scoring and reward mechanisms remain undecided. Forum updates remain in the forum, with local drafts outside the published artifact set.
