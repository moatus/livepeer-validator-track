# JOB-003 — artifact-only prompt/job consistency

Completed on smart@smart-nv, NVIDIA RTX 3090. Held-out: **0/60 correct-run false rejections**, **0/40 close-prompt false acceptances**, **0/40 distant-prompt false acceptances**. Reload false rejections: **0/6**. These are correlated observations from ten unseen families and two reused held-out noise realizations, not independent population reliability estimates.

The artifact-only numerical verifier can reject these genuine wrong-prompt measurements against privately generated per-job references without receiving prompt or output content. This is empirical job consistency under a trusted reference/collector boundary. It is not verification from a prompt hash alone and does not prove execution, freshness, causality or prompt-injection prevention.

## Frozen design and observed numerical results

Fifteen benign hand-authored prompt families, each with base A, close change B and distant C. Five complete families are calibration, ten are held out. Each split reuses two seeds (5101/5202 versus 6303/6404): four main noise realizations total. Every A/B/C job has a real trusted reference and an independent full candidate generation. A↔B close swaps and A↔C distant swaps are predeclared, same seed/settings. All family variants stay in one split. Twelve extra fresh-process/model-reload generations cover ABC at the first seed of families 0,1,5,6. No model sweep or alternate feature method.

Every primary negative copies the expected opaque job ID, request/settings/model commitments, output claim and ordinary envelope fields. Only the numerical measurement and its required authenticated digest/signature change. Job metadata does not enter numerical scoring. Ground truth is absent from the bundle and joined only after scoring. Main prompt swaps deliberately isolate fingerprint substitution; output delivery swaps are separate controls.

Use the unchanged IMG-002 conditional-branch 54 statistics: six reductions at three corresponding U-Net residual layers and denoising steps 0/12/24. Each fingerprint is 54 little-endian float32 = 216 bytes. Scale = feature population standard deviation across the 30 calibration reference vectors, floored at 1e-6. Score = float64 RMS standardized candidate-minus-reference. Accept score ≤ 1e-05. Tolerance was declared as max(1e-5, ten times maximum calibration positive distance including reloads). Calibration positives: 36, maximum 0.0; calibration swaps: 40, minimum 0.307047. Calibration passed the original method; no held-out tuning. This nonzero numerical tolerance is an engineering floor, not a validated cross-runtime tolerance. A distance is not a likelihood.

| Split / comparison | N | Accepted | Distance min / median / max |
|---|---:|---:|---|
| calibration / correct | 30 | 30 | 0 / 0 / 0 |
| calibration / close | 20 | 0 | 0.3070472 / 0.6794932 / 1.104063 |
| calibration / distant | 20 | 0 | 0.9581317 / 1.440635 / 2.029216 |
| calibration / reload | 6 | 6 | 0 / 0 / 0 |
| heldout / correct | 60 | 60 | 0 / 0 / 0 |
| heldout / close | 40 | 0 | 0.2842027 / 0.6341741 / 1.204524 |
| heldout / distant | 40 | 0 | 0.7959698 / 1.528602 / 3.208854 |
| heldout / reload | 6 | 6 | 0 / 0 / 0 |

All 90 independent candidates and 12 reloads had bitwise-identical fingerprints and delivered pixel content to their expected reference on this host. This makes the tested comparisons easy to separate, but establishes neither universal zero tolerance nor cross-GPU robustness. Correlated reciprocal swaps share reference and donor runs; repeats share prompts and seeds. No confidence interval is presented as an independent-trial population estimate.

## Identical effective input limitation

Two different raw prompt strings share a long prefix and differ only beyond the CLIP truncation window. Full token lengths are [152, 152], effective 77-token inputs are verified equal. Both underwent real generation and produced identical fingerprints and pixels. The raw input commitments differ; a correctly re-signed envelope carrying the expected raw input commitment and the other measurement passes numerical verification. This control is excluded from fitting and main semantic-change rates. Execution measurements cannot be expected to distinguish raw strings that become identical effective model inputs. Main prompts fit the token limit (full token length range [9, 14]) and all ABC token inputs differ.

## Commitment, receipt and output scorecard

Canonical encoding and exact commands are in README.md/common.py. SHA-256 commitments use fresh independent secret 32-byte input/output blindings and versioned, length-framed purpose separation. Input commits exact supplied UTF-8 prompt string and the full declared request specification (including pinned model/profile, scheduler/settings, seed and requested output); private token records distinguish raw text from effective input. Output commits width/height and post-safety RGB uint8 pixel bytes, not PNG metadata. The observer recomputes delivered output with the expected job output blinding. The scheme is illustrative; no formally validated privacy claim is made.

