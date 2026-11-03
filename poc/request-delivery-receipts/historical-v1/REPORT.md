# RECEIPT-005 — independent upstream receipt and customer delivery binding

Private CPU-only synthetic mechanics test. **PASS: 3/3 honest exchanges accepted; 9/9 invalid core cases rejected or unverified; zero false acceptance.** All4 separate boundary controls and7 consequential mutation tests passed. Spend **$0**; actual model executions **0**. This is not deployment evidence, hidden-weight verification, a provider benchmark or an API interoperability result.

The hard decoy attack is rejected: a genuine upstream-signed synthetic expensive-provider response is retained, while independently observed customer bytes contain a cheap substitute. Signature verification succeeds, then delivery equality fails with DELIVERY_MISMATCH. Contacting the genuine provider is insufficient. Under provider honesty and independent custody of customer evidence, this would catch that routing/output dishonesty for the particular bound exchange. It cannot prove the gateway used the provider's result causally or ran a model rather than serving identical cached bytes.

## Frozen protocol and trust

PROTOCOL.json was frozen before fixture generation and measurements (SHA-256: `3b9a572827fb0575cbefcd1a288212735af69ddde9f8bfb2b2e6c96ea4df9e4a`). Signature payload literally contains job_id, client challenge, provider, canonical model/version, full exact request SHA-256, exact response SHA-256, terminal status, format and media URI-to-byte-digest map, plus protocol version. Ed25519 uses established cryptography; versioned length framing and sorted compact canonical UTF-8 JSON reuse JOB-003 mechanics. All fixture requests include user input, instructions and settings. All response comparisons use independent actual delivery bytes, never a gateway-provided delivery digest.

Trust.json pins issuer authority, key, provider and model/version independently of attacker receipts. Customer.json represents separately retained intended request and actual delivery, including fresh client challenge issuance. The offline harness authenticates neither customer custody nor deployment key enrollment: these are declared trusted inputs, not discovered from gateway metadata. Replacing either trusted source defeats the result. Freshness means matching a customer-issued challenge and consuming a job, never a guarantee of new computation.

JSON uses exact bytes; SSE includes ordered LF-delimited event bytes and a final exact [DONE] event. No generic normalization or legitimate transforms are supported. Media JSON records are checked exactly and their mock:// asset URI must resolve in independently retained delivered asset bytes with matching signed digest. No URI fetch occurs. This mock endpoint contract is not NEAR or any provider standard.

## Core outcomes

| Case | Scope | Reason | Receipt bytes | Customer evidence bytes | Request / delivered / asset raw bytes |
|---|---|---|---:|---:|---:|
| honest_json | exchange_verified | EXACT_EXCHANGE_BOUND | 735 | 503 | 117 / 30 / 0 |
| honest_sse | exchange_verified | EXACT_EXCHANGE_BOUND | 733 | 582 | 117 / 70 / 0 |
| honest_media | exchange_verified | EXACT_EXCHANGE_BOUND | 835 | 604 | 117 / 33 / 19 |
| changed_user_input | rejected | REQUEST_MISMATCH | 742 | 510 | 117 / 30 / 0 |
| changed_instruction_settings | rejected | REQUEST_MISMATCH | 752 | 520 | 117 / 30 / 0 |
| changed_delivery | rejected | DELIVERY_MISMATCH | 740 | 508 | 117 / 30 / 0 |
| old_nonce_new_job | rejected | JOB_CHALLENGE_MISMATCH | 741 | 499 | 117 / 30 / 0 |
| duplicate_job_replay | rejected | JOB_ALREADY_CONSUMED | 744 | 512 | 117 / 30 / 0 |
| expensive_provider_decoy_substitute | rejected | DELIVERY_MISMATCH | 759 | 527 | 117 / 30 / 0 |
| truncated_sse | rejected | DELIVERY_MISMATCH | 736 | 557 | 117 / 56 / 0 |
| gateway_signature_as_upstream | rejected | SIGNATURE_INVALID | 753 | 521 | 117 / 30 / 0 |
| missing_signature | unverified | MISSING_SIGNATURE | 594 | 509 | 117 / 30 / 0 |

Customer evidence sizes above include JSON encoding and hex expansion. Exact per-boundary sizes and individual verification times are in results.json; trust.json is additional independently provisioned policy. Cases manipulate actual request/response bytes, signature or independently supplied evidence, rather than asking the verifier to compare expected labels. The expected-reason table is joined only after verify returns. Duplicate replay first accepts the same receipt, then reuses the consumed set and rejects it.

## Boundary controls

| Control | Scope | Reason |
|---|---|---|
| trusted_signer_wrong_hidden_backend | exchange_verified | EXACT_EXCHANGE_BOUND |
| replay_no_independent_freshness | unverified | NO_INDEPENDENT_FRESHNESS |
| missing_independent_delivery | unverified | NO_INDEPENDENT_DELIVERY |
| attacker_chosen_issuer_key | rejected | UNTRUSTED_ISSUER |

The wrong-backend control executes a local lookup returning different synthetic response bytes from mock-cheap-backend. The independently pinned upstream signs the expected model/version assertion over those bytes; independent delivery matches, so exchange_verified is correct within its narrow scope. This deliberately demonstrates that signatures cannot establish an honest model assertion or hidden execution. It is not model_execution_proven. No real backend/model runs.

A genuine saved response without independent freshness issuance is unverified. Even with nonce issuance, a provider can cache or lie about computation. Missing independent delivery is unverified: a valid upstream signature describes upstream output but gives no information about different bytes the gateway may send the customer. An attacker-chosen issuer/key is rejected; supplying a gateway key while claiming the pinned issuer also fails real public-key verification.

Seven focused mutation tests cover delivery substitution/absence, consumed replay, missing freshness and payload edits, attacker-key injection, validly re-signed incomplete SSE, asset byte substitution/missing lookup, and SSE event reordering. The core truncated-SSE case fails exact delivered hash; the additional signed-incomplete-stream test independently checks terminal parsing. Honest JSON/SSE/media fixtures serve as initial readiness smoke controls and all passed before interpreting the attack scorecard; no model calibration is involved.

## Measurements and deployment gap

100 warm CPU batches ×16 saved cases, excluding signing and file I/O: median batch **2.428 ms** (min 2.204, max 2.798); median batch amortized per case **151.7 µs**. This mixed tiny-fixture mock benchmark does not estimate provider latency or production throughput. Python and platform are recorded in results.json.

A deployment still requires a cooperating honest provider or independently authenticated upstream witness, securely enrolled/rotated issuer keys, protected request/challenge and actual-delivery capture, durable replay state, complete stream/async and media custody, agreed byte contracts and privacy/retention policies. These are prerequisites, not implemented components. Customer identity and observation authenticity are assumed; no account framework, TLS integration, daemon, external call, GPU, real credential or Livepeer use was introduced. The single-writer local consumed set is intentionally not a production replay service.

All outputs remain in the authorized private research directory. Prior JOB-003 and follow-up research sources remain untouched. REPORT.md, PROTOCOL.json, code, synthetic fixtures, public trust policy, results and hash manifest form the review bundle; no private signing material is included. No reviewers were launched by this worker.
