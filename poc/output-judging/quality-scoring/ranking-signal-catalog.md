# Judge and ranking signals for behavioral model identification

Local research only. Access date for every linked source: **2026-10-25**. No inference, paid calls, installs, deployment, commits, publication, or product changes were performed. This catalog concerns identifying a generator from its behavior; it does not establish execution, independent demand, or economic value.

## Recommendation

**Test judge-derived profiles as additional features, not as identity proofs.** A model may repeatedly fail particular counting, spatial, temporal, or physical-consistency tasks while another equally preferred model succeeds. Those conditional differences could add signal to an existing behavioral fingerprint. A single overall quality score usually discards the information most relevant to that hypothesis. Whether the profiles distinguish *quality-matched* generators, or add anything beyond existing KBF features, remains unverified.

For a small image/video study, prioritize **PickScore v1 raw logits**, **GenEval per-task outcomes**, and **VideoScore2's three separate scores**. These cover preference, structured correctness, and temporal/physical judgments. Run image and video experiments separately. If only one modality is initially available, do not generate another solely to complete the catalog. VisionReward offers richer checklist data but brings heavier dependencies and more calibration work.

Keep Vouch's judge quality component separate from its quality/cost/speed composite. Provider price and latency identify deployment conditions as well as—or instead of—the model. The `nemotron-omni-vision` label alone does not identify immutable weights, a particular NVIDIA release, rubric, sampler, or score calibration. Exact Vouch implementation inspection is a separate workstream.

## What data could be collected?

| Data type | Example record | Potential identity information | Important limitation |
| --- | --- | --- | --- |
| Scalar preference/reward | Prompt, image, raw reward | Conditional preference distribution across task types | Strong quality/style confounding; many models can share it |
| Rubric score vector | Alignment, artifacts, physics | Relative strengths and recurring failures | Judge axes can be correlated or poorly calibrated |
| Checklist/structured correctness | Count correct, left/right correct, OCR exact-match | Fine-grained failure pattern | Detector/OCR errors become part of the measurement |
| Pairwise/listwise decisions | A preferred to B, optional confidence | Relative behavior against stable anchors | Depends on reference candidates, order, ties, and comparison policy |
| Logits/probabilities | Yes/no logits, reward-head logit | Finer distinctions than rounded scores | Not automatically calibrated; access is runtime-specific |
| Embeddings/features | Image/frame/text feature vectors | Style/content/geometry distributions | Similarity represents encoder features, not generator identity |
| Dedicated attribution output | Class probabilities plus unknown rejection | Directly trained identity discrimination | Requires labeled generator data; weak transfer is possible |

