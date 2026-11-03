# Identifying model substitution from outputs

These experiments test whether finished images provide useful evidence of which model produced them. They preserve negative findings and failed controls as research outcomes.

| Study | Files | Main result |
| --- | --- | --- |
| Quality scores and visual features (JUDGE-004) | [Study index](quality-scoring/README.md) | Close SD1.4/1.5 discrimination: PickScore 21/36, visual features 18/36, combined 22/36. |
| Local AI judge and offline recovery | [Qwen report](quality-scoring/evidence/QWEN-REPORT.md), [sensitivity report](quality-scoring/evidence/sensitivity/local-qwen-sensitivity/REPORT.md) | 30/215 main outputs met the strict schema; offline recovery produced inconsistent exploratory gains. |
| Image-pattern analysis (FORENSIC-006) | [Report](image-forensics/REPORT.md), [analysis](image-forensics/analyze.py) | Tested methods failed the frozen close-model screen and were sensitive to benign transformations. |
| Four-output comparison (CONSENSUS-007) | [Results and limitations](peer-comparison/REPORT.md), [results](peer-comparison/results.json) | 0/19 close substitutions flagged by the tested RPA method, with 18/19 false accusations under honest JPEG compression. One GPU simulated submissions. |

Original code, numeric features, reports and bounded saved records are included. Bulk images/model weights and host logs are excluded. Some frozen scripts retain host-dependent input paths and deliberate first-run assertions; do not rerun them over preserved results. Work on a disposable copy when reproducing.

The research implication for [M3.2 §3](../../validator-track-workbench.html#M3.2) is a limit on the tested identity claims, not proof that every possible output attribution method fails. Hosted Nemotron was not executed. Exploratory review/parent acceptance is not protocol adoption.
