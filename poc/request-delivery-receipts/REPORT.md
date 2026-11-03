# RECEIPT-005 v2 — bounded format correction

**PASS:** original12 core cases (3 honest accepted,9 invalid rejected/unverified),4 boundary controls and7 mutation tests still pass. New signed-format regressions: **14/14 malformed rejected;3/3 valid non-ASCII UTF-8 controls accepted;0 failures**. Spend $0; actual model executions0.

The correction rejects non-UTF-8 JSON/SSE/media and NaN/Infinity/-Infinity consistently. Malformed-input controls exposed this bounded parser defect. The exact verifier change is verifier-v1-to-v2.diff.

Code artifact v2 retains receipt005-v1 signed-wire identifiers, original signed fixtures/public trust and byte-identical PROTOCOL.json. FORMAT-CONTRACT-v2.json makes the JSON/media UTF-8 profile clarification explicit. No new trust component or schema was introduced.

The guarantee remains exchange_verified: authenticated upstream assertions match independently intended request and actually delivered bytes under trusted provider/customer-custody assumptions. Genuine upstream decoy output with substituted customer delivery fails. A dishonest trusted provider can still falsely assert model/version, so hidden weights, causal execution and fresh computation remain unproved. Missing independent freshness/delivery remains unverified; attacker-selected keys remain untrusted. No deployment/interoperability result is claimed.

results.json contains the full v2 core/control replay; format-regressions.json contains17 exact-body signed-format observations; verification.json consolidates counts and original integrity. Original-results.json and original-report.md preserve the historical v1 measurements and analysis; their batch benchmark was **not rerun and is not a v2 measurement**. No broader testing or production throughput experiment was performed.

Original receipt-binding/ is entirely unchanged, including review bundle SHA256 62d1403d17846775204b5f08d2679c3d7c60b50dfee16f2066544f64d6be76c4. Original before/after file hashes are included. The v2 archive contains only synthetic evidence, code, public trust, reports and integrity records; no private keys.

Reproduce with installed Python3/cryptography, no network:

```sh
python3 -B -m unittest -v test_boundaries
python3 -B test_formats.py
python3 -B run.py
```

Reruns overwrite local result files/times; use a separate copy when rerunning. Tests create ephemeral keys only in memory. See README.md for standalone verifier use and declared custody/replay limitations.