Ed25519 authenticates the receipt contents, including job ID, request commitment, model/profile/settings commitments, output commitment, numerical fingerprint digest and measurement version. It does not authenticate the truth of a worker association. The worker test key can sign deliberate lies. All ordinary main prompt-swap receipts are validly signed and commitment-consistent; their commitment-only check passes, while numerical checking rejects them.

| Separate control | N | FP accept | Signature valid | Commitment/receipt accept | Combined accept |
|---|---:|---:|---:|---:|
| copied_reference_no_fresh_execution | 1 | 1 | 1 | 1 | 1 |
| identical_effective_input | 1 | 1 | 1 | 1 | 1 |
| receipt_unchanged | 1 | 1 | 1 | 1 | 1 |
| signed_wrong_fingerprint | 1 | 0 | 1 | 1 | 0 |
| signed_wrong_output | 1 | 1 | 1 | 0 | 0 |
| stale_other_job_receipt | 1 | 0 | 1 | 0 | 0 |
| unsigned_edit_fingerprint_digest | 1 | 1 | 0 | 0 | 0 |
| unsigned_edit_input_commitment | 1 | 1 | 0 | 0 | 0 |
| unsigned_edit_job_id | 1 | 1 | 0 | 0 | 0 |
| unsigned_edit_measurement_version | 1 | 1 | 0 | 0 | 0 |
| unsigned_edit_model_profile | 1 | 1 | 0 | 0 | 0 |
| unsigned_edit_output_commitment | 1 | 1 | 0 | 0 | 0 |
| unsigned_edit_settings_commitment | 1 | 1 | 0 | 0 | 0 |
| unsigned_edit_version | 1 | 1 | 0 | 0 | 0 |
| wrong_delivery_no_observer | 1 | 1 | 1 | 1 | 1 |
| wrong_delivery_with_observer | 1 | 1 | 1 | 0 | 0 |

Unchanged receipt passes. Eight individual receipt field edits without re-signing fail signature checks. A whole genuine other-job receipt retains a valid signature but fails expected job identity. A validly signed wrong-job fingerprint passes the commitment checks and fails numerical comparison. A validly signed wrong output claim and a wrong delivered output with an honest expected claim both pass fingerprint-only checking but fail output consistency. These output failures are credited to commitments/observer, never to fingerprints.

Two intended negative controls pass: copying a known genuine expected fingerprint/output commitment and re-signing a claimed job proves no fresh execution; and claiming expected output while delivering other saved bytes passes if no trusted observer hashes the delivery. The latter is the same wrong saved image used in the observer-present failure. Receipt job IDs reject stale labels, not fabricated fresh computation. A trusted reference runner costs actual private inference, and the collector must associate genuine measurements and delivered bytes. An operator who controls them can replay or lie. Signatures/commitment equality establish neither causality, input privacy, generation, nor absence of malicious instructions. Changed benign prompt strings are not a prompt-injection benchmark.

## Costs, artifacts and safety

194 real full generations were saved: 90 references, 90 independent candidates, 12 reload repeats, 2 token-collision controls. No fake tensors, output-only image features, paid APIs, containers or runner services. The reference burden is one full SD1.5 generation per expected prompt/config/seed. The first cold reference is included in totals; timing excludes model load, latent creation and PNG write but includes synchronized pipeline/hooks, safety checker and PIL conversion.

| Role | Generations | Total pipeline seconds | Median seconds | Min / max seconds |
|---|---:|---:|---:|---:|
| reference | 90 | 119.348 | 1.2935 | 1.2713 / 2.5976 |
| candidate | 90 | 118.238 | 1.2927 | 1.2731 / 1.8685 |
| reload | 12 | 16.453 | 1.2751 | 1.2680 / 1.8288 |
| control | 2 | 3.054 | 1.5271 | 1.2683 / 1.7859 |

Five model loads total 13.439s. Verifier CPU per case median 114.42 µs, p95 128.43 µs; total 0.02801s, excluding JSON/import loading. Audited complete verifier run including imports: 0.0701s. These include signature/commitment comparisons and numerical scoring, not generation. Fingerprint files total 41904 bytes; PNG images 88649953 bytes; minimal bundle 1106665 bytes / 238 cases (JSON repeats reference vectors per case; not a compact transport benchmark).

