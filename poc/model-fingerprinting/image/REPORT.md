# IMG-002 — SD 1.4 versus SD 1.5 internal fingerprints

Completed on `smart@smart-nv` using NVIDIA GeForce RTX 3090. Held-out identification: **80/80 (100.0%)**, from **20 held-out prompts in 10 semantic groups**, two matched seeds per prompt and two models. These 80 generations are correlated observations, not 80 independent prompts. Calibration used 10 other prompts in five groups, two other seeds, 20 examples per model.

Each fingerprint is **54 float32 statistics / 216 binary bytes**. The numerical classifier receives only those values, plus model labels during calibration. It receives no prompt, embedding, image, model path/name, hash, timing, memory, dimensions, or provenance fields. Filesystem labels select records for evaluation but do not become classifier features.

## Result

Confusion (rows truth, columns predictions sd14/sd15): `{'sd14': {'sd14': 40, 'sd15': 0}, 'sd15': {'sd14': 0, 'sd15': 40}}`. Seed prediction agreement: 40/40 model/prompt pairs. Both held-out seeds are reused across all 20 prompts; this is a two-noise-realization test, not 40 independently sampled seeds.

Prompt-cluster bootstrap 95% accuracy interval: [1.0, 1.0]. This percentile interval degenerates at perfect observed accuracy. A Wilson interval for the proportion of prompts with all four model/seed predictions correct is [0.838874841947188, 0.9999999999999999], with 20/20 all-correct prompts. Neither interval establishes deployment reliability; prompts within the same semantic group can remain correlated and this is a small synthetic-authored sample.

| Group | Correct / generations |
|---|---|
| bicycles | 8 / 8 |
| birds | 8 / 8 |
| boats | 8 / 8 |
| botanical | 8 / 8 |
| deserts | 8 / 8 |
| dogs | 8 / 8 |
| fantasy | 8 / 8 |
| forests | 8 / 8 |
| kitchens | 8 / 8 |
| workshops | 8 / 8 |

Per-seed results: `{"3303": {"correct": 40, "n": 40}, "4404": {"correct": 40, "n": 40}}`. No accuracy target was required and no held-out tuning was performed. Distances are comparison scores, not calibrated probabilities. Unknown-model rejection is not established.

## Frozen method

`config.json`, `manifest.json` and pinned revisions were hashed before inference. `before-heldout.sha256` freezes the calibration fit, runner and analysis script before held-out generation. `verification.json` checks chronology and hashes. No held-out record existed when `freeze.py` fitted the classifier.

Full stock `StableDiffusionPipeline` text-to-image generation: 512×512 FP16, batch size one image, 25 DDIM steps, guidance 7.5, empty negative prompt, eta 0, no LoRA/refiner/upscaler. Classifier-free guidance internally evaluates an unconditional/conditional pair. Hooks pool **conditional index 1 only**, excluding unconditional index 0. Both models receive identically seeded, CPU-created FP16 initial latent tensors; their hashes match across models and repeats. Effective scheduler values are identical across every load and saved in each `load-*.json`; internal default-value bookkeeping order is ignored in verification. Standard safety checking remains enabled and is outside fingerprint measurement.

Observe corresponding U-Net residual outputs at `down_blocks.1.resnets.1`, `mid_block.resnets.1`, and `up_blocks.2.resnets.1`, at zero-based denoising steps 0, 12, 24. For each valid activation tensor, pool all conditional channels/spatial positions into mean, population standard deviation, mean absolute value, RMS, standardized third moment and standardized fourth moment. Computation uses float32 reductions; summaries are serialized as little-endian float32. No padding or invalid values are included; all these fixed-resolution activation positions are valid. Only bounded summaries are retained, never activation traces.

Calibrate a transparent nearest-centroid classifier with per-feature pooled within-class population standard deviations floored at 1e-6. Compare mean squared standardized distances in float64. There is no feature selection or learned threshold.

## What separates the models

- magnitude: 99.5% of standardized squared centroid gap; diagnostic subset accuracy 80/80.
- shape_moments: 0.5% of standardized squared centroid gap; diagnostic subset accuracy 70/80.

