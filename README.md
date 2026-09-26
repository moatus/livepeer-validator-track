# Network Engineering SPE II — Validator Track

The public research and delivery hub for the validator track of Network Engineering SPE II, led by Shane (@moatus). The work builds on the Livepeer 2.0 litepaper: clarify its objectives and assumptions, test its economics, develop a validator-track expansion, and evaluate a practical review workflow.

- [Project board](https://github.com/users/moatus/projects/1)
- [Milestone overview](MILESTONES.md)
- [Native milestones](https://github.com/moatus/livepeer-validator-track/milestones)
- [Task issues](https://github.com/moatus/livepeer-validator-track/issues?q=is%3Aissue+label%3Atrack%3Atask)
- [Deliverable register](deliverables/README.md)
- [Artifact and review workflow](docs/WORKFLOW.md)
- [Monthly updates](updates/README.md)
- [Decision log](docs/DECISIONS.md)
- [SPE pre-proposal](https://forum.livepeer.org/t/pre-proposal-network-engineering-spe-ii/3344)

The milestone and task structure is in place. Research findings, models and test results will be added as reviewable artifacts as the work progresses. A planned artifact path is not a delivered artifact. Target dates and reviewers remain to be agreed.

## Working structure

Five native milestones group the work: litepaper foundation, incentive and evidence tests, litepaper expansion, bounded validation, then pilot and handoff. Each has a tracking issue and a Project overview card. Task issues are linked as sub-issues and assigned to the same native milestone. Each task records a question, expected artifact, completion criteria, dependencies and reviewed deliverables. The milestones describe the reasoning path; useful work can overlap across them.

Implementation can live in other repositories. Keep one delivery issue here that links to the upstream issue, PR and resulting artifact; avoid copying the same discussion and progress into two trackers.

Research conclusions and protocol adoption are different decisions. Record evidence, uncertainty and requested handoffs without representing a proposed mechanism as approved policy.

## Research and deliverables

Use task issues to frame questions and link results. Put research reports, specifications and diagrams in [`deliverables/`](deliverables/), and reproducible models, fixtures and tests in [`experiments/`](experiments/). The [deliverable register](deliverables/README.md) links reviewed results to milestones; the Project board shows current work. Cite sources, assumptions, versions and limits so others can inspect or reproduce the findings.
