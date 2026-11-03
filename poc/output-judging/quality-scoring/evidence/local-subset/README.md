# JUDGE-004 standalone pilot

Read `REPORT.md` for measured results and the external-judge blocker. This directory contains a completed 216-image local experiment and **no Nemotron measurements**. No script here makes a paid inference request.

## Inspect / verify without GPU, network, or new paid calls

From this directory:

```bash
.venv/bin/python verify.py
.venv/bin/python analyze.py --verify
```

Verification hashes all raw/normalized outputs, checks family/seed splits, duplicate usable images, matched SD1.x noise, numeric feature allowlists, pixel statistics and embedding-score consistency, then recomputes saved model selection and results. Reproducing results uses saved `local-scores.npz`; model weights are not needed for verification. `verification.json` is refreshed by verification and excluded from the immutable artifact hash list.

## Contents

- `PROTOCOL.json`, `prompts.json`, `.sha256` files: prespecified settings, requirements, family splits and seeds.
- `download-identities.json`, `SCORER-LOCK.json`, `checkpoint-verification-*.json`: exact immutable revisions, file hashes and pre-score locks.
- `raw/`, `normalized/`, `records/`: 216 generation attempts, images and per-image provenance/hashes.
- `stability-inputs/`, `stability-manifest.json`: twelve selected prior images; no completed judge votes.
- `local-scores.npz`, `.csv`: raw preference scalars, image/text embeddings and fixed visual features for base/JPEG75/resize256 variants. The CSV omits bulky embeddings; NPZ preserves them.
- `frozen-analysis.json`, `results.json`, `predictions.json`: saved decisions, confusion counts, clustered intervals, coverage and individual predictions.
- `nemotron-scores.json`, `nemotron-describe.raw`, `mcp-tools.raw`, `loc-catalog.json`, `blockers.json`, `spend.jsonl`: exact missing-route evidence and zero-call accounting.
- `accuracy.png`, `robustness-quality.png`, `contact-sheet.jpg`, `result.html`: standalone plots/representative media.
- `code-history.json`, `code-hashes-initial.json`, `artifact-checksums.sha256`, `cleanup.json`, `requirements.lock`: execution/version/audit trail.

## Reproduce local generation/scoring

Use a **new sibling directory**, copying frozen manifests/scripts, never overwrite this run. The original exact SD1.x caches must remain available read-only at `/home/smart/repos/livepeer/research/image-fingerprinting-poc/2026-10-25/models/{sd14,sd15}`; file identities are rechecked. Downloading those exact revisions elsewhere and changing the explicit `OLD` cache path is required on another machine. All new SDXL/PickScore/processor downloads are pinned by copied `download-identities.json`; `download.py` reuses the immutable lock, not mutable main.

Create a Python 3.12 venv in the new directory. Set `UV_CACHE_DIR` to a new subdirectory there before installing `requirements.lock` with uv. The initial run used default uv cache; see the containment deviation in cleanup. Model downloads set `HF_HOME` inside the experiment directory and disable implicit HF token use.

Execute these scripts with that venv, in order (one GPU job at a time):

```bash
python download.py
python generate.py sd14
python generate.py sd15
python generate.py sdxl
python score_local.py
python analyze.py
python plot.py
python write_report.py
python verify.py
```

Copy `PROTOCOL.json`, `PROTOCOL.json.sha256`, `prompts.json`, `prompts.json.sha256`, `download-identities.json`, `stability-manifest.json`, `spend.jsonl` and all current scripts to the new directory first. `prepare.py` is the original authorship helper, **not a resumption/reproduction step**. It refuses to overwrite a frozen protocol. The authored protocol was pinned before generation; exact scorer identities were locked before scoring, with the timing caveat stated in the report.

`generate.py` resumes only completed records; an attempt marker without a terminal record fails closed rather than silently rerolling. There are no warmup images. Never delete attempt records to reroll inside the 216-image cap. `analyze.py` refuses to overwrite `frozen-analysis.json`; use `--verify` for deterministic recomputation. Do not choose new methods after inspecting heldout results.

`score_local.py` needs GPU and local weights; verification does not. Models retain standard pipeline safety behavior. SDXL base has no built-in safety checker; its optional invisible watermarker was disabled as prespecified. No refiner, hidden generator hooks, GenEval detector, MCP server or product integration is added.

## External judge

No configured user-owned Agent bearer or verified live bounded token rate was available. Free MCP discovery is not paid account authorization. Do not run via keyless demo credits or substitute another provider. Current declared route is `create_media` with model override `nemotron-omni-vision`; the historical Vouch `run_capability` tool is absent in the retrieved current catalog. A future judge experiment needs authenticated supported access, current price/max-token bounds, one valid smoke, 36 retained stability votes and schema freeze before a new untouched evaluation. Do not retrofit these locally inspected heldout outputs into a claim of a new fully blinded experiment.