The first four statistics include activation location/magnitude; standardized third/fourth moments are scale-invariant shape summaries. These diagnostic partitions were written in the analysis script before held-out collection and are not replacement classifiers selected from the outcomes. Their results do not change the primary 54-statistic result. Mean can reflect signed offsets as well as scale. Genuine learned activation magnitude is permitted and is explicitly disclosed.

Largest calibration gap contributions:
- `0/down_blocks.1.resnets.1/std_population`: 24.0%.
- `0/down_blocks.1.resnets.1/rms`: 23.8%.
- `0/down_blocks.1.resnets.1/mean_absolute`: 14.5%.
- `24/up_blocks.2.resnets.1/mean_absolute`: 5.1%.
- `24/up_blocks.2.resnets.1/std_population`: 4.2%.
- `24/up_blocks.2.resnets.1/rms`: 4.2%.

## Repeats and instrumentation cost

A balanced fixed subset covers five calibration and five held-out prompt/seed jobs, each on both models. It is repeated once in-process and once after a fresh process/model reload, always with fixed prompt and seed. Held-out repeats never enter fitting.
- repeat-inprocess: 20/20 bitwise-identical fingerprints; 20/20 identical image pixels; 20/20 identical predictions. Maximum absolute feature delta 0; maximum calibration-standardized RMS delta 0.
- repeat-reload: 20/20 bitwise-identical fingerprints; 20/20 identical image pixels; 20/20 identical predictions. Maximum absolute feature delta 0; maximum calibration-standardized RMS delta 0.

One warmup precedes each of eight loads. Ten matched warm uninstrumented/instrumented pairs per model alternate order; baselines remove every hook. Synchronized timing covers full pipeline generation through PIL conversion and safety checking, including hook reductions/transfers. Initial latent construction, model loading/downloads, file writes and classifier comparison are outside the timer. Allocated/reserved peaks include model weights and pipeline work; allocator caching affects reserved figures. Paired bootstrap intervals resample ten jobs (10,000 replicates) and do not capture other days, GPUs or all desktop contention. Raw samples are in `runs/*.json` and `results.json`.

**sd14**: baseline median 1.2926s; instrumented median 1.2979s. Median paired delta 0.00549s, 95% paired-bootstrap interval [0.0038763300981372595, 0.006418911041691899]; median paired overhead 0.42%, 95% interval [0.2994479384389903, 0.49767305094907677]. Identical baseline/instrumented pixels: 10/10.
Peak allocated bytes: `{'timing-baseline': 3440806912, 'timing-instrumented': 3440806912}`; peak reserved bytes: `{'timing-baseline': 4043309056, 'timing-instrumented': 4043309056}`.

**sd15**: baseline median 1.2935s; instrumented median 1.2986s. Median paired delta 0.00509s, 95% paired-bootstrap interval [0.00034381879959255457, 0.012800934026017785]; median paired overhead 0.39%, 95% interval [0.0275583926507339, 0.9902797836930599]. Identical baseline/instrumented pixels: 10/10.
Peak allocated bytes: `{'timing-baseline': 3440806912, 'timing-instrumented': 3440806912}`; peak reserved bytes: `{'timing-baseline': 4043309056, 'timing-instrumented': 4043309056}`.

## Identity and scope

- sd14: `CompVis/stable-diffusion-v1-4` revision `133a221b8aa7292a167afc5127cb63fb5005638b`.
- sd15: `stable-diffusion-v1-5/stable-diffusion-v1-5` revision `451f4fe16113bff5a5d2269ed5ad43b0592e9a14`.

The SD 1.5 repository is the maintained mirror named in the request, not affiliated with the original Runway publisher. Downloads were public and unauthenticated. Actual local checkpoint/config SHA256 values are in `identity-*.json`; tensor-content digests in `component-tensor-identities.json` exclude serialization metadata.

