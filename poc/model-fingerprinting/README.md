# Model fingerprinting

These studies ask different questions and their success counts must not be combined into a general accuracy claim.

| Study | Code and report | Result and limit |
| --- | --- | --- |
| Speech-model discrimination (ASR-001) | [Speech package](speech/README.md), [report](speech/REPORT.md), [runner](speech/run.py) | 36/36 first held-out model/clip cases under the tested configurations; precision/runtime and scale effects limit generalization. |
| Image-model discrimination (IMG-002) | [Image package](image/README.md), [report](image/REPORT.md), [runner](image/run.py) | 80/80 held-out SD1.4/1.5 generations, fixed runtime/settings; no fabrication-resistance guarantee. |
| Individual-job consistency (JOB-003) | [Job package](job-consistency/README.md), [report](job-consistency/REPORT.md), [offline verifier](job-consistency/bundle/verifier.py) | Bounded consistency tests passed; copied genuine evidence and wrong deliveries without an observer could pass. |

The study directories contain inference scripts, numerical records and reports. Raw audio, generated images, model weights and private inputs are not distributed. Full inference reproduction requires the pinned model/data dependencies and adapting any original host paths. See the [package and reproduction boundaries](../README.md).

These results support [M3.1’s evidence-gap analysis](../../validator-track-workbench.html#M3.1) and [M3.2 §2’s ongoing evaluation](../../validator-track-workbench.html#M3.2), especially the separation of advertised identity, execution, freshness and actual delivery. They do not prove independent customer demand or economic purpose.
