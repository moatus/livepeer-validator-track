import pathlib,json,datetime,collections,hashlib,base64
import numpy as np
P=pathlib.Path(__file__).resolve().parent
r=json.loads((P/'results.json').read_text());D=json.loads((P/'frozen-analysis.json').read_text());ids=json.loads((P/'download-identities.json').read_text());proto=json.loads((P/'PROTOCOL.json').read_text());scores=np.load(P/'local-scores.npz');records={x['key']:x for x in [json.loads(f.read_text()) for f in (P/'records').glob('*.json')]}
def pct(x):return f'{100*x:.1f}%'
def table(task):
 lines=['| Feature | Correct / heldout | Accuracy | Prompt-cluster 95% interval | Calibration | Alpha |','|---|---:|---:|---:|---:|---:|']
 for name in ['majority','pickscore','visual','visual+pickscore','pickscore_image_embedding']:
  z=r['results'][task][name]['base'];lo,hi=z['prompt_cluster_ci95'];d=D[task].get(name,{});lines.append(f"| {name} | {z['correct']}/{z['n']} | {pct(z['accuracy'])} | {pct(lo)}–{pct(hi)} | {pct(d['calibration_accuracy']) if d else '—'} | {d.get('alpha','—')} |")
 return '\n'.join(lines)
report=f'''# JUDGE-004: generator identification from score profiles

Run closed {datetime.datetime.now(datetime.timezone.utc).isoformat()}. **Partial experiment: all independent local stages completed; the external-judge hypothesis remains unanswered.** No Nemotron smoke, repeated vote, main judgment, or paid call occurred. Local baselines are measurements, not substitutes for the missing external judge.

Vouch source commit `f400251dcee98eb3add551499af63b83a9323613` was inspected only as measurement precedent; its client/judge fixture snapshots are retained under `precedent-*`. No Vouch product or prior experiment artifacts were edited.

## What was actually tested

216 new real images: 24 authored prompts × 3 independent draws × 3 generators. Exact SD1.4 versus SD1.5 is the primary comparison. SDXL base alone is the secondary broader contrast. One RTX 3090, sequential generators, no model containers, no generator hooks. Split whole semantic families before generation: 12 train / 6 calibration / 6 heldout. Seeds 41001–41003 / 52001–52003 / 63001–63003 are disjoint across splits and paired between SD1.x models using the same CPU FP16 noise. Each split reuses its three-seed list across prompts; this is three noise realizations per split/resolution, not independent noise for every image. There are 36 primary and 54 three-way heldout images, clustered into **only six prompt families**. These sample counts are not large enough for broad attribution claims.

Prompt families are authored task domains; individual families have one prompt here, no paraphrase variants. They are a small convenience probe set, not a random sample of all prompts. Broad skills such as counting and binding occur across splits intentionally; semantic-domain names do not establish universal semantic independence.

## Local results: primary SD1.4 vs SD1.5

{table('sd1x')}

Chance is 50%; majority predicts SD1.4 because training is balanced and ties are lexically fixed. The color/edge-plus-PickScore baseline changes accuracy by {100*(r['results']['sd1x']['visual+pickscore']['base']['accuracy']-r['results']['sd1x']['pickscore']['base']['accuracy']):+.1f} percentage points relative to the PickScore scalar. This comparison is descriptive. **Nemotron-vector added value versus scalar quality or simple output features: not measured.** PickScore is a preference scalar, not a calibrated universal quality measure.

For the close pair, the combined baseline gets just one more heldout image correct than the scalar (22 versus 21 of 36). Its clustered interval is 47.2%–75.0%, including chance. The scalar shows modest above-chance performance on these six probe families, but the embedding adds no improvement and the sample does not establish dependable checkpoint identification.

## Local results: broader SDXL contrast

{table('threeway')}

Chance is 33.3%. SDXL is generated at native 1024 pixels versus SD1.x at matched 512; its architecture, native resolution and configuration are confounded. Normalizing every scorer input to RGB 512 does not remove all generation-resolution effects. A three-way result must not be interpreted as evidence that the difficult SD1.x pair is separable.

The combined three-way baseline gets 35/54 correct versus 31/54 for the scalar: +4 images, or +7.4 percentage points. That is a broader known-generator/configuration distinction, with resolution confounding; it does not rescue the weak close-pair result.

![Heldout local-baseline accuracy](accuracy.png)

## Confusion counts

Rows are true labels and columns are predicted labels in the stated order.
'''
for task in ['sd1x','threeway']:
 report+=f"\n### {task}\n\n"
 for name in ['majority','pickscore','visual','visual+pickscore','pickscore_image_embedding']:
  z=r['results'][task][name]['base'];report+=f"- `{name}`, labels `{z['classes']}`: `{z['confusion']}`\n"