Tensor-content equality across the candidates: `{"safety_checker/model.fp16.safetensors": true, "text_encoder/model.fp16.safetensors": true, "unet/diffusion_pytorch_model.fp16.safetensors": false, "vae/diffusion_pytorch_model.fp16.safetensors": true}`. Tokenizer/config file comparisons are in `results.json`; effective config differences are retained in `effective-component-config-differences.json`. The text-encoder config has projection_dim 512 versus 768, but the actual CLIPTextModel has no projection head and does not use that field (installed source retained in `CLIPTextModel-source.txt`). VAE scaling_factor and norm_num_groups defaults resolve to identical effective values. U-Net functional config values match; private version/path/default-bookkeeping metadata differ. The text encoder, VAE and safety checker have identical tensor contents; U-Net tensors differ. Thus the controlled distinction is denoiser weights in these specific pipelines, including their weight-dependent denoising trajectories, rather than architecture or text-encoder/VAE identity. A later activation also reflects earlier denoising outputs, not solely the local layer weights. Config metadata and hashes are provenance only. Identical component weights here do not imply every deployment uses those components.

This is private empirical identification between two known candidates on one host, runtime, precision, scheduler and parameter setting. Same-family success does not prove every close checkpoint or deployment variant is distinguishable. Job binding, forgery resistance, privacy leakage, secure execution, unknown-model rejection, cross-GPU transfer, other model variants and generalization to other schedulers/precisions/settings were not tested. No output-only baseline was added. This is not a visual-quality benchmark.

## Safety observation and verification correction

The standard safety checker flagged SD 1.5 calibration job p08/1101 (a watercolor illustration of colorful geometric shapes), on its first run, timing baseline/instrumented pair, in-process repeat and reload repeat: five black replacements for one unique prompt/seed job. No held-out image was flagged. Its internal fingerprint still comes from genuine denoising before safety processing. Safety output is never a feature. The timing pixel check establishes equality of 19 non-replaced pairs plus one black-replacement pair; underlying decoded image equality for that flagged pair was not measured.

Initial verification failed a blanket no-safety-flags assertion. That assertion exceeded the protocol, which explicitly permits standard safety mechanisms. The original failure remains in verification-initial.json/log; verification now checks flagged images are black and held-out images are not replaced. No model, classifier, prompt, feature or result was changed.

## Execution, verification and cleanup

Started 2026-10-25T15:31:52Z; completed 2026-10-25T15:43:29.099327+00:00. Environment: Python 3.12.15, torch 2.9.1+cu128, torch CUDA 12.8; versions `{'diffusers': '0.35.2', 'transformers': '4.57.1', 'accelerate': '1.11.0', 'safetensors': '0.8.0', 'numpy': '2.5.4', 'scipy': '1.18.1', 'pillow': '13.0.0', 'torchvision': '0.24.1', 'matplotlib': '3.11.2'}`. Driver/desktop process snapshots are in `host-before.txt` and `host-after.txt`. No existing GPU compute job was present; desktop processes were preserved. One model was loaded at a time. No services, containers, paid calls, credentials, production changes, commits or pushes were used.

The initial smoke failed before generation because provenance logging tried to cast a Transformers config directly to dict; the logger was corrected without changing the frozen measurement protocol. Successful smoke logs are retained. Dependency installation used cached/public wheels, with no source build. The prior ASR environment/artifacts were only read.

Saved generation count: 202 (plus eight unsaved warmups). Numerical fingerprint count: 182. Safety flags: 5. Verification: `{"protocol_config.json": true, "protocol_manifest.json": true, "protocol_models.json": true, "frozen_files": true, "count_saved_202": true, "all_float32_54_finite": true, "all_images_512_actual_hash": true, "matched_latents_across_models_repeats": true, "disjoint_prompt_groups": true, "disjoint_split_seeds": true, "fit_before_heldout": true, "fit_only_calibration_20_each": true, "same_effective_scheduler_every_load": true, "all_eight_phases_completed": true, "safety_replacements_consistent": true, "heldout_images_not_safety_replaced": true, "model_files_unchanged": true}`. Each completion file records GPU allocated/reserved bytes after deleting the pipeline and emptying cache; some process-local allocations (about 33 MiB after evaluation) remain until process exit. The final process check, rather than an in-process zero-memory claim, establishes cleanup. `cleanup.json` records the final process check.

Recommendation: retain this as a bounded same-family checkpoint result and test predeclared transfer conditions in a future separately authorized experiment before making broader claims. No further model runs are needed for IMG-002.

See `README.md` for commands, `separation.png`, `repeatability-overhead.png`, and `contact-sheet.png` for visuals; `results.json` is the full numerical result.
