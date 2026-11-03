# JUDGE-004: local Qwen paired exploratory extension

This is a paired exploratory extension of the frozen original experiment, not fresh blind confirmation. Original heldout outcomes had already been seen. No new images were generated. No Livepeer, hosted inference, credentials, uploads, product edits, commits or publication were used. Hosted spend is exactly $0; local electricity and hardware costs were not measured.

## What was run

Official `Qwen/Qwen2.5-VL-7B-Instruct`, immutable revision `cc594898137f460bfe9f0759e9844b3ce807cfb5`, BF16 on one RTX 3090 24 GB using Transformers 4.57.1 / torch 2.9.1, SDPA, no quantization or fallback. This is a general local instruction VLM, not a trained reward judge, Nemotron, or Vouch. Hosted Nemotron remains unrun. Official documentation: https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct .

Weights/configs were downloaded from the official public repository to this extension’s `model/`, with anonymous access. All selected files have SHA256 hashes in `model-lock.json`. A new `.venv` uses the prior experiment’s compatible pinned packages, installed through uv’s shared package cache; no prior environment was changed. Hugging Face/Xet may use its ordinary shared transport cache. No source builds, driver/service changes, or unrelated process shutdowns occurred. Model weights and environment remain local and are excluded from the review bundle.

Inputs are the original normalized 512×512 RGB images; processor bounds are 256×28×28 to 512×28×28 pixels (actual image grids and token counts retained per call). Only in-memory pixels, prompt text, and a frozen checklist reach the model; no filenames, sample IDs, labels, latency or price enter the judge prompt or classifier features. Greedy decoding: seed 904, do_sample=false, one beam, max_new_tokens=160, context cap 2048. JSON is parsed strictly, without extraction, repairs, or retries. Individual raw votes and token IDs remain in `raw-responses.jsonl`. Full vocabulary soft logits were not retained.

Protocol/checklists were frozen before Qwen outputs (`PROTOCOL.json`, `inputs.json`, `freeze-hashes.json`). Code and dependency identities at scoring are in `execution-lock.json`. The stability inputs precede all main-set scoring. No rubric or classifier tuning followed stability or heldout inspection.

## Hardware, time and cost

Initial availability: RTX 3090 24 GB, ~24 GB VRAM free, 20 GB host RAM available, 1.1 TB disk free. Official BF16 weights fit without quantization. Download+weight hashing: 309.2 s; model load: 40.0 s; model load+scoring after Python imports: 414.8 s. Initial Python/runtime imports also took several minutes of disk waits (see `score-process.json`). Peak allocated CUDA memory: 15.57 GiB; reserved: 15.64 GiB. Process peak RSS: 3.46 GiB. These are process measurements, not whole-host maxima. Calls: 251/280; hosted spend $0.

## Coverage

| Generator | Original usable | Attempted | Parsed | Parse failures | Runtime failures | Train/cal/heldout parsed |
|---|---:|---:|---:|---:|---:|---|
| sd14 | 72 | 72 | 10 | 62 | 0 | 5/4/1 |
| sd15 | 71 | 71 | 15 | 56 | 0 | 7/5/3 |
| sdxl | 72 | 72 | 5 | 67 | 0 | 2/1/2 |

A descriptive audit of formatting is in `failure-audit.json`; every vote/status is in `score-coverage.csv`, and all 24 prompt-family coverage counts are in `per-prompt-coverage.json`. Incomplete strict-schema coverage is a substantive failure of this fixed judge configuration. Complete-case results, if present, are selected by format compliance and cannot establish performance on the full frozen corpus. No extraction or protocol repair was added after seeing failures.

The original has 216 generation attempts and 215 usable images. Its one excluded safety/black image is not silently restored. All comparisons below use exactly the same successfully parsed main images, joined to saved baselines by stable sample ID. Failed outputs remain explicit in the raw ledger; no missing-value signal is used.

## Identification results

Only 30/215 main images passed (185 strict parse failures). Consequently the primary heldout comparison has just four images and the secondary just six. These tiny selected subsets cannot answer whether Qwen adds identification signal across the corpus. Baseline methods below are refitted using the same complete-case train/cal subset as Qwen, rather than reusing the historical models fit on all usable images.