report+='''
## Coverage, failures and safety

| Generator | Scheduled | Saved successful | Black output | Usable for classifiers | Nemotron judgments |
|---|---:|---:|---:|---:|---:|
'''
for c,z in r['coverage'].items():report+=f"| {c} | {z['scheduled']} | {z['successful']} | {z['black']} | {z['usable']} | 0 |\n"
report+='''
All generation attempts have an append-only per-key attempt marker and a terminal record. No warmup generations and no rerolls. Safety flags and black images are retained separately in records. SD1.x standard safety checkers stayed enabled. The standard SDXL base pipeline supplies **no built-in safety checker**; none was removed. Its optional invisible watermarker was explicitly disabled before generation to prevent easy watermark-based identity leakage. These choices are in the prespecified protocol. The single SD1.5 black replacement is calibration prompt p14, draw 2: primary calibration has 35 usable examples and three-way calibration 53. Heldout coverage remains balanced at 36 / 54. Any black/safety replacements are excluded from classifiers, rather than becoming a missingness feature.

## External judge stability: unavailable

| Stage / axis | Planned | Completed | Variance / agreement |
|---|---:|---:|---|
| Existing-image calibration pilot | 12 byte-identical inputs × 3 votes = 36 | 0 | unavailable |
| Object/count, color binding, spatial, typography | fixed applicable requirements | 0 | unavailable |
| Craft / aesthetics | fixed 0–10 axes | 0 | unavailable |
| Main set | 216 judgments | 0 | unavailable |

`stability-manifest.json` binds twelve IMG-002 inputs, prompts and hashes. `stability-inputs/` contains normalized anonymous PNGs. No generator label would enter the judge rubric or upload filename. The selected images are **inputs only**, not measured stability data. There are no raw responses or parsed votes to analyze and no averaging-away of disagreement. Judge-repeat noise, per-axis between-image variation and applicability-mask behavior could not be tested. The proposed rubric schema is prespecified, never empirically calibrated/finalized. Existing pilot families do not enter the heldout main manifest by family name.

### Exact access blocker

`livepeer-roboflow` is absent from PATH; `python3 -m livepeer_roboflow` reports no installed module. The packaged plugin launcher reports `cli_unavailable` because there is no installed package or bundled wheel. No product code was changed to add an adapter.

Read-only unauthenticated MCP discovery at `https://agent.livepeer.org/api/mcp` succeeded. `nemotron-describe.raw` maps the requested `nemotron-omni-vision` to `nvidia/nemotron-3-nano-omni/vision`, with `create_media` as its registered invocation surface. The older Vouch client's `run_capability` path is not registered in the current tool list. The describe card requires `inputs.image_url`; it contains inconsistent source_url/generate/analyze examples, so a validated smoke would also be necessary. No configured user-owned bearer was found in the environment, the absent Storyboard env files, or inspected Codex/Claude MCP settings. The kit's LOC credential is a separate access domain; canonical `GET https://loc.cloudspe.com/v1/capabilities` returned HTTP 404, saved verbatim. It was not repurposed as an Agent/Fal credential.

Discovery advertises **static-registry $0.0063 per 1,000 tokens**, `live_price_usd=null`, and a default maximum of 1,024 output tokens. Uncached `get_pricing` independently returned the same rate with `price_source=static_fallback` (`nemotron-pricing.raw`). It does not establish a current bounded live meter or support for the proposed 256-token/temperature-zero controls. Neither immutable judge weights nor serving runtime is pinned by this alias. No free demo allowance, new account, alternate judge or direct paid provider was used. No upload occurred. Restoring this arm requires an existing user-owned authenticated Agent route plus verified price/token bounds and supported sampling controls, followed by smoke/stability before judging a new untouched main evaluation. The current images have already been used for local analysis, so they must not silently become a new fully blinded pilot.

The attempted status message to supplied parent thread `012384a6-1659-47bb-9d6a-c665e362b160` returned `thread_not_found`; no message was delivered. The blocker was reported in this thread while local work continued.

## Scoring and fitting

Fixed authored requirements map to object/count, color binding, spatial and typography axes, with explicit inapplicable entries. No per-output LLM checklist. The contemplated Nemotron quality scalar is .60 applicable-requirement mean + .25 craft/10 + .15 aesthetics/10, without price, speed or URLs. It was never computed.

PickScore uses the pinned `yuvalkirstain/PickScore_v1` encoder and pinned LAION CLIP-H processor. The saved scalar is `exp(logit_scale) * dot(normalized_image_embedding, normalized_text_embedding)`, before any generator-set softmax. The supplementary raw image-embedding baseline **reuses the PickScore encoder**, so it is not an independent judge. Text embeddings are stored only for audit; no prompt ID or text-only identity classifier is fit.

Simple features are twelve fixed values: RGB means/stds, luminance mean/std, horizontal/vertical absolute luminance differences, saturation-range mean/std. Every scorer sees new metadata-free RGB 512 PNGs. Classifiers receive only explicit numeric feature arrays. Filenames, dimensions, model labels, seeds, prompt IDs, hashes, price, latency and URLs never enter feature arrays. Generator targets and prompt families are used only for labels and partitions.

One ridge classifier family; train-only standardization and coefficients; alpha chosen from [100,10,1,.1] using calibration accuracy with ties favoring 100. Every fit and quality-band boundary was saved to `frozen-analysis.json` before the heldout evaluation. Offline recomputation repeats the identical frozen calculation, never selects a new method. Confidence intervals use 2,000 bootstrap draws of whole heldout prompt families, fixed seed 904, preserving model/draw clustering. They describe uncertainty conditional on this small probe collection and do not cover model/rubric selection, deployment changes, new seed distributions or arbitrary prompts.

## Comparable-preference subset

The central pooled-training PickScore tertile band is intersected with every generator's calibration score range. Bounds are fixed before heldout inspection. This is a cheap preference-overlap check, **not full quality matching or a causal adjustment**. Attrition and counts are reported, not optimized for a favorable result.

| Task | Frozen score interval | Retained / heldout | Per-generator counts | Color/edge + PickScore accuracy |
|---|---|---:|---|---:|
'''
for task in ['sd1x','threeway']:
 z=r['results'][task]['visual+pickscore']['base'];b=z['quality_band'];report+=f"| {task} | {b['bounds'][0]:.3f}–{b['bounds'][1]:.3f} | {b['n']}/{z['n']} | {b['counts']} | {pct(b['accuracy']) if b['accuracy'] is not None else 'unavailable'} |\n"
