# Artifact and review workflow

## Task to deliverable

1. State the question and expected artifact in a task issue; link the milestone and prerequisites.
2. Produce the smallest artifact that answers the question. Research reports, diagrams, models, datasets, specifications and test results are all valid outputs. A few transparent litepaper examples can establish a conditional concern. Broader cooperative, market and adversarial cases belong in M3, where they inform whether and where to expand the litepaper.
3. Record methods, sources, assumptions, findings, limitations and reproduction instructions where applicable.
4. Review the artifact. Its status moves from drafted to reviewed only when the review is complete; never infer a review from silence.
5. Add the reviewed artifact version to the issue's Deliverables table, the Project Artifact field and the deliverable register.
6. Close the task after its definition of done is met. Update the milestone overview and the monthly outcome summary.

## Where artifacts live

- M1 and M2 research: the research workbench, `validator-track-workbench.html` at the repository root. Each milestone step is a workbench page backed by linked records. Cite a reviewed step by commit permalink to the file plus the step name.
- Reports, diagrams and specifications: under `deliverables/`, organized by milestone and linked from their task issues. Later milestones may still use separate files.
- Reproducible models, scripts and bounded fixtures: under `experiments/`, with an explanation and result link.
- PDFs, recordings and large datasets: a suitable release asset or durable external location. Record access, version and any retention limits. A temporary CI download is not a durable record.
- Implementation elsewhere: link the upstream issue or PR and the actual delivered artifact or release from the track's delivery issue.

Use a commit-specific permalink for a reviewed repository file. A branch link identifies the latest revision and can change. External artifacts need a dated/versioned identity and public access when cited as public deliverables. The PR is useful review history; the result should be discoverable without reading the PR conversation.

## Task record

Each issue includes the question, source/version basis, expected artifact, completion criteria, dependencies, a Deliverables table and findings. Planned paths stay in code formatting until files exist. The Project Artifact field should link the primary submitted result; the issue can index several artifacts.

Project Status tracks work: Todo, In Progress, Done. An artifact's status is drafted or reviewed. A failed hypothesis or documented evidence limitation can be a completed research outcome if it answers the question and is reviewed. Reviewed research is not approval to deploy or change protocol economics.

Keep a path from source to recommendation: litepaper objective or provision, assumption, concern, evidence, recommendation (no change, a clarification or a litepaper expansion) and unresolved decision. Current-system impact checks should identify relevant deployed versions and include contracts, off-chain components and participant workflows as appropriate. If evidence shows an existing mechanism needs revision, record that explicitly. Detailed engineering estimates are unnecessary for early checkpoints.

## Milestones and dates

Native repository milestones are the grouping and due-date record. Overview issues summarize the outcome and link their task sub-issues. Keep the Markdown overview consistent at reporting points. M2–M5 target dates are agreed and listed in [MILESTONES.md](../MILESTONES.md). The Project Target date field mirrors milestone deadlines on overview cards; task dates can be set separately when agreed. Do not interpret the reporting setup deadline as every milestone's delivery date.

This repository is the validator track's research and reporting hub. Tasks implemented elsewhere need one reporting issue here linking the authoritative external work. Do not duplicate full milestones or artifacts across repositories simply to show them on a board.

## Public research

The repository and Project are public. Add findings, models, tests and supporting assets in a form others can inspect, with source attribution and reproducible methods where possible. Keep credentials, customer payloads and restricted third-party material out of the repository. Public deliverable links should resolve for readers without special access.