Ridge one-vs-rest with intercept, training-only StandardScaler, alpha selected on original calibration families from [100,10,1,0.1] with ties favoring the first/larger value. No refit on train+cal and no heldout threshold search. Original whole-family split is preserved: 12 train / 6 calibration / 6 heldout; seeds are shared across matched generators, disjoint across splits.

Qwen vector: four sparse requirement outcomes (no=0, partial=.5, yes=1; inapplicable numerically zero) plus four explicit applicability masks, craft/10 and aesthetics/10. Applicability is authored per prompt, shared by all generators; no prompt ID enters features. Quality scalar preserves the original formula: .6×mean(applicable requirements)+.25×craft/10+.15×aesthetics/10. Craft and aesthetics are subjective VLM ratings, not human ground truth.

| Task | Features | Heldout correct/n | Accuracy | Prompt-mean bootstrap 95% interval |
|---|---|---:|---:|---|
| sd1x | pickscore | 2/4 | 0.500 | [0.000, 1.000] |
| sd1x | visual | 3/4 | 0.750 | [0.250, 1.000] |
| sd1x | visual+pickscore | 1/4 | 0.250 | [0.000, 0.750] |
| sd1x | qwen | 3/4 | 0.750 | [0.250, 1.000] |
| sd1x | qwen+pickscore | 1/4 | 0.250 | [0.000, 0.750] |
| sd1x | qwen+visual+pickscore | 2/4 | 0.500 | [0.000, 1.000] |
| sd1x | qwen_quality | 3/4 | 0.750 | [0.250, 1.000] |
| threeway | pickscore | 4/6 | 0.667 | [0.250, 1.000] |
| threeway | visual | 1/6 | 0.167 | [0.000, 0.375] |
| threeway | visual+pickscore | 1/6 | 0.167 | [0.000, 0.375] |
| threeway | qwen | 3/6 | 0.500 | [0.125, 0.750] |
| threeway | qwen+pickscore | 3/6 | 0.500 | [0.125, 0.750] |
| threeway | qwen+visual+pickscore | 0/6 | 0.000 | [0.000, 0.000] |
| threeway | qwen_quality | 3/6 | 0.500 | [0.125, 0.750] |

Qwen alone predicted SD1.5 on every retained heldout image for both tasks (confusion matrices: primary [[0,1],[0,3]]; three-way [[0,1,0],[0,3,0],[0,2,0]], rows/columns SD1.4, SD1.5, then SDXL). Thus its 3/4 and 3/6 merely match the retained subset’s majority-class accuracy, and show no generator discrimination on these cases.

Original published baselines were PickScore 21/36 and visual+PickScore 22/36 on SD1.4 vs SD1.5; 31/54 and 35/54 on three-way. Shared-case denominators above must be checked before comparing these historical counts. `results.json` includes raw confusion matrices with class order, train/cal summaries, and per-prompt counts. `predictions.json` contains every train/cal/heldout prediction; `fitted-analysis.json` retains selection and normalization parameters.

## Matched within-image changes

| Task | Comparison | Improved | Worsened | n | Accuracy difference | Paired cluster interval |
|---|---|---:|---:|---:|---:|---|
| sd1x | qwen minus pickscore | 1 | 0 | 4 | +0.250 | [+0.000, +0.750] |
| sd1x | qwen minus visual+pickscore | 2 | 0 | 4 | +0.500 | [+0.000, +1.000] |
| sd1x | qwen+pickscore minus pickscore | 0 | 1 | 4 | -0.250 | [-0.750, +0.000] |
| sd1x | qwen+pickscore minus visual+pickscore | 1 | 1 | 4 | +0.000 | [-0.750, +0.750] |
| sd1x | qwen+visual+pickscore minus pickscore | 1 | 1 | 4 | +0.000 | [-0.750, +0.750] |
| sd1x | qwen+visual+pickscore minus visual+pickscore | 1 | 0 | 4 | +0.250 | [+0.000, +0.750] |
| threeway | qwen minus pickscore | 0 | 1 | 6 | -0.167 | [-0.375, +0.000] |
| threeway | qwen minus visual+pickscore | 2 | 0 | 6 | +0.333 | [+0.000, +0.750] |
| threeway | qwen+pickscore minus pickscore | 0 | 1 | 6 | -0.167 | [-0.375, +0.000] |
| threeway | qwen+pickscore minus visual+pickscore | 2 | 0 | 6 | +0.333 | [+0.000, +0.750] |
| threeway | qwen+visual+pickscore minus pickscore | 0 | 4 | 6 | -0.667 | [-1.000, -0.250] |
| threeway | qwen+visual+pickscore minus visual+pickscore | 0 | 1 | 6 | -0.167 | [-0.375, +0.000] |