report+='''
Small retained subsets do not support a claim that quality has been controlled away; consult exact counts. No rejection thresholds or unknown-model experiment was performed. Only these three generators were authorized.

## Cheap robustness checks

No extra generation or hosted calls. The same frozen base classifiers receive local JPEG quality-75 round trips and a 256-pixel downsize/512-pixel upsize. PickScore and simple features are recomputed; the raw base images are untouched. These postprocessing checks are prespecified sensitivity measurements, not fresh independent heldout tests.

| Task / feature | Base | JPEG75 | Resize256 |
|---|---:|---:|---:|
'''
for task in ['sd1x','threeway']:
 for name in ['pickscore','visual','visual+pickscore','pickscore_image_embedding']:
  z=r['results'][task][name];report+=f"| {task} / {name} | {pct(z['base']['accuracy'])} | {pct(z['jpeg75']['accuracy'])} | {pct(z['resize256']['accuracy'])} |\n"
report+='''
![Preference distributions and robustness](robustness-quality.png)

## Within- and between-generator variation

Descriptive all-split summaries below remove the same-prompt mean, then compare within-generator residual mean-square variation with between-generator centroid mean-square variation in train-standardized feature space. They do not tune the classifier or supply independent inferential evidence.

| Task / feature | Within generator | Between centroids | Ratio |
|---|---:|---:|---:|
'''
for task in ['sd1x','threeway']:
 for name,z in r['results'][task]['variation_descriptive_all_splits'].items():report+=f"| {task} / {name} | {z['within_generator_residual_mean_square']:.4f} | {z['between_generator_centroid_mean_square']:.4f} | {z['ratio']:.4f} |\n"
