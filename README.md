# Network Engineering SPE II — Validator Track

The public research and delivery hub for the validator track of Network Engineering SPE II, led by Shane (@moatus). The work builds on the Livepeer 2.0 litepaper: understand its objectives and mechanisms, test its assumptions, evaluate whether and where to expand it, test what is recommended, and hand off a practical validator workflow.

The project tests the litepaper's protocol mechanics: rewards, validation, delegation, emissions, buyback and governance. The paper's market case and its agent-layer vision are context; they are not under test.

- [Project board](https://github.com/users/moatus/projects/1)
- [Milestone overview](MILESTONES.md)
- [Native milestones](https://github.com/moatus/livepeer-validator-track/milestones)
- [Task issues](https://github.com/moatus/livepeer-validator-track/issues?q=is%3Aissue+label%3Atrack%3Atask)
- [Deliverable register](deliverables/README.md)
- [Artifact and review workflow](docs/WORKFLOW.md)
- [Monthly updates](updates/README.md)
- [Decision log](docs/DECISIONS.md)
- [SPE pre-proposal](https://forum.livepeer.org/t/pre-proposal-network-engineering-spe-ii/3344)

The milestone and task structure is in place, and the M1 and M2 research is under way in the [research workbench](#research-workbench). M1's September steps have reviewed versions. The October source migration is a new draft; M2's first pilot has completed its stage work, and the [connected second slice](docs/m2/SLICE-02.md) is prepared but not started. Target dates and external reviewers remain to be agreed.

## Research workbench

[`validator-track-workbench.html`](validator-track-workbench.html) holds the M1 and M2 research as one linked, browsable record set. It is a single TiddlyWiki file: download it and open it in a web browser; nothing needs to be installed. It works offline.

It follows the litepaper through the milestone steps M1.1 to M2.3:

| Step | Task | Workbench status |
| --- | --- | --- |
| M1.1 How the architecture works, mechanism by mechanism | [#6](https://github.com/moatus/livepeer-validator-track/issues/6) | September reviewed; October revision drafted |
| M1.2 What each mechanism depends on, and its critical questions | [#7](https://github.com/moatus/livepeer-validator-track/issues/7) | September reviewed; October revision drafted |
| M1.3 Which cases matter most | [#8](https://github.com/moatus/livepeer-validator-track/issues/8) | September reviewed; October revision drafted |
| M1.4 What exists today, and what would need to be built | [#14](https://github.com/moatus/livepeer-validator-track/issues/14) | September reviewed; October revision drafted; deployed mapping remains version-bound |
| M2.1 How the mechanisms behave together | [#10](https://github.com/moatus/livepeer-validator-track/issues/10) | In progress: pilot reconstruction and October reconciliation |
| M2.2 Testing the critical questions | [#9](https://github.com/moatus/livepeer-validator-track/issues/9) | In progress: September pilot preserved; October bridge; connected model next |
| M2.3 What would resolve each concern? | [#15](https://github.com/moatus/livepeer-validator-track/issues/15) | In progress: pilot findings consolidated; October reconciliation drafted |

Inside, the litepaper is described as twelve mechanisms. Each mechanism page explains the mechanism in plain words, lists its parts, and marks what the paper states and what is still to be defined or decided (design questions). It also asks whether the mechanism could work as intended (critical questions, tested against concrete cases and their legitimate lookalikes), and records what exists in today's Livepeer system. Step pages tell the story of each milestone step; role guides summarise what changes for node operators, delegators and validators. The current source is the [October paper](docs/litepaper-2.0.md), extracted from its [archived PDF](docs/sources/litepaper-2026-10.pdf). Its [provenance](docs/sources/README.md) separates original text, editorial extraction wrappers and the preserved September version. Historical September citations and results remain version-labelled; October citations use their own source record. PDF figures remain authoritative in the PDF. Start with "How to read this workbench" on its home page.

Findings, conclusions and proposed critical questions in the workbench are research drafts, labelled by how firmly they are held (assumption, inference, hypothesis, supported by the text). M1's September versions are accepted as research deliverables; October revisions remain drafted (see the [deliverable register](deliverables/README.md)); acceptance records that the research is fit to build on, not that any finding is proven, and none is a protocol decision.

**Tools.** [`validator-track-workbench-tools/`](validator-track-workbench-tools/) holds `vtw.py` (show and find to read and search the workbench from a terminal; export, import, lint and diff to edit it), a browser check, a word-budget check and unit tests; its README explains how to edit the workbench. The workbench's reward-arithmetic check comes from the baseline accounting workbook in [`experiments/m1/baseline-accounting/`](experiments/m1/baseline-accounting/): `build.py` generates the workbook and `verify.py` checks it.

## Listening guides

These supporting review guides summarize M1.1–M1.4 for listening, each labeled about twelve minutes. They retain their source basis at commit `eec258d`; the workbench and deliverable register hold the research and its reviewed versions.

- [M1.1 — Architecture and mechanisms](docs/reviewer-resources/m1.1-review-listening-guide-short.md)
- [M1.2 — Dependencies and critical questions](docs/reviewer-resources/m1.2-review-listening-guide-short.md)
- [M1.3 — Scenarios and legitimate lookalikes](docs/reviewer-resources/m1.3-review-listening-guide-short.md)
- [M1.4 — Current system to litepaper map](docs/reviewer-resources/m1.4-review-listening-guide-short.md)

## Working structure

Five native milestones group the work: litepaper foundation, incentive and evidence tests, an evaluation of whether and where to expand the litepaper, bounded validation, then pilot and handoff. Each has a tracking issue and a Project overview card. Task issues are linked as sub-issues and assigned to the same native milestone. Each task records a question, expected artifact, completion criteria, dependencies and reviewed deliverables. The milestones describe the reasoning path; useful work can overlap across them.

Implementation can live in other repositories. Keep one delivery issue here that links to the upstream issue, PR and resulting artifact; avoid copying the same discussion and progress into two trackers.

Research conclusions and protocol adoption are different decisions. Record evidence, uncertainty and requested handoffs without representing a proposed mechanism as approved policy.

## Research and deliverables

Use task issues to frame questions and link results. The M1 and M2 research lives in the [research workbench](#research-workbench); a reviewed version is recorded by commit. Put other reports, specifications and diagrams in [`deliverables/`](deliverables/), and reproducible models, fixtures and tests in [`experiments/`](experiments/). The [deliverable register](deliverables/README.md) links reviewed results to milestones; the Project board shows current work. Cite sources, assumptions, versions and limits so others can inspect or reproduce the findings.