These are paired differences for the same images, not comparisons across regenerated samples. Bootstrap uses 2,000 paired whole-prompt-cluster resamples with seed 904, restricted to surviving parseable families. As in the original, each sampled prompt contributes its mean correctness with equal weight; these intervals describe prompt means, while the point accuracies above use raw image counts. Unequal surviving counts can make those estimands differ. The original has six heldout families; four survive strict parsing here for both tasks. These intervals do not recover the excluded images. Only six original heldout families exist; seeds repeated across families introduce correlation that this bootstrap does not eliminate. Intervals are descriptive and cannot support broad population confidence or hidden-execution proof.

## Stability

12 old IMG002 images ×3 greedy votes. 4/12 images have identical parsed votes on every repeat; 12/12 have byte-identical raw response text. Deterministic repeats establish only run repeatability, not stochastic uncertainty, calibration or judge reliability.

The per-image equality flag in results.json includes null parse outcomes; interpret it together with the parsed count. The parsed-vote repeatability count above requires three valid votes. Per-axis within-image variance and between-image variance are recorded in `results.json`; axes follow `vector_columns`. Repeated votes are never counted as additional identification samples.

## Interpretation and limits

For sd1x, adding Qwen to visual+PickScore changes 1/4 to 2/4 (+0.250); 1 corrects and 0 reversals. This tiny, format-selected subset provides no credible evidence of incremental signal. It is not a new confirmation.
For threeway, adding Qwen to visual+PickScore changes 1/6 to 0/6 (-0.167); 0 corrects and 1 reversals. This tiny, format-selected subset provides no credible evidence of incremental signal. It is not a new confirmation.

SD1.4 vs SD1.5 is primary. Three-way is secondary and can be driven by broad SDXL separation; SDXL native 1024 generation versus SD1.x 512 and other original settings remain confounds despite input normalization. Three shared draws per prompt and six heldout families sharply limit inference. Local Qwen scores do not establish what Nemotron or another reward-trained judge would do. There was no optional quality-overlap analysis, no new threshold tuning, and no alternative model search. Before a new experiment, keep this same model and establish strict schema compliance on calibration-only inputs (for example, constrained output or a prespecified output example). That is a recommendation, not a repair or a second run here. A future confirmation requires a genuinely untouched prompt-family set and a separately prespecified protocol; it must not relabel these images as blind.

## Reproduce and review

From this directory:

```bash
.venv/bin/python analyze.py --verify
.venv/bin/python verify.py
```

`verify.py` is offline and does not load model weights or invoke inference. It validates artifact hashes, strict response parsing, split/seed separation, duplicate images, judge-text leakage, shared baseline provenance when the original is available, and reproduces classification, per-prompt results, confusion matrices, paired changes and bootstrap intervals from saved scores. An independent environment needs the exact numpy/scikit-learn versions in `requirements.lock`, not the full inference stack.

Inference reproduction (local model already present): `.venv/bin/python score.py`. The scorer resumes existing calls rather than duplicating them; use a separately copied experimental directory and remove its prior raw ledger/runtime to repeat. Its original overall hard deadline is retained in source, so change that explicitly for a new reproduction and record the change. No credentials are needed. Download provenance is in `setup.py`; full package versions are in `requirements.lock`.

