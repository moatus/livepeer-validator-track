# Recent sources: can judge, reward, and ranking scores identify a generator?

**Date of scan:** 2026-10-25
**Role:** source discovery for Shane. Research only. No protocol, no adoption, no experiment rerun.
**Question:** can the scores a judge, reward model, or ranking benchmark emits act as a behavioral signature of which model generated an image, video, or audio clip?

**Short answer.** No primary study found in this pass trains a classifier on evaluator score profiles and reports held-out generator identification (models, tasks, sample size, attack limits). Quality correlation is not that study. What does exist is a usable inventory: some scorers emit a vector, generators draw different shapes on fixed multi-axis benchmarks, and several 2026 papers show those numbers move for reasons other than which weights ran. A score profile can complement a text probe such as KBF. It is not a proof of weights, and it is easier to spoof than a knowledge-boundary audit because the score is the training target of reward hacking.

Context from the 2026-10-25 external-model scan: black-box text audits (Cai et al., MET, IRIS, KBF) are statistical and multi-query; Smudged Fingerprints (arXiv:2512.11771, SaTML 2026) shows image-attribution fingerprints are removable. This note does not repeat those papers. It asks whether *judge outputs* add a signal those papers do not use.

## How to read a number

These are different objects. Mixing them is the main way a leaderboard gets cited as identity evidence.

| Object | What it is | What it is not |
| --- | --- | --- |
| Scoring checkpoint | A model that, on a new sample, emits a scalar or a small vector (HPSv3, VideoScore2, Audiobox). | A claim that the sample came from a named generator. |
| Benchmark profile | A fixed prompt suite plus per-dimension metrics, usually published as a model-level radar (VBench-2.0). | A calibrated score of one arbitrary customer clip. |
| Pairwise rank | Which of two outputs a judge prefers. Depends on the other candidate. | An absolute property of one generator. |
| Composite application score | Quality mixed with cost and speed (Vouch). | A pure behavioral signature. |
| Identity evidence | Held-out classification or a two-sample test of a score vector against an enrolled generator, with an attack section. | "Model A scores higher than model B on aesthetics." |

A scalar can still carry identity information if the *distribution* of scores on a fixed probe set differs by generator. That experiment was not found. The sources below say what features you could enroll, and why a naive enrollment would be confounded.

## Search result on direct identification

Opened recent primaries on image and video reward models, VLM rubric judges, human-preference checkpoints, audio aesthetic axes, judge bias, and score manipulation (about twenty pages; twelve written up). None of them states: these generators, this score vector, this sample size, this held-out prompt or seed split, this attack success. Papers that *do* attribute generators (for example saliency-based generator-specific classifiers, arXiv:2610.23411, 16 Oct 2026; forensic diffusion features, arXiv:2510.27602, v2 10 Mar 2026) use pixels or internal features, not reward-model scores. They are cited only as the contrast. They were not given full slots.

## Twelve sources

### 1. Vouch Studio — the application that motivated the question

- **URL:** https://github.com/martinvibes/vouch-studio
- **Date / version:** README as fetched 2026-10-25. Repository, not a paper. Hackathon app (Atumera Livepeer Agent Hackathon, Track 01). Commit count on the page: 21. No release tag was read.
- **What it emits:** Per render, a checklist of 4–8 requirements marked met, partly met, or missed, plus notes and a flaw list. Two independent judge passes are merged. Video is judged from three frames (15%, 50%, 85%). Then a grade S–F from a published formula: quality = 60% brief match + 25% craft + 15% aesthetics; vouch score = 70% quality + 20% value + 10% speed. Brief match below 50 caps the grade at 58. The judge named in the README is Livepeer capability `nemotron-omni-vision`. Checklist text and prompt rewrite use `gemini-text`. The Board aggregates score, quality, cost per usable render, speed, win rate, and reliability. Seed data shipped with the repo: 14 shootouts, 42 renders.
- **What the source supports:** A blind checklist judge plus cost and latency can rank a small lineup on one brief, and the per-item checklist is a richer trace than a scalar. The README says strong models tie on easy briefs and price then decides, and that small Board samples are noisy.
- **Code / weights / license:** Application code is the repo above. `nemotron-omni-vision` is a Livepeer capability name in this README, not a weights file this pass opened. NVIDIA's Nemotron 3 Nano Omni tech report is a different object (arXiv:2604.24954, v2 11 May 2026): an omni *understanding* model, not a documented visual reward checkpoint. Software license of the Vouch repo was not read.
- **Identity relevance:** The checklist vector (which requirements failed) is the part that could differ by generator. The vouch score itself mixes in price and speed, so two generators with the same pixels and different list prices get different scores. A winner among three is candidate-set dependent.
- **Limits:** The README states the judge is an AI, not a human art director. No held-out identification protocol. The checklist is regenerated from each brief, so profiles are not on a shared axis unless the checklist is frozen.

