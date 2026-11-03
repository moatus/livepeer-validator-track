# Comparing multiple outputs to detect model substitution

The tested method did not reliably identify close-model substitutions. Its RPA representation flagged **0/19** close substitutions and falsely accused **18/19** honest JPEG-compressed cases. All four submissions were simulated on one GPU; they were not independently operated network nodes.

The [numerical results](results.json), [frozen protocol](PROTOCOL.json) and [full experimental report](report.html) describe the methods and comparisons. The [M3 evaluation](../../../validator-track-workbench.html#M3.2) explains the implications for validator evidence.

## Interpretation limits

Prior encoder exposure matters: the reused forensic checkpoint's training classes included SDXL and SD1.5. That limits generalization claims; it is not evidence of computational leakage from held-out labels during this experiment. The checkpoint identity is retained in `identities.json`.

The SD1.x comparisons used independently seeded generation rather than matched input noise. The original protocol's `paired_cpu_fp16_noise` label must not be read as proof of matched noise; `schedule.json` and `generate.py` identify the actual generation setup. The numerical results are unchanged by this clarification.

Feature-based CPU replay can check the calculations and permutation results from the included data. It does not independently certify GPU execution, omitted image files or the encoder's training corpus. Full reproduction requires the model/data dependencies and original media. The observed failures do not prove that every output-attribution method fails, but they do not support using this method for economic penalties.
