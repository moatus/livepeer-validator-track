# IMG-002 private GPU experiment

Evidence is local to this directory. Read REPORT.md for outcomes and limits. No production integration or publication. The two fixed public models run one at a time on Smart NV's RTX 3090. Full environment versions are in runtime.json and requirements.lock.

Reproduce in a **fresh experiment directory**, preserving existing outputs. Copy the scripts, this README and requirements.lock. `prepare.py` resolves model revisions at invocation; for an exact pinned reproduction copy this experiment's models.json, config.json, manifest.json and protocol-freeze.json instead of rerunning prepare. All paths are relative to each script's own directory.

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.lock
# New public/synthetic-authored manifest and config (do not overwrite existing evidence):
.venv/bin/python prepare.py
HF_HUB_DISABLE_IMPLICIT_TOKEN=1 .venv/bin/python download.py
.venv/bin/python components.py
.venv/bin/python run.py sd14 smoke
.venv/bin/python run.py sd15 smoke
bash execute.sh
.venv/bin/python verify.py
.venv/bin/python write_report.py
```

For existing evidence, verification and analysis are CPU-only:

```bash
.venv/bin/python analyze.py
.venv/bin/python verify.py
```

Do not rerun generators in this evidence directory: run.py writes named records rather than maintaining an independent replication namespace. execute.sh stops on failure, completes both calibration collections, freezes the classifier and script hashes, then runs held-out collection, timing, in-process and reload repeats. No held-out tuning or accuracy acceptance threshold. Two benign prompts per semantic group; five groups calibration, ten groups held out. Each split uses its own pair of seeds, shared across prompts within the split.

Numerical files are raw 54-element little-endian float32 vectors, 216 bytes. Ground truth and provenance are separate JSON files under runs/. freeze.py uses calibration vectors/labels only. analyze.py classifies from those numerical vectors before reading representative images solely to build the contact sheet. The primary classifier never consumes prompts or images. Model hashes, component identities, original configs, settings, load times, per-run synchronized timings, memory peaks, image and initial latent hashes are saved separately. No full activation traces are stored. Hooks observe conditional CFG index 1 at three corresponding residual layers and steps 0/12/24; standard safety checker remains active outside the feature path.

Sources: [SD 1.4](https://huggingface.co/CompVis/stable-diffusion-v1-4), [SD 1.5 maintained mirror](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5), [Diffusers callbacks](https://huggingface.co/docs/diffusers/using-diffusers/callback). This implementation uses supported PyTorch forward hooks, without modifying model/pipeline source. Checkpoint license: CreativeML Open RAIL-M; model cards are retained with downloads. Prompts are synthetic-authored in prepare.py, frozen before inference.

cleanup.json is a final observed process check, not produced by the inference runner. No processes other than this experiment's own are ever stopped. The venv and public downloaded weights remain for reproducibility; no active worker is intended to remain.
