# JOB-003 — private prompt/job consistency experiment

Run on smart@smart-nv with one already-cached SD1.5 checkpoint, outside product repositories. All data here is private research. `bundle/` is a minimal export suitable for artifact-only verification; it is not published. No prompt or output content is in that bundle. The host agent had access to all roles; there is no OS isolation.

Interpreters:

```bash
cd /home/smart/repos/livepeer/research/job-fingerprinting-poc/2026-10-25
# Existing environment, used read-only; no packages installed into it:
PY=/home/smart/repos/livepeer/research/image-fingerprinting-poc/2026-10-25/.venv/bin/python
```

Exact artifact-only invocation, usable from any working directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 /home/smart/repos/livepeer/research/job-fingerprinting-poc/2026-10-25/bundle/verifier.py /home/smart/repos/livepeer/research/job-fingerprinting-poc/2026-10-25/bundle --output /home/smart/repos/livepeer/research/job-fingerprinting-poc/2026-10-25/reproduced-decisions.json
```

Verifier dependencies: Python 3 and `cryptography` (system installation 46.0.5). No GPU, Diffusers, Torch, NumPy, model download, private manifest, image decoder or generation environment needed. `common.py` defines canonical bytes and uses only the standard library. Numerical scores read only 54 reference numbers, 54 candidate numbers, 54 calibration scale numbers, and the frozen scalar tolerance. Job ID selects an expected record; identifiers and commitments do not enter scoring. Receipt signatures use Ed25519 via `cryptography`. Input and output commitments use independently blinded SHA-256. See REPORT.md for trust limits.

Recheck local experiment integrity and logical access boundary:

```bash
"$PY" check.py
PYTHONDONTWRITEBYTECODE=1 python3 audit_bundle.py
"$PY" analyze.py
```

The full run is reproducible in a NEW empty destination by copying source scripts there (keep the same directory depth so the read-only precedent path resolves). Do not rerun preparation in this completed destination: it would replace frozen private IDs/blindings. Generation refuses to overwrite existing run records. Sequence used:

```bash
python3 prepare.py
python3 requester.py
"$PY" run.py calibration
"$PY" run.py calibration-reload
"$PY" freeze.py
"$PY" run.py heldout
"$PY" run.py heldout-reload
"$PY" run.py collision
python3 build_bundle.py
PYTHONDONTWRITEBYTECODE=1 python3 bundle/verifier.py bundle --output decisions.json
"$PY" analyze.py
"$PY" check.py
PYTHONDONTWRITEBYTECODE=1 python3 audit_bundle.py
```

`prepare.py` freezes 15 hand-authored prompt families, 5 calibration / 10 held out, ABC variants with two seeds per split, and a separately excluded token-collision control. Main independent candidates are actual second runs, not vector copies. `run.py` imports only the precedent observer implementation; it does not invoke the precedent loader/writer. It disables bytecode writes on subsequent loads and uses the old interpreter/cache without environment changes. The initial calibration import used the existing prior module cache; only new experiment artifacts are intended writes. Main parameters: 512×512, FP16, batch1, DDIM25, CFG7.5, eta0, empty negative prompt, normal safety checker. CPU-seeded FP16 initial latents are identical across matched jobs.

`freeze.py` fits feature scales from 30 calibration references and tolerance from 30 independent candidates plus six reloads. It verifies 40 calibration swaps clear tolerance; if not, it stops before held-out inference. No alternate method was used. `before-heldout.json` hashes runner, scoring/export sources, calibration and requests before held-out inference. `private/ground-truth.json` is joined by `analyze.py` AFTER exported verifier scoring.

The export contains `cases.json`, `rule.json`, `public-key.hex`, `verifier.py`, `common.py`. Expected references/output commitments are supplied by the trusted reference runner/observer. Secret test key and independent per-job input/output blindings remain under restricted `private/`. Never export that directory. The export is for logical access separation, not a privacy guarantee about numerical fingerprints.

Commitment encoding: UTF-8 canonical JSON with sorted keys, no whitespace, no NaN; exact supplied strings retained without Unicode normalization. Every hash/signature payload uses big-endian uint64 length-framed fields including version `job003-v1` and a distinct purpose tag. Input covers raw prompt, seed, pinned model/profile, negative prompt, dimensions, precision, scheduler/settings, output format and tokenization semantics. Effective token IDs and token-length checks are private. Raw RGB output identity is length-framed version/domain, big-endian width/height, row-major RGB uint8 pixels after standard safety processing. PNG metadata is excluded. Input/output use fresh separate 32-byte secret blindings. The output observer uses the EXPECTED job's output blinding when hashing delivered bytes. No blinding is exported beside its hash.

Receipt signs version, unique job ID, input commitment, model/profile digest, settings commitment, output commitment, fingerprint digest, measurement version. The worker test key may authenticate lies; verifier must compare numerical evidence and expected/observed output commitments independently. A digest never replaces the 54 numerical values. Scores are RMS distances, not probabilities.

Additional final artifacts: `model-identity.json`, `generation-requirements.lock`, `test-verifier-runtime.json`, `binding-main-scorecard.json`, `final-checks.json`. `delivery_evidence.py` checks the saved alternative output, without inference. `finalize.py` checks expected control behavior and audited decision reproduction. The initial scheduler-bookkeeping check correction is recorded in REPORT.md and verification-initial.json.
