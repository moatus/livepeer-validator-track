# Artifact and review workflow

## Task to deliverable

1. State the question and expected artifact in a task issue; link the milestone and prerequisites.
2. Produce the smallest artifact that answers the question. Research reports, diagrams, models, datasets, specifications and test results are all valid outputs. A few transparent litepaper examples can establish a conditional concern. Broader cooperative, market and adversarial cases belong with the proposed litepaper expansion when they inform a design choice.
3. Record methods, sources, assumptions, findings, limitations and reproduction instructions where applicable.
4. Obtain the agreed review. Reviewer identity and acceptance criteria should be explicit; do not invent a reviewer or infer acceptance from silence.
5. Add the accepted artifact version to the issue's Deliverables table, the Project Artifact field and the deliverable register. Link a PR separately if it records review.
6. Close the task after its definition of done is met. Update the milestone overview and the monthly outcome summary.

## Where artifacts live

- Reports, diagrams and specifications: under `deliverables/`, organized by milestone and linked from their task issues.
- Reproducible models, scripts and bounded fixtures: under `experiments/`, with an explanation and result link.
- PDFs, recordings and large datasets: a suitable release asset or durable external location. Record access, version and any retention limits. A temporary CI download is not a durable acceptance record.
- Implementation elsewhere: link the upstream issue or PR and the actual delivered artifact or release from the track's delivery issue.

Use a commit-specific permalink for an accepted repository file. A branch link identifies the latest revision and can change. External artifacts need a dated/versioned identity and public access when cited as public deliverables. The PR is useful review history; the result should be discoverable without reading the PR conversation.

## Task record

Each issue includes the question, source/version basis, expected artifact, completion criteria, dependencies, a Deliverables table and findings. Planned paths stay in code formatting until files exist. The Project Artifact field should link the primary submitted result; the issue can index several artifacts.

Project Status tracks work: Todo, In Progress, Done. Artifact review tracks Not submitted, In review, Accepted or Changes requested. A failed hypothesis or documented evidence limitation can be a completed research outcome if it answers the question and passes review. Accepted research is not approval to deploy or change protocol economics.

Keep a path from source to recommendation: litepaper objective or provision, assumption, concern, evidence, proposed addition and unresolved decision. Current-system impact checks should identify relevant deployed versions and include contracts, off-chain components and participant workflows as appropriate. If evidence shows an existing mechanism needs revision, record that explicitly. Detailed engineering estimates are unnecessary for early checkpoints.

## Milestones and dates

Native repository milestones are the grouping and due-date record. Overview issues summarize the outcome and link their task sub-issues. Keep the Markdown overview consistent at reporting points. Target dates are not yet agreed; do not interpret the reporting setup deadline as every milestone's delivery date.

This repository is the validator track's research and reporting hub. Tasks implemented elsewhere need one reporting issue here linking the authoritative external work. Do not duplicate full milestones or artifacts across repositories simply to show them on a board.

## Public research

The repository and Project are public. Add findings, models, tests and supporting assets in a form others can inspect, with source attribution and reproducible methods where possible. Keep credentials, customer payloads and restricted third-party material out of the repository. Public deliverable links should resolve for readers without special access.