These are different tools. A **learned perceptual distance**, such as [LPIPS v0.1](https://github.com/richzhang/PerceptualSimilarity), compares two images using learned features; it needs a reference image and is not a general quality judge. A **reranker** selects relative to candidate alternatives. A **reward/quality judge** estimates a preference or criterion. An **identity classifier** is trained to discriminate generators. Extracting a reward model's embeddings does not convert its training objective into attribution. Paired distances can be useful controls when references have a meaningful relationship; arbitrary reference images primarily introduce content confounding.

## Representative catalog: ten evaluator families

Named versions below are *verified representatives*, not claims that every family is the latest or best available. Untagged repositories and model-card `main` branches remain mutable: pin checkpoint hashes, code commits, processor/config revisions, and dependency versions before measuring. “Local” means runtime can process content without sending it to an inference provider after dependencies/weights are acquired; it is not a completed network or telemetry audit. No defensible per-output monetary price was found in the cited artifacts, and none is invented here. Downloadable weights still incur compute/storage cost.

### 1. General multimodal rubric judge: NVIDIA Nemotron 3.5 Super VL

- **Exact representative:** `nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-BF16`, released October 15, 2026; 120B total/12B active parameters. This newly released model is **not established as Vouch's `nemotron-omni-vision` backend**.
- **Input/output:** Text instructions/rubric plus images or sampled video frames; reference output only if the custom task requires it. Generates text: scores, structured judgments, or pairwise choices require a controlled prompt and parser. No native calibrated generator-identity score is documented.
- **Access/license/status:** Downloadable weights, vLLM/SGLang examples; OpenMDW-1.1. Current card documents BF16 and separate quantized deployment options.
- **Repeatability/blind spots:** Sampling, frame selection, backend, quantization and rubric affect results. General vision capability does not validate grading. Text rendered inside images can influence a prompted judge; counting/OCR and temporal sampling need controls. Local hosting can keep media local; hosted access exposes the supplied content under that provider's terms.

Primary source: [NVIDIA model card and runtime recipes](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-BF16).

### 2. Text-image preference baseline: PickScore v1

- **Identity:** `yuvalkirstain/PickScore_v1`, CLIP-H fine-tuned on Pick-a-Pic. Established 2023 checkpoint; no newer release is asserted.
- **Inputs/data:** Prompt and generated image; no reference image. Card exposes normalized image/text features and scaled dot-product logits. Example converts logits into softmax preferences across the supplied images. Preserve **raw logits**, because probabilities change when candidates change; single-candidate softmax is always 1.
- **Access/license/status:** Local Transformers weights. [Code license](https://github.com/yuvalkirstain/PickScore/blob/main/LICENSE) is MIT; weight/base-model terms require separate confirmation because the card lacks explicit license metadata.
- **Repeatability/blind spots/privacy:** Feed-forward evaluation is easier to stabilize than sampled rubric generation, subject to precision/kernel/preprocessing differences. Example truncates text at 77 tokens. Aesthetic/population preference and training-generator biases may dominate; compositional or OCR correctness is not guaranteed. Local inference needs no content upload.

Primary sources: [model card and scoring implementation](https://huggingface.co/yuvalkirstain/PickScore_v1), [Pick-a-Pic paper](https://arxiv.org/abs/2305.01569).

### 3. Fine-grained preference: VisionReward image/video family

- **Identity:** `THUDM/VisionReward-Image` (and explicit BF16 variant), `THUDM/VisionReward-Video`; CogVLM2-based. Official ImageReward README identifies VisionReward as its successor. Historical `ImageReward-v1.0` remains a simpler prompt/image scalar-and-ranking baseline, not the latest family member.
- **Inputs/data:** Prompt, image/video, checklist questions; binary answers, weighted score, video comparison. Dataset describes 60 image/64 video dimensions. **Do not assume the default score contains every raw dimension:** image script masks selected answers and adds `clip-flant5-xxl` VQAScore alignment.
- **Access/license/status:** Downloadable SAT/CogVLM2 checkpoints. Repository Apache-2.0; **weights use custom CogVLM2 terms**, not that repository license. Image FP32 checkpoint extraction and BF16 variant are documented.
- **Repeatability/blind spots/privacy:** Script exposes temperature .8; record answer-generation policy and auxiliary scorer. Checklist wording, answer parsing, frame sampling and learned weights can change profiles. Human preference is not identity. Local execution is possible, with heavier runtime requirements.

Primary sources: [official repo](https://github.com/zai-org/VisionReward), [image card](https://huggingface.co/THUDM/VisionReward-Image), [video card](https://huggingface.co/THUDM/VisionReward-Video), [actual image scoring script](https://github.com/zai-org/VisionReward/blob/main/inference-image.py), [ImageReward successor notice](https://github.com/zai-org/ImageReward).

### 4. Video reward judge: VideoScore2

- **Identity:** `TIGER-Lab/VideoScore2`, based on Qwen2.5-VL-7B-Instruct; successor to VideoScore v1/v1.1, released in 2025.
- **Inputs/data:** Generated video plus generation prompt; no reference video. Separate visual quality, text-video alignment and physical/common-sense consistency ratings, with generated rationale. Official script parses three integer ratings and also computes custom token-confidence-weighted “soft” values. Those values are **not** demonstrated identity probabilities or standard expected ratings.
- **Access/license/status:** Downloadable Transformers checkpoint, Apache-2.0 card; repository supplies inference/training and OOD preference-evaluation code.
- **Repeatability/blind spots/privacy:** Official inference uses 2 fps, `do_sample=True`, temperature .7 and up to 1,024 new tokens. Repeated grading or a deliberately deterministic modified recipe needs calibration. Sparse frames miss brief defects; rationales may be inaccurate; preference/quality validation is not generator identification. Local operation possible; public demo uploads should not be treated as private.

Primary sources: [checkpoint](https://huggingface.co/TIGER-Lab/VideoScore2), [inference code](https://github.com/TIGER-AI-Lab/VideoScore2/blob/main/vs2_inference.py), [paper](https://arxiv.org/abs/2509.22799).

### 5. Temporal/capability measurement pipeline: VBench series

- **Identity:** VBench original 16-dimension suite; VBench-2.0 adds 18 dimensions across five capability categories; VBench++ supplies additional settings. **A benchmark/pipeline, not one scoring checkpoint.** Original and 2.0 scores are not interchangeable.
- **Inputs/data:** Videos and dimension-specific prompt/metadata; some I2V components also require input images. Individual metric values, per-video records, aggregates and relative model rankings arise from different component models/methods.
- **Access/license/status:** Official repository unifies these variants; Apache-2.0 code with separate dependency/checkpoint terms. README records 2026 I2V arena activity and documents customized-video evaluation.
- **Repeatability/blind spots/privacy:** Pin exact component, preprocessing and sampling. Do not equate a static sharp clip's apparent temporal consistency with useful motion. Full suite is heavier than a small selected-axis experiment. Local component execution can retain video; audit each component for external services. Good capability coverage does not demonstrate individual-output source attribution.

Primary source: [official VBench repository and version overview](https://github.com/Vchitect/VBench).

### 6. Structured prompt alignment: GenEval

- **Identity:** Official GenEval framework, original 2023 task definitions, Mask2Former detector via MMDetection 2.x. **Not a monolithic judge checkpoint.**
- **Inputs/data:** Generated image and structured metadata describing intended objects, count, colors and relations; prompt alone is insufficient for the documented evaluator. Produces per-image `correct` and failure `reason`, and category scores. No reference image. OCR is not a supported axis in this original suite.
- **Access/license/status:** Local code and detector download; MIT framework license, separate detector/dependency terms. Available original benchmark; ongoing release cadence not established.
- **Repeatability/blind spots/privacy:** Fix detector weights, thresholds and image processing. Detector vocabulary and detection failures may masquerade as generator failures, especially stylized or unusual objects. Structured correctness offers a different signal from preference, but category ceilings reduce discriminating power. Local images/metadata need not leave the runtime.

Primary sources: [official README and task/evaluation schema](https://github.com/djghosh13/geneval), [paper](https://arxiv.org/abs/2310.11513).

### 7. Text rubric judge: Prometheus 2, 7B

- **Identity:** `prometheus-eval/prometheus-7b-v2.0`, Mistral-7B-Instruct-v0.2-based. A pinned 2024 representative, not a claim of newest judge.
- **Inputs/data:** Instruction, response, scoring rubric **and reference answer** in documented format; pairwise mode takes two responses. Generates feedback and integer 1–5 score, or A/B preference. Multiple rubrics yield a vector only through multiple controlled evaluations.
- **Access/license/status:** Downloadable Transformers checkpoint; Apache-2.0 card, which additionally discusses generated-training-data terms. Current card still documents both grading formats.
- **Repeatability/blind spots/privacy:** Decode settings, reference quality, prompt wording and candidate position affect judgments. Verbosity/style and prompt injection in assessed text are experimental risks. Reference dependence can leak answer quality rather than identity. Local inference is available; submitting to a remote endpoint shares the evaluated text/reference/rubric.

Primary source: [checkpoint card, required input templates and licensing notes](https://huggingface.co/prometheus-eval/prometheus-7b-v2.0).

### 8. Text scalar reward: Skywork Reward Llama 3.1 8B v0.2

- **Identity:** `Skywork/Skywork-Reward-Llama-3.1-8B-v0.2`, not v0.1. Official card explains v0.2 removes preference-data overlaps with RewardBench.
- **Inputs/data:** Chat-template-formatted conversation plus candidate answer; no reference answer required. Sequence-classification reward logit per answer; compare logits to rank candidates. Not a calibrated correctness or identity probability.
- **Access/license/status:** Downloadable Transformers checkpoint. Card requires the **Skywork Community License** and links its terms; the Llama 3.1 base has separate terms to review. This is an established decontaminated representative, not asserted latest.
- **Repeatability/blind spots/privacy:** Fix tokenizer/chat template/truncation, precision and runtime. Length/style/safety preference effects and benchmark contamination matter. Text can be processed locally. **RewardBench is a benchmark, not the reward model**; its current repository also covers RewardBench 2.

Primary sources: [Skywork v0.2 model card](https://huggingface.co/Skywork/Skywork-Reward-Llama-3.1-8B-v0.2), [official RewardBench repository](https://github.com/allenai/reward-bench).

### 9. Speech naturalness: UTMOSv2

- **Identity:** UTMOSv2 `fusion_stage3` pretrained model, official Python API/repository; newer than UTMOS22. Release page lists v1.3.0 library improvements; package version and model weights are separate identifiers.
- **Inputs/data:** Speech waveform/file and sample rate; no text prompt or clean reference required. Predicted naturalness MOS scalar, utterance/batch records. Domain ID is configurable and affects calibration.
- **Access/license/status:** Local PyTorch package with pretrained weights; MIT code, HF-hosted weights documented. Repository provides inference/training documentation and maintained API releases; verify exact weight terms separately.
- **Repeatability/blind spots/privacy:** Docs describe random waveform-frame selection, repeats and fold averaging. Fix crop indices/seeds, domain, fold and aggregation; measure within-file variance. Naturalness does not establish intelligibility, speaker identity, transcript fidelity or generator identity. Voice/accent/language and recording chain are major potential confounders. Local inference avoids uploading speech; MOS alone is not a privacy guarantee.

Primary sources: [official repository](https://github.com/sarulab-speech/UTMOSv2), [inference/calibration guide](https://github.com/sarulab-speech/UTMOSv2/blob/main/docs/inference.md), [release history](https://github.com/sarulab-speech/UTMOSv2/releases).

### 10. Speech impairment vector: DNSMOS P.835

- **Identity:** Microsoft DNS-Challenge's nonpersonalized DNSMOS P.835, `DNSMOS/DNSMOS/sig_bak_ovr.onnx`; companion P.808 estimator `model_v8.onnx`. Personalized DNSMOS is a different mode and should not be mixed in.
- **Inputs/data:** Speech audio; local script resamples to 16 kHz. No clean reference or transcript. Raw and calibrated signal (`SIG`), background (`BAK`), overall (`OVRL`) scores, plus P.808 MOS; segmented and averaged measurements.
- **Access/license/status:** Downloadable ONNX models and local ONNX Runtime script. Repo has MIT code license and CC-BY-4.0 general license; checkpoint-specific application should be confirmed. Available established noise-suppression metric; newest model release status not verified.
- **Repeatability/blind spots/privacy:** Fix resampling, windows, ONNX provider and calibration mode. Noise/background and channel conditions can dominate any generator signal. Noise-suppression quality is not a transcript intelligibility measurement. Local inference avoids service upload; vector still reveals properties of audio/content.

Primary sources: [official DNSMOS README](https://github.com/microsoft/DNS-Challenge/blob/master/DNSMOS/README.md), [local inference and checkpoint paths](https://github.com/microsoft/DNS-Challenge/blob/master/DNSMOS/dnsmos_local.py), [license separation](https://github.com/microsoft/DNS-Challenge).

## What is supported by literature, and what is the hypothesis?

The cited preference/judge papers evaluate human agreement, quality/alignment, capability ranking, or reward-guided selection. GenEval and VBench expose differences between known generators' aggregate capabilities. **That is not an experiment identifying an unknown generator from judge-score profiles.** This bounded scan did not find direct evidence that combining these particular judges yields reliable source identification after matching quality, style and content, or improves KBF. This is a search limitation, not proof that no such literature exists.

Generator attribution itself has primary evidence: [Yu et al., ICCV 2019](https://openaccess.thecvf.com/content_ICCV_2019/papers/Yu_Attributing_Fake_Images_to_GANs_Learning_and_Analyzing_GAN_Fingerprints_ICCV_2019_paper.pdf) trains fingerprints for GAN attribution, including fine-grained training differences. Its learned attribution representation is not an off-the-shelf human-preference score; results on those GANs do not establish modern diffusion/video attribution. Proactive fingerprint/watermark work is a further distinct category requiring generator modification and should not be counted as passive judge evidence.

**Quality-matched generators can plausibly be separated only if their task-conditional profiles differ beyond scorer noise.** Equal average reward does not mean equal vectors, but equal vectors remain possible. Preference models trained on similar data/encoders can strongly correlate, making several scores look like independent evidence when they are not. A rich judge can also erase source artifacts by focusing on semantic quality. Both positive and null outcomes are informative.

## Small next test: proposed design, not performed

1. **Freeze measurement.** Choose exact checkpoint/code/processor revisions, task schema, score extraction, preprocessing, frame/crop policy, precision and decoding. Preserve raw score dimensions and parse failures. For VideoScore2 compare the documented stochastic recipe's repeatability with a separately calibrated deterministic recipe; do not silently change it and reuse published calibration claims.
2. **Measure judge noise first.** Regrade identical existing outputs. If within-output variance approaches between-model differences, stop or simplify. Record variance separately from generator seed variation.
3. **Use a small balanced battery.** Proposed starting point: 24–40 image prompts across counting, spatial binding, typography and ordinary scenes, with 3–4 outputs/model/prompt; independently, 12–20 short-video prompts spanning ordinary motion and physical interaction, with 3 outputs/model/prompt. These are illustrative planning counts, not a power calculation or an authorization to incur costs. Use existing outputs when available.
4. **Top three measurements.** PickScore raw logits provide a scalar preference baseline; GenEval provides structured image failure profiles; VideoScore2 provides three video axes. Add an explicit OCR engine plus exact-match/character-error rule for typography only after choosing and pinning that separate implementation—GenEval does not supply it. VisionReward's checklist is the richer follow-up if simple profiles show signal. Prometheus/Skywork are adjacent text controls; UTMOSv2/DNSMOS are adjacent speech controls, with ASR/reference-transcript error measurement needed for intelligibility.
5. **Test independence.** Compare existing KBF alone, judge features alone, and their combination, plus a simple average-quality baseline. Evaluate within quality bands or controlled matched subsets. Fit any normalization/feature selection on training data only. Report pairwise score correlation and incremental held-out accuracy/calibration; no assumed multiplication of likelihoods from correlated judges.
6. **Hold out tasks and generators.** Split by prompt family and seed so siblings do not cross train/test. Hold out a generator entirely to test unknown refusal. Evaluate model revisions/fine-tunes separately where labels allow. Keep one generator's outputs from each source/provider treatment balanced to prevent routing artifacts from becoming the label.
7. **Report distributions.** Include confusion matrix, per-family separation, judge repeatability, confidence intervals with prompts as the resampling unit, false attribution/unknown rejection, and any quality-matching failures. Represent identity as a calibrated distribution over hypotheses with an unknown option, not one “identity number.” Pairwise tests require fixed anchors, reversed candidate order, and explicit ties.

Privacy applies throughout: sending only a final scalar to a validator does not mean the scorer never saw the original media/prompt, nor that the scalar is private. Scores, vectors, rationales and embeddings may reveal content or permit inference; rationales can quote it. Keep local raw outputs and provenance separate from any eventual disclosure policy. No retention or confidentiality guarantee was verified for public demos or hosted providers.

## Unverified gaps

- Exact Vouch backend identity, revision, prompt, frame sampling, response parsing and score mixture require its code/config review; the NVIDIA representative above is not a substitution claim.
- No current hosted prices, throughput, GPU-hour estimate, inference benchmark, weight download, or local runtime validation was obtained.
- Some licenses are clear at code level but incomplete or different at weight level, explicitly marked above. This catalog is not a deployment/legal clearance.
- No implementation SHA manifest was generated, because no experiment is being run. Mutable linked sources must be pinned when selecting the actual battery.
- No claim of generator identification performance, tamper resistance, privacy preservation, or additional independent KBF evidence is established by this research.