The method did not change, so no new broad hook-overhead benchmark was performed. Context only: IMG-002 measured SD1.5 median hook overhead 0.39% / 0.00509s over ten paired jobs, with paired-bootstrap interval 0.0276–0.9903%; those are prior measurements, not a new JOB-003 timing result. Desktop contention and startup affect current timing.

Normal safety checking remained enabled, outside fingerprint extraction. Safety replacements in this experiment: 2. Flagged runs (if any) are listed in results.json and checked for black pixels; output comparisons describe delivered post-safety pixels, not pre-safety decoded images. No safety bypass was used.

## Provenance, access separation and cleanup

Model: stable-diffusion-v1-5/stable-diffusion-v1-5 revision 451f4fe16113bff5a5d2269ed5ad43b0592e9a14; reused pinned local FP16 files and prior interpreter/cache read-only. 512×512, batch1, DDIM25, CFG7.5, eta0, empty negative prompt; deterministic PyTorch settings and CPU-created matched FP16 latents. model-identity.json carries the prior file SHA-256 identities, rechecked by check.py. Load files carry actual scheduler/runtime versions. No environment package was installed or modified; system cryptography supplies Ed25519 separately from GPU generation.

verification.json: 24/24 checks pass. It checks protocol/pre-heldout hashes and chronology, counts, independent positive records, finite vectors, all image pixels/output commitments, split disjointness, equal matched latents, tokenizer checks, safety flags, scheduler parity, model-file identities, export schema, private-data exclusions and secret-file permissions. The artifact-only bundle has five files and no prompt, tokens, embeddings, output content, seed, family label, blinding, signing key, private manifest path or ground truth. access-audit.json records an actual exported verifier run with experiment reads outside bundle forbidden, using only Python/cryptography library dependencies. This is logical access separation; the experiment agent can read all roles, and fingerprints may leak information that was not studied.

GPU use was one pipeline at a time, batch1; only this experiment processes were allowed to exit naturally. host-before.txt / host-after.txt and cleanup.json record desktop preservation and no remaining experiment GPU process. No services, drivers, T3 state, production files, AGENTS files, earlier experiment outputs, Git commits, pushes or parent journal were changed. Test secrets remain restricted private local artifacts; none are printed or exported. The initial precedent module import used its existing cached bytecode; subsequent imports explicitly disabled bytecode writes. No prior loader/writer was called.

Artifacts: README.md gives exact verifier/reproduction commands; bundle/ is the transferable artifact-only input; numerical-scorecard.json and binding-scorecard.json keep credits separate; decision-rows.json/.csv join truth after scoring; distances.png / errors.png visualize distances and raw errors; vectors/ and images/ retain real private inference outputs; protocol.json / frozen-rule.json / before-heldout.json establish design and freeze; journal-entry.json is for the parent to inspect, not an edit to its journal.

Conclusion: the original small numerical fingerprint separates the tested effective prompt changes under exact deterministic same-job references. It requires a full trusted private reference generation per job and trustworthy collection. It is neither a cryptographic proof of execution nor a freshness proof or semantic security guarantee.

## Verification correction and final scorecard checks

The first integrity pass failed only `same_effective_scheduler`: Diffusers serializes `_use_default_values` in process-dependent order. Every effective scheduler value and the set of defaulted fields matched. The verifier check now sorts only that private bookkeeping list. `verification-initial.json` preserves the failure; verification.json passes 24/24. No model, measurement, threshold, scoring/export source, prompt or result changed. `final-checks.json` separately confirms all control expectations, exact agreement of audited and original decisions (excluding CPU timing), exported source equality to frozen source, and the five-file export. `binding-main-scorecard.json` reports fingerprint-only, receipt/commitment-only and combined counts for all primary comparisons. `private/delivery-evidence.json` links output-swap controls to the actual saved alternative image, committed under the expected job blinding.

The three roles are logical: requester.py creates expected requests/commitments; run.py performs reference/candidate inference with a colocated trusted pixel observer; build_bundle.py simulates the worker receipt signer and exports expected collector records; bundle/verifier.py consumes only the export. Their common hosting agent/process access is explicitly trusted here. Secret blinding is illustrative and does not establish that numerical fingerprints or unblinded public settings digests conceal request information. No privacy leakage analysis was performed.