report+='''
## Samples and cost

| Resource | Cap | Used | Accounting |
|---|---:|---:|---|
| New local generator attempts | 216 | 216 | per-attempt markers + terminal records |
| Nemotron calls including retries | 280 | 0 | no inference submissions |
| Hosted estimate | $8 total ceiling | $0 | no uploads / paid operations |
| Hosted actual attributable spend | $8 total ceiling | $0 | no paid operations; no account statement queried |
| Unobservable paid-call settlement | — | none | no paid request existed |

`spend.jsonl` is append-only. Read-only describe/tools discovery is documented as free. Public downloads and local compute are not hosted inference spend; no electricity/disk dollar value is invented. No max-token billing envelope was assumed from a static rate card.

## Exact identities and reproducibility

'''
for key,x in proto['generators'].items():report+=f"- {key}: `{x['repo']}@{x['revision']}`.\n"
for key in ['pickscore','processor']:report+=f"- {key}: `{ids[key]['repo']}@{ids[key]['revision']}`.\n"
report+='''
File-level checkpoint SHA256 identities are in `PROTOCOL.json` (SD1.x), `checkpoint-verification-*.json`, and `download-identities.json` (new downloads). `runtime-*.json` records effective scheduler, safety/watermark configuration, GPU and Torch/CUDA versions. SD1.x file identities were rehashed before loading, using caches read-only. New environments/weights are isolated in this directory. Exact dependency versions are in `requirements.lock`.

Protocol/prompt hashes were frozen before main generation. Exact PickScore/processor download identities and scorer/analysis code hashes were locked in `SCORER-LOCK.json` before any scoring; the original generation protocol recorded scorer repository names before their immutable revisions resolved. Script hashes were first recorded during generation, not falsely presented as a prior code freeze. `generate-sd1x-executed.py` matches the initial generation-code hash; a no-reroll crash-restart guard was added before SDXL. See `code-history.json`. No image generation settings were changed after observing outputs. The required judge-first calibration order could not be fulfilled; independent local stages proceeded under the brief's explicit blocked-route allowance.

Run `verify.py` offline to rehash media, check split/seed/duplicate integrity, enforce explicit feature schemas, validate independent pixel statistics and embedding-dot-product scores, recompute train/calibration decisions and all heldout results, and verify the terminal artifact hash manifest. It makes no provider calls. See `verification.json`, `README.md`, and `RUN-COMMANDS.sh`. The review bundle excludes weights, environments, caches and credentials, and includes representative images rather than all media. Full raw/normalized images remain on disk.

The package installer initially used its default shared uv cache; old venvs and model caches were not modified, but that installer cache may have gained download entries outside this directory. No shared cache files were deleted because concurrent jobs might use them. This is a workspace-containment deviation, recorded in `cleanup.json`. New HF model cache/download paths are inside the experiment directory. No Git commits, publication, product edits, system/driver changes, containers, or remote jobs were performed.

## Limits and conclusion

The primary and secondary local results above apply to these known checkpoints, settings and prompt families only. They do not establish hidden execution, weight identity, unknown-generator rejection, or robustness to adaptive rerolls/fine-tuning. The prior runtime-hook IMG-002 result is a different observation setting and supplies no output-only attribution evidence here. No text KBF/IRIS is applied to images.

The original GenEval framework is optional and was not installed or run; no legacy detector build was attempted. No GenEval/OCR result is claimed.

**The proposed external judge profile's incremental value remains unmeasured because access and billing bounds could not be established.** The completed local baselines, image corpus, immutable identities and reproducible analysis are useful partial results for independent review; they are not a positive or negative Nemotron result.

![Fixed representative heldout outputs, first draw of each family](contact-sheet.jpg)
'''
(P/'REPORT.md').write_text(report)
# Self-contained result preview, a compact table rather than duplicating every report detail.
rows=''
for name in ['pickscore','visual','visual+pickscore','pickscore_image_embedding']:
 a=r['results']['sd1x'][name]['base'];b=r['results']['threeway'][name]['base'];rows+=f'<tr><td>{name}</td><td>{a["correct"]}/{a["n"]} · {pct(a["accuracy"])}</td><td>{b["correct"]}/{b["n"]} · {pct(b["accuracy"])}</td></tr>'
html='''<!doctype html><html><head><meta charset="utf-8"><style>body{font-family:system-ui;color:var(--foreground,#222);margin:0}h2{font-size:19px}p{line-height:1.45}table{width:100%;border-collapse:collapse;font-size:13px}td,th{text-align:left;padding:10px 4px;border-bottom:1px solid #bbb}img{width:100%;height:auto}small{color:var(--muted-foreground,#555)}</style></head><body><h2>JUDGE-004 · local baselines completed</h2><p>216 real images. <b>Nemotron was blocked before any paid call.</b> Its score-profile advantage remains unanswered.</p><table><tr><th>Feature</th><th>SD1.4 vs SD1.5</th><th>Three generators</th></tr>'''+rows+'''</table><p><small>Six heldout prompt families. Chance: 50% / 33.3%. SDXL native resolution/configuration is a confound. The embedding reuses PickScore’s encoder.</small></p><img alt="Accuracy with prompt-cluster intervals" src="data:image/png;base64,'''+base64.b64encode((P/'accuracy.png').read_bytes()).decode()+'''"><p>Nemotron: 0 calls · attributable hosted spend $0 · no public demo credits.</p></body></html>'''
(P/'result.html').write_text(html)
print('REPORT.md and result.html written')