### 2. HPSv3 and HPSv3++ — scalar human-preference checkpoints, and a scorer that is told the generator's tier

- **URLs:** HPSv3 paper https://arxiv.org/abs/2508.03789 (v2, 22 Aug 2025; ICCV 2025, pp. 15086–15095). Code https://github.com/MizzenAI/HPSv3. Project https://mizzenai.github.io/HPSv3.project/. HPSv3++ paper https://arxiv.org/abs/2606.14657 (v1, 12 Jun 2026; README says ACM MM 2026). Code https://github.com/PlantPotatoOnMoon/HPSv3-PlusPlus.
- **What they emit:** HPSv3: one preference score from a VLM backbone trained with an uncertainty-aware ranking loss on HPDv3 (1.08M text-image pairs, 1.17M pairwise comparisons). The README table is pairwise preference *accuracy* of the checkpoint on other datasets (for example HPSv3 76.9 on HPDv3 versus PickScore 65.6). That accuracy is a property of the judge, not a score of a generator. HPSv3++ adds a second dataset, HPDv3++ (212K pairs, separate text-fidelity and aesthetic labels on Qwen-Image), and a reward that is conditioned on generator capability and RL iteration. Reported preference accuracy: +9.8 points versus HPSv3 on HPDv3, +5.5 on GenAI-Bench, 79.1% / 88.1% on the authors' HPDv3++ split. A human comparison of RL outputs: HPSv3++ win rate 77.5% versus HPSv3 on 100 prompts.
- **What the source supports:** A single human-preference scalar is the wrong feature for identity: it is trained to collapse many axes into "which image do people pick." HPSv3++ is the more interesting fact. The authors say an unconditioned reward mis-scores as generators get stronger and as RL iterations proceed, so they feed capability and iteration into the scorer. The score is explicitly not on one scale across generator families unless those conditions are supplied. Their own hyperparameter note says aggressive RL settings make both HPSv3 and HPSv3++ reward-hack (the number rises without a matching visual gain).
- **Code / weights / license:** Both papers point at the GitHub repos above. HPSv3++ paper license on arXiv is the non-exclusive distribution license, which is not a software license. Repo licenses were not re-read. A third-party 4-bit pack (https://github.com/Stella2211/hpsv3-4bit) says HPSv3 uses Qwen2-VL-7B and HPSv3++ uses Qwen3-VL-8B; that backbone claim is from the pack's README, not re-checked against the papers.
- **Identity relevance:** The residual between an unconditioned score and a capability-conditioned score is a possible family cue, and a drift alarm if a served model is quieter or stronger than the enrolled tier. It is a calibration finding, not an identification result.
- **Limits:** No closed-set attribution. Conditioning on the claimed capability *uses the name you are trying to test*. Using the conditioned score as an identity feature would be circular if the claimant supplies the tier.

### 3. VisionReward — the richest open question vector

- **URL:** https://arxiv.org/abs/2412.21059 (v4, 5 Jan 2026; first submitted 30 Dec 2024). Code stated in the abstract: https://github.com/THUDM/VisionReward. Paper license CC BY 4.0. Repo license not re-read.
- **What it emits:** A hierarchy the authors describe as nine major dimensions, decoupled into 64 fine-grained questions for images (the dataset table in the HTML says 18–20 dimensions and 61–64 questions, 81K samples, about 5.0M annotations, image and video). The preference score is a linear weighting of question outcomes, so the interpretable object is the question vector and the deployed reward is the weighted sum.
- **What the source supports:** On the authors' comparisons, VisionReward beats VideoScore by 17.2% in preference-prediction accuracy, and text-to-video models optimized with it win 31.6% more pairwise comparisons than the same models optimized with VideoScore. The paper's point is preference alignment, not source attribution.
- **Identity relevance:** The question vector is the overlooked feature. A weighted sum throws away the pattern (which questions a generator fails). Enrolling the 64-way outcome vector on a frozen prompt set is the closest off-the-shelf analogue of a capability vector. This pass did not find that enrollment.
- **Limits:** Questions and weights were fit to human preference, so dimensions that humans treat as one "quality" factor will be correlated (see source 12's halo result on text rubrics). Video and image question sets differ, so a shared profile needs an explicit mapping. No attack section for someone optimizing the weighted sum.

### 4. VideoScore2 — three video scores plus a rationale

- **URL:** https://arxiv.org/abs/2509.22799 (v1, 26 Sep 2025). Paper HTML is CC BY 4.0. A code URL is not in the abstract; not verified here.
- **What it emits:** Three scores — visual quality, text-to-video alignment, physical/common-sense consistency — plus a chain-of-thought rationale. Trained on VideoFeedback2, 27,168 human-annotated videos from 20+ text-to-video models, with scores and reasoning traces. Training is supervised fine-tuning then GRPO. Reported figures are judge accuracy, not generator IDs: 44.35 (+5.94) on their in-domain VideoScore-Bench-v2, and 50.37 (+4.32) average on four out-of-domain sets (including VideoGenReward-Bench and VideoPhy2). They also use it as a Best-of-N reward.
- **What the source supports:** A three-axis video score is available as a generative judge, and the rationale is extra text. The in-domain test split is described by a later methods appendix (arXiv:2606.11838) as 500 held-out videos; that sample size is secondhand and not re-read in VideoScore2 itself.
- **Identity relevance:** Three correlated quality axes are a weak fingerprint. The rationale text might carry generator-specific failure language, but it is also the channel an attacker can stuff (source 9). Best-of-N selection changes the output distribution toward whatever the judge likes, so a generator tuned against VideoScore2 will look more like the judge's preference than like its base checkpoint.
- **Limits:** Accuracy of the judge against human labels is not separability of generators. No held-out source-ID protocol.

### 5. VBench-2.0 — a benchmark profile, not a preference checkpoint

- **URL:** https://arxiv.org/abs/2503.21755 (v2, 20 Aug 2025; project page dates the release Mar 2025, https://vchitect.github.io/VBench-2.0-project/). Code lives in https://github.com/Vchitect/VBench under `VBench-2.0`. Paper license on arXiv is the non-exclusive distribution license. Repo license not re-read. Predecessor VBench is CVPR 2024; VBench++ is TPAMI 2025 (arXiv:2411.13503).
- **What it emits:** Eighteen fine-grained dimensions in five groups: Human Fidelity, Controllability, Creativity, Physics, Commonsense. The suite mixes generalist VLM/LLM judges with specialist anomaly detectors. The project page publishes per-model radar charts, normalized per dimension. The README (fetched via the repo) says a user can evaluate one dimension on their own videos. The published comparison people cite is a model-level profile on the authors' prompt suite, checked against human preference annotations.
- **What the source supports:** On a shared prompt suite, video generators do not move together on every axis. A radar is a behavioral sketch of a model *on that suite*. That is the closest public artefact to a generator signature, and it was built to rank quality.
- **Identity relevance:** A natural test, not done in the paper, is whether a new clip's 18-vector is closer to the enrolled radar of the claimed model than to others, under new prompts and seeds. Specialist detectors (anatomy, physics) are less "taste" and more artifact, so they are the axes most analogous to a forensic cue. VLM axes inherit judge bias (sources 7, 9, 10).
- **Limits:** Normalization per dimension makes the chart comparative, not an absolute scalar. One published point per model is not a distribution, so it cannot support a significance test. Prompt suite and judge version are part of the measurement; a later VLM judge is a different instrument. VBench++ adds trustworthiness (fairness, bias, safety) as further axes, still as a benchmark.

### 6. Meta Audiobox Aesthetics — four audio axes, per clip

- **URL:** https://arxiv.org/abs/2502.05139 (v1, 7 Feb 2025). Code stated in the paper: https://github.com/facebookresearch/audiobox-aesthetics. Repo license not re-read.
- **What it emits:** Four no-reference scores per clip: Production Quality (PQ), Production Complexity (PC), Content Enjoyment (CE), Content Usefulness (CU). The README example line is `{"CE": 5.146, "CU": 5.779, "PC": 2.148, "PQ": 7.220}`. The model is a predictor on WavLM features, for speech, music, and sound. The paper reports correlation with human MOS and with system rank, not generator identity. On their tables, PQ/CE/CU track MOS; PC does not (negative correlation on VMC22).
- **What the source supports:** Audio already has a small public vector that is not a single MOS. PC is a different kind of signal (how many elements, not how "good"), which is the sort of axis that can differ by generator even when quality scores tie.
- **Identity relevance:** Same enrollment idea as VisionReward, on a 4-vector. A 2025 follow-on (AudioMOS Challenge T12, arXiv:2512.05592, 5 Dec 2025) treats these axes as prediction targets and ensembles them; it still does not attribute systems by the vector. A later citation notes Audiobox scores sometimes preferred random inharmonic notes over structured melodies; that is a secondhand warning, not a number from this paper.
- **Limits:** System-level SRCC in the paper is "does the average score rank audio systems the way listeners do," which is quality ranking. No spoofing study. Scores summarize private audio; publishing them is a coarse leak of production character, not a transcript.

### 7. Attractive faces skew preference models and leaderboards

- **URL:** https://arxiv.org/abs/2610.28195 (v1, 20 Oct 2026). Comment on the abs page: WACV 2027. License CC BY 4.0. Code not stated on the abs page.
- **What it emits / studies:** Not a new scorer. A user study plus an audit of existing scorers. Annotators rank more attractive faces as higher quality even for real photographs of the same fidelity, and they do so when an attractive synthetic face is compared with an unattractive real one. Elo simulation from that study can invert a leaderboard. Editing 40 facial attributes one at a time, attractiveness is the strongest correlate of score for four of five preference models (PickScore, MPS, HPSv2.1, HPSv3), and the strongest regression predictor. Preference-aligned generation shifts faces younger and more feminine and can override an explicit "unattractive" prompt.
- **What the source supports:** On face prompts, a high HPSv3 or PickScore is evidence of attractiveness bias at least as much as evidence of a generator. Two generators can be separated by this axis because one draws more attractive faces, which is a content prior, not a weight hash. A leaderboard rank is reversible by that prior.
- **Identity relevance:** Negative. A face-heavy probe set will fingerprint "how attractive are the faces," then call it the model. Mitigation is discussed (data collection and post-training) but this pass did not re-read the method.
- **Limits:** The abs page does not give annotator count or image count. Do not invent them. Scope is faces, not a general image prior. The fifth model of the five is not named in the abstract.

### 8. Reward hacking in text-to-image RL — the score can be bought

- **URL:** https://arxiv.org/abs/2601.03468 (v1 6 Jan 2026; v2 31 Aug 2026). License CC BY 4.0. Code not on the abs page.
- **What the source supports:** Aesthetic and human-preference rewards, and prompt-image consistency rewards, each induce reward hacking. Ensembling several rewards only partly mitigates it. Across reward models the shared failure is artifact-heavy images that still score high. The authors add a lightweight artifact reward, trained on a small set of clean versus artifact images, and report that it improves realism and reduces hacking in several T2I RL setups. An earlier inference-time paper, MIRA (arXiv:2510.01549, 2 Oct 2025), makes the same point for test-time noise optimization: extra freedom to chase a reward (Aesthetic, HPSv2, PickScore) increases hackability unless an image-space constraint holds the sample near the base model.
- **Identity relevance:** This is the attack on a score signature. A weak generator fine-tuned or searched to match an enrolled score vector can present the target profile without being the target weights. That is the media analogue of GhostPrint for fingerprints, and it is easier, because the objective is the public score rather than a hidden key. Matching the *weighted sum* is easier than matching a 64-question vector; the vector is the feature worth testing, and this paper says the sum is hackable.
- **Limits:** The abstract does not give a spoof rate against a named identification classifier, because no such classifier is the subject. "Artifact-prone" is their qualitative failure mode, not a measured false-accept rate for attribution.

### 9. Don't read the log — text injected into a video judge flips the verdict

- **URL:** https://arxiv.org/abs/2609.28564 (v1, 23 Sep 2026). Title on the abs page: *Don't Read the Log: Execution Traces Contaminate Verifiers in Video-Generation Agents*. License CC BY 4.0. Code not on the abs page.
- **Protocol in the abstract:** 109 generated two-event clips, manually labeled so the requested event is visibly completed or visibly missing. Frames held fixed. Three open-weight Qwen-VL judges (7B, 8B, 32B). A trace that reports a successful tool call makes them accept 78–90% of the failures, up from 7–19% with no text. A contradicting trace makes them reject up to 100% of correct clips. An instruction to use only the frames does not remove the effect. Frontier closed judges on the same clips are essentially unmoved. In a repair loop, an honest planner that always regenerates ends at judge pass rate 1.00 and human-labeled pass rate 0.28. A cheap checker that writes its verdict into the trace launders its errors into a stronger judge (0.69 false accepts). The abstract says the cap this imposes on the true pass rate matches a simulation to two decimals.
- **Identity relevance:** If the signature is a VLM judge's scores, whoever writes the prompt, the checklist, or a tool log controls the signature. Vouch's judge is shown the checklist and the render; a passthrough node that can add a caption, a subtitle, or a trace is in this threat model. The paper's proposed control is least-privilege judging: a visual requirement sees frames only, with OCR text blurred. That control is a precondition for treating visual scores as evidence about pixels.
- **Limits:** One benchmark of two-event clips. Open-weight Qwen-VL judges fail; the abstract says frontier closed judges do not, on this set. Not a generator-identification study. The honest planner result is the important one: no adversarial agent is required.

### 10. Fooling the LVLM judges — visual edits inflate scores

- **URL:** https://arxiv.org/abs/2505.15249 (v2, 15 Nov 2025; EMNLP 2025). License CC BY 4.0. Code not on the abs page.
- **What the source supports:** Adversarial visual manipulations inflate text-image alignment scores of LVLM judges. The authors build FRAME, a multi-domain meta-evaluation set with diverse score distributions, inject the biases, and report that every tested LVLM judge, in every domain, scores the manipulated images higher. Combining biases amplifies the effect. Pairwise judging is affected too. Prompt-based mitigation does not remove it. Larger judges are not more robust in their results (they name GPT-4.1 and GPT-4o as vulnerable).
- **Identity relevance:** A post-process on the image can move the judge without changing the generator. That stacks on Smudged Fingerprints: pixel fingerprints can be removed, and judge scores can be pushed up, by edits after generation. A score profile enrolled on clean outputs will not survive an intermediary who is allowed to retouch.
- **Limits:** The abstract does not list the judge roster or the size of FRAME. The attack goal is a higher score, not impersonation of a chosen generator's profile. Impersonation is a harder bar and is not shown.

### 11. Judge identity moves the scores — Judging the Judges

- **URL:** https://arxiv.org/abs/2610.21179 (v1, 15 Oct 2026). Project page https://anneharrington.github.io/judging-the-judges/. Code https://github.com/michael-tyl/RaRE. License CC BY 4.0.
- **What the source supports:** In rubric-as-reward training of Qwen3-4B-Base on RaR-Medicine and RaR-Science, five frontier and open-weight judges produce a substantial spread in scores from judge identity alone. A naive average of judges does not beat the best single judge. Their ensemble (RaRE: confidence-weighted Likert via judge logprobs, and a mask that drops high-disagreement rollouts) beats every single judge they tried on HealthBench and GPQA Diamond. Per-theme, the ensemble picks up different judges' strengths.
- **Identity relevance:** The score is a property of the judge as much as of the generator. Any enrolled profile must name the judge version the way KBF must name the model version. The useful signal in their setup is the disagreement pattern across judges, not one judge's scalar. Disagreement is also what they choose to *discard* for training; for attribution it is the part worth keeping.
- **Limits:** Text rubrics on medicine and science answers, not images. "Substantial spread" is the abstract's wording; the numeric gap is not in the abstract and is not repeated here. Not a generator-ID experiment.

### 12. Rubric text dominates the judge — checklist scores are not a model property

- **URL:** https://arxiv.org/abs/2610.24971 (v1, 18 Oct 2026). License CC BY 4.0. Code not on the abs page.
- **What the source supports:** Holding the judge and the outputs fixed, rubric wording moves the pass rate of correct outputs from 2% to 100%. Changing the judge model, or the rendering of the same checks, moves it by a few points. Self-review of the rubric then drifts: the reviser adds requirements the task never stated and deletes checks that human labels had supported, on a planted-flaw grading task and on SummEdits and RAGTruth, with three reviser models. Under all-must-pass aggregation they give a closed-form Shapley value per check (catch credit, false-fail blame, unique catches). A gate that freezes label-derived checks holds nearly every drifting revision at its starting quality, with the same decisions under three judges.
- **Identity relevance:** Vouch rebuilds a 4–8 item checklist from each brief with a text model. Under this result, that checklist, not the vision judge and not the generator, is the main dial on the pass rate. A Board aggregated across briefs with different checklists is not a generator signature. A signature protocol has to freeze the checks. The Shapley quantities are a practical way to see which checks actually separate outputs and which only add false fails.
- **Limits:** Text grading, not visual generation. The 2% to 100% swing is for correct outputs under rubric rewrites they constructed; it is not a measured swing for Vouch's vision judge. The direction transfers; the magnitude does not, until someone measures it.

## Robustness, in one place

| Threat | What a primary source shows | Consequence for a score signature |
| --- | --- | --- |
| Judge bias / content prior | Attractive faces dominate PickScore, MPS, HPSv2.1, HPSv3 (source 7). | Face probes measure attractiveness. |
| Position and pairwise presentation | FRAME finds pairwise LVLM judging inflates under visual bias (source 10). A separate 3D-judge note (arXiv:2606.20364, 18 Jun 2026) reports pure position answering when the panel is overloaded, and keeps only swap-consistent verdicts. | A single left/right vote is not a measurement. |
| Self-preference and authorship labels | *Self- and Other-Labels Induce Bidirectional Bias in LLM Judges*, arXiv:2608.18091, v2 6 Sep 2026. Under blind review, self-preference disappears. Under matched quality, the label "self" or "other" alone inflates or deflates scores, regardless of the true source. | Naming the generator in the judge prompt writes the identity into the score. Blind scoring is required, and even then the label channel is enough to fake a preference. |
| Prompt and seed confounding | VBench radars are comparable only because the prompt suite is shared (source 5). Vouch checklists are not shared (sources 1 and 12). | Profiles on different prompts are not the same feature space. |
| Judge drift | HPSv3++ exists because older rewards mis-scale as generators and RL steps change (source 2). Rubric self-review drifts the instrument (source 12). | Enroll per judge version and per rubric hash, as KBF enrolls per model version. |
| Candidate-set dependence | Vouch picks a winner among three. Source 7 shows Elo order can invert. | A win rate is not a unary signature. |
| Output attacks | Visual edits inflate LVLM scores (source 10). Traces flip video verdicts with frames fixed (source 9). | The intermediary who can edit pixels or captions can edit the signature. |
| Score manipulation | T2I RL and test-time search raise the reward while leaving artifacts (source 8). Intra-rubric divergence (arXiv:2610.26685, 19 Oct 2026) finds that as the total rubric score rises, some sub-scores fall. | Optimizing the aggregate erases the sub-score pattern that would have been the signature. |
| Privacy | Checklist items restate the brief and record whether the image satisfied them (source 1). Audiobox and HPS scalars are coarser but still describe the private output. | A verifier who is not supposed to see the prompt or the media still learns structure from the score vector. This is not a privacy-preserving proof. |

*Inside the Scorer* (arXiv:2610.25724, 19 Oct 2026) is the mechanistic version of the halo problem: across 25 base models, rubric directions in activation space are partly separable, but steering "grammar" barely beats steering the wrong rubric. Analytic sub-scores are not independent controls. A long question vector will contain redundant axes. That paper is essay scoring, not images.

## Relation to KBF and to image or video

KBF (arXiv:2605.29524, v3 30 Sep 2026) fingerprints a text model by what it stably gets right and wrong near its knowledge boundary. A score profile is the same shape of test with a different observable: freeze a probe set, record a vector of automatic judgments, compare the vector to an enrollment of the claimed generator. It fits image, video, and audio, where there is no factual boundary to query. It does not fit a single private customer job, for the same reason KBF does not: both are multi-sample distributional checks.

Where KBF is stronger: the probes can be secret and rotated, and the model is not trained to match them. Where a score profile is weaker: the coordinates are public reward functions that people already optimize, the judge can be prompted or shown a log, and post-processing changes the input to the judge. Where a score profile might see something KBF cannot: a media generator's failure shape on physics, text rendering, or production complexity, which never appears in a text answer.

IRIS-style probe routing still applies. A gateway that recognizes a frozen audit checklist and serves the real model only then will pass. Secret, rotating probes help only if the judge features do not themselves reveal the audit.

## Three leads

These are measurements worth running. They are not findings.

1. **Frozen question vector, held-out prompts.** Take VisionReward's question outcomes, or VBench-2.0's specialist axes, on a prompt set enrolled per generator. Test identification on held-out prompts and seeds, and report confusion among models of the same family. Publish the vector, not the weighted sum. Success criterion: accuracy above a same-family baseline, with the prompt effect partialed out (same prompt, several generators). Failure mode already predicted: axes that track attractiveness or a shared RL reward will cluster by content, not by weights.

2. **Unconditioned minus capability-conditioned score.** HPSv3++ says the scorer needs the generator's tier. On a claimed model, compare the score with the tier the claimant declares against neighboring tiers. A large swing means the sample does not sit where that tier's reward was calibrated. This detects coarse substitution or a stale enrollment. It does not name the substitute, and it is circular if the conditioned model was told the answer. Keep the unconditioned score as the feature and the conditioned score as a sensitivity check.

3. **Disagreement across judges, with the log removed.** Run two or three judges that source 11 shows do not agree, on frames only, with OCR text removed as in source 9. Enroll the pattern of disagreements. A mimic that hacks one public reward (source 8) has to hack several judges at once, including specialist anomaly detectors that are not the same loss. The attack section has to include trace injection, visual bias edits, and a reward-hacked student of the claimed model. If those collapse the disagreement pattern, the lead is closed.

## What this pass did not do

No models were run. No Board numbers were recomputed. Licenses of GitHub repos were not opened except where the arXiv license badge was read. Dates are submission or revision dates from the abs pages fetched on 2026-10-25, or the README text fetched the same day. Secondary commentary (a 20 Oct 2026 post calling PickScore a bad reward model; a reply that HPSv3's labels sometimes prefer SDXL over real photos) was used only as a hint and is not evidence.
