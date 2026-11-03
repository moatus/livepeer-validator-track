# Private ASR fingerprinting experiment

Run locally as `smart` on Smart NV. No service/container, production code, paid API, diarization or model training is involved. Python 3.12, CUDA-capable PyTorch, ffmpeg and an RTX 3090 were used. Existing desktop processes were left running. Only one model is loaded at a time.

## Reproduce

```bash
cd /home/smart/repos/livepeer/research/asr-fingerprinting-poc/2026-10-25
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.clean.lock
# test-clean.tar.gz downloaded from https://www.openslr.org/resources/12/test-clean.tar.gz
.venv/bin/python prepare.py
# Use a fresh output directory (archive existing runs first) for an independent reproduction.
timeout 1200 .venv/bin/python run.py parakeet --split calibration
timeout 1200 .venv/bin/python run.py whisper --split calibration
.venv/bin/python freeze.py
timeout 1200 .venv/bin/python run.py parakeet --split evaluation
timeout 1200 .venv/bin/python run.py whisper --split evaluation
timeout 1200 .venv/bin/python run.py parakeet --round 1
timeout 1200 .venv/bin/python run.py whisper --round 1
.venv/bin/python analyze.py
```

`run.py` skips existing per-run output files. Archive outputs and frozen classifier for a fresh independent experiment. Each invocation reloads the model. Round 0 has one inactive-hook baseline and one active-hook run per clip, with order alternated; round 1 has two active runs per clip. Full transcription with word timestamps runs each time. One warm-up precedes each invocation and is excluded from measurements. CUDA synchronization brackets timed inference; model load/download is recorded separately. The output JSON includes raw model timestamps and normalized `text`/`words`, timings, CUDA memory and fingerprint. Fingerprints contain 24 float32 values (96 binary bytes); JSON representation is larger. Only the first encoder call contributes features. The rest of transcription still completes.

## Method and sources

`config.json` specifies the method frozen before inference. `frozen-before-evaluation.json` is fit from calibration before collecting evaluation outputs. Per-model centroids and pooled within-model feature standard deviations define nearest-centroid classification. This learns host/config-specific activation distribution signatures of these two architectures. It does not compare arbitrary hidden-state coordinates across architectures. No ID, filename, shape, padding, timing or word formatting is supplied as a classifier feature. Ground truth is stored as metadata beside, not inside, numerical fingerprints.

Three encoder layers are observed at relative depth 1/4, 1/2, final. PyTorch forward hooks see real hidden states in a complete transcription. Each supplies eight dimension-independent distribution/temporal statistics. Parakeet uses its actual layer `pad_mask` to exclude padding. Whisper restricts pooling to ceil(duration*50) frames from its fixed 30-second window; its attention can still incorporate padded context. Parakeet uses native valid lengths and 8x acoustic subsampling; the summaries do not try to erase architectural differences. The hook observes encoder work only, not decoder identity, timestamp alignment correctness or end-to-end authenticity.

- Parakeet model, CC BY 4.0: https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3
- Whisper official PyTorch implementation, MIT: https://github.com/openai/whisper
- Whisper word timestamps (cross-attention/DTW): https://github.com/openai/whisper/blob/main/whisper/transcribe.py
- LibriSpeech, CC BY 4.0, Vassil Panayotov et al., derived from LibriVox: https://www.openslr.org/12/
- Dataset paper: https://www.danielpovey.com/files/2015_icassp_librispeech.pdf

Dataset selection is deterministic from public test-clean: first ten sorted speakers with three 5–20 second utterances; first four speakers calibration, six held out. Source utterance IDs, reference text, archive/member/WAV SHA256 and normalized paths are recorded in `dataset.json`. All selected files are 16 kHz mono PCM16 written once, identical paths for both models. No private speech or generated speech is used.

See `REPORT.md` for actual results and limitations, `results.json`/`distances.json`/`runs.csv` for numerical evidence, `separation.png` for a standalone plot, `requirements.lock`/`runtime.json` and model identity/hash records for provenance. Logs retain setup failures as well as successful execution.

`environment-observed.freeze` and `requirements.lock` preserve the full measured environment, including unused CUDA-13 dependencies left by the failed initial install. `requirements.clean.lock` is its constrained dependency closure for the selected PyTorch-2.9.1 stack, omitting those unused packages; it is the recommended fresh-install input. The complete experiment was run in the observed environment, not rerun in a second clean environment.
