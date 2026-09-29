# Experiments and reproducible material

- [`m1/baseline-accounting/`](m1/baseline-accounting/) — the M1.1 baseline accounting workbook. `build.py` generates a spreadsheet that reproduces the litepaper's reward arithmetic for one round and two nodes: fee split, emission shares, MFS (the rule that caps a node's reward share at its stake share) and the validator multiplier. `verify.py` checks the workbook against independent arithmetic fixtures. The numbers are illustrative, not an emissions policy or a forecast; the research workbench cites the results as its baseline workbook.

For each experiment, identify its task and question; input versions and access or licensing constraints; method; expected controls; execution instructions; resource or paid-call budget; result artifact; errors and limitations. Separate simulations from measured network observations.

Use bounded fixtures or existing authorized services. Do not upload credentials, customer payloads or unrelated datasets. Model-runner deployment is not a prerequisite for this coordination repository.
