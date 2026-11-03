# Request and delivery receipt verification

Read [the result and limitations](REPORT.md) and [the format contract](FORMAT-CONTRACT-v2.json). The wire identifiers remain v1; the verifier enforces UTF-8 and finite JSON numbers.

Requires Python3 and installed `cryptography` (measured with50.0.0). No network, GPU, real accounts, endpoints or model execution.

Run saved evidence without signing keys:

```sh
python3 -m unittest -v test_boundaries
python3 run.py
python3 verifier.py --receipt fixtures/honest_json/receipt.json --customer fixtures/honest_json/customer.json --trust trust.json --consumed /tmp/receipt005-consumed.json
```

The CLI returns0 for exchange_verified,1 otherwise. Repeating the CLI with the same consumed file rejects replay. Choose a caller-owned fresh file for an independent test. It is a deliberately single-writer harness; concurrent use, atomic persistence and durable multi-session replay protection are not implemented. `run.py` overwrites results.json with newly measured times; the review archive preserves recorded outcomes; no v2 batch benchmark was run.

`trust.json` is independently provisioned verifier policy, NOT discoverable from receipt fields. `customer.json` fixtures stand in for customer-controlled pre-submission intended bytes, fresh challenges and post-delivery actual bytes. Their filesystem source is the explicit trust boundary. An attacker who can replace them or trust.json defeats verification. The receipt issuer/key metadata does not provision trust. Fixture location/labels/expected reasons do not enter `verify`.

`generate.py` can create a new synthetic trial with ephemeral Ed25519 signing keys; it overwrites the fixture set and public key, so use a separate copy. Private signing keys exist only in process memory and are never exported. Run.py and verifier.py replay the saved fixtures with only a public key. Mutation tests create their own ephemeral synthetic key for a signed incomplete-SSE control.

`PROTOCOL.json` was written before first fixture generation/outcomes. Schemas and acceptance policy were not tuned to outcomes. Framing/canonical JSON and Ed25519 mechanics follow JOB-003 common.py/verifier.py; exact-byte SHA-256 replaces private blinded image commitments because these synthetic, disclosed exchange bytes require equality, not a privacy claim. Delivery absence is explicitly unverified, addressing JOB-003's documented receipt-only gap. No product code imported or changed.

`MANIFEST.sha256` describes the original full experiment bundle; it includes development documents that are not distributed here and predates edits to the usage documentation. Use the supplied tests to check verifier behavior. Private keys, caches, credentials, model weights and original private source documents are excluded.
