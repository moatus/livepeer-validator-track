# Milestone overview

Owner: Shane (@moatus). [Project board](https://github.com/users/moatus/projects/1). M2–M5 target dates are agreed for 2026 and recorded below. M1 is reviewed and M2 has received its handoff; M3–M5 are planned. M1's four workbench steps are the first reviewed deliverables (see the [deliverable register](deliverables/README.md)). The M1 and M2 work is drafted in the [research workbench](validator-track-workbench.html) (see the [README](README.md#research-workbench)).

Research path: **understand the litepaper → test its assumptions → evaluate whether and where to expand it → test what is recommended → hand off a validator workflow**. M3 takes two kinds of input: concerns the M2 tests leave unresolved after plausible completions of the paper are compared, and areas the litepaper leaves unaddressed or where its mechanisms work against its own goals. For each, it decides whether a litepaper expansion is warranted and what it would be. "No expansion needed" and "clarify the existing rule" are valid outcomes. Work may overlap across milestones.

| Milestone | Intended outcome | Tracking | Target date | Budget (USD) | Accepted deliverables |
| --- | --- | --- | --- | ---: | --- |
| [M1 — Objectives, assumptions and validation requirements](https://github.com/moatus/livepeer-validator-track/milestone/1) | Baseline, required claims, early threats and current-system map. | [#1](https://github.com/moatus/livepeer-validator-track/issues/1) | To agree | — | [M1.1–M1.4](deliverables/README.md) |
| [M2 — Test litepaper incentives and evidence limits](https://github.com/moatus/livepeer-validator-track/milestone/2) | Substantiate material concerns and evidence limits. | [#2](https://github.com/moatus/livepeer-validator-track/issues/2) | 2026-10-19 | $5,000 | None |
| [M3 — Evaluate where the litepaper could be expanded](https://github.com/moatus/livepeer-validator-track/milestone/3) | Decide whether and where a litepaper expansion is warranted, and what it would be. | [#3](https://github.com/moatus/livepeer-validator-track/issues/3) | 2026-11-09 | $7,000 | None |
| [M4 — Bounded economic and work-validation tests](https://github.com/moatus/livepeer-validator-track/milestone/4) | Test the litepaper's consequential assumptions, anything M3 recommends, and reviewer methods. | [#4](https://github.com/moatus/livepeer-validator-track/issues/4) | 2026-12-07 | $8,000 | None |
| [M5 — Validator workflow pilot and delivery handoff](https://github.com/moatus/livepeer-validator-track/milestone/5) | Exercise a bounded workflow and hand off supported recommendations. | [#5](https://github.com/moatus/livepeer-validator-track/issues/5) | 2026-12-31 | $10,000 | None |

**Total M2–M5 budget: $30,000 USD.**

## M1 — Objectives, assumptions and validation requirements

Use the Livepeer 2.0 litepaper as the design foundation. Separate its desired outcomes from proposed mechanisms and assumptions. Explain the intended cooperative flow of payments, rewards, costs and participant incentives. Examine each mechanism for what its success depends on that is not yet established, including the claims reward eligibility relies on, what evidence could establish them, and where even perfect execution evidence would leave an economic problem. Inspect current Livepeer components enough to show the scale of the litepaper's changes.

**Completion:** A baseline of the twelve mechanisms; a pass through each mechanism with eight lenses (calculation, observation, inference, policy and authority, individual incentives, collective behaviour, social and operational effects, and system feedback), with proposed critical questions wherever its success depends on something not yet established; representative attack and legitimate scenarios; and a versioned current-system → litepaper impact map covering contracts, off-chain components and participant roles. Mark unresolved choices and unknowns.

| Task | Artifact | Status |
| --- | --- | --- |
| [M1.1 — Map litepaper objectives, mechanisms and incentives](https://github.com/moatus/livepeer-validator-track/issues/6) | Workbench step M1.1, "How the architecture works, mechanism by mechanism" | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/2c697f9f5b29911d2fb26fa5b26d76c61f5fdc1a/validator-track-workbench.html) (`2c697f9`) |
| [M1.2 — Identify what each mechanism depends on and its critical questions](https://github.com/moatus/livepeer-validator-track/issues/7) | Workbench step M1.2, "What each mechanism depends on, and its critical questions" | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/2c697f9f5b29911d2fb26fa5b26d76c61f5fdc1a/validator-track-workbench.html) (`2c697f9`) |
| [M1.3 — Define adversarial scenarios and legitimate lookalikes](https://github.com/moatus/livepeer-validator-track/issues/8) | Workbench step M1.3, "Which cases matter most" | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/2c697f9f5b29911d2fb26fa5b26d76c61f5fdc1a/validator-track-workbench.html) (`2c697f9`) |
| [M1.4 — Map the current system to the litepaper](https://github.com/moatus/livepeer-validator-track/issues/14) | Workbench step M1.4, "What exists today, and what would need to be built" | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/2c697f9f5b29911d2fb26fa5b26d76c61f5fdc1a/validator-track-workbench.html) (`2c697f9`) |

## M2 — Test litepaper incentives and evidence limits

Reassemble the mechanisms from the M1 handoff into one system: participants and their overlapping roles, their choices, information, timing and payoffs. Rank what to test. Then test the critical questions in that order, with small economic examples and focused evidence inquiries. Begin with intended cooperative behavior, then vary a pivotal condition or strategic action. Stop when a test supports or rejects the specific concern; a full network simulation is unnecessary. Examine only evidence relevant to those concerns.

**Completion:** A reconstruction of the combined system with a ranked list of what to test; reproducible economic examples and focused evidence inquiries with explicit assumptions and limits, including what validators can observe; and a consolidated record of what the tests show and what would resolve each concern (a specification, better evidence, a change in incentives or a policy choice), linking litepaper provisions, assumptions, evidence, current-system implications and design questions. Distinguish modeled vulnerability from observed prevalence. Hand M3 the concerns that remain unresolved and the areas the paper leaves unaddressed.

| Task | Artifact | Status |
| --- | --- | --- |
| [M2.1 — Reconstruct how the mechanisms behave together](https://github.com/moatus/livepeer-validator-track/issues/10) | Workbench step M2.1, "How the mechanisms behave together" | Handoff from M1 received; nothing run |
| [M2.2 — Test the critical questions](https://github.com/moatus/livepeer-validator-track/issues/9) | Workbench step M2.2, "Testing the critical questions" | Not started; tests proposed |
| [M2.3 — Consolidate findings and design requirements](https://github.com/moatus/livepeer-validator-track/issues/15) | Workbench step M2.3, "What would resolve each concern?" | Not started |

## M3 — Evaluate where the litepaper could be expanded

Start from the M1 and M2 findings. M3 receives two kinds of input: concerns the M2 tests leave unresolved after plausible completions of the paper are compared on their tradeoffs, and areas the litepaper leaves unaddressed or where its mechanisms work against its own goals: reward integrity, open market participation, participant incentives, credible validation and implementation. Specification details that the paper plainly implies remain design questions for build work; they enter M3 only if they amount to an unaddressed area. For each input, evaluate whether a litepaper expansion is warranted and what it would be. "No expansion needed" and "clarify the existing rule" are valid outcomes. Model scenarios only for the options worth pursuing, and only where they clarify a design choice or failure boundary.

**Completion:** A list of the unresolved concerns, gaps and conflicts, with the evidence for each; an evaluation of the options for each, with participant incentives and a recommendation; small cooperative, ordinary-market and selected adversarial scenarios, or equivalent worked cases, for the options worth pursuing; and, for any recommended expansion, an integration map tracing **current system → litepaper**, **litepaper → recommended expansion** and **current system → recommended expansion** across contracts, off-chain components, workflows and migration considerations. Identify what M4 should test, and where a recommendation adjusts an existing mechanism.

| Task | Planned artifact |
| --- | --- |
| [M3.1 — Identify gaps and conflicts that could warrant an expansion](https://github.com/moatus/livepeer-validator-track/issues/11) | `deliverables/m3/gaps-and-conflicts.md` |
| [M3.2 — Evaluate expansion options and participant incentives](https://github.com/moatus/livepeer-validator-track/issues/12) | `deliverables/m3/expansion-evaluation.md` |
| [M3.3 — Explore scenarios for the options worth pursuing](https://github.com/moatus/livepeer-validator-track/issues/17) | `deliverables/m3/option-scenarios.md` |
| [M3.4 — Map any recommended expansion onto the current system](https://github.com/moatus/livepeer-validator-track/issues/13) | `deliverables/m3/integration-map.md` |

## M4 — Bounded economic and work-validation tests

Test the litepaper's consequential assumptions, whatever M3 recommends (if anything), and validator judgments. A small table, calculation or targeted experiment suffices if it answers the question. Useful service-validation tests can begin before every economic choice is settled.

**Completion:** Selected cooperative, market-pressure and adversarial cases; bounded work-integrity, quality or availability tests; and a draft procedure for evidence, uncertainty, disagreement and service failures. Record negative results, reviewer cost and relevant false positives.

| Task | Planned artifact |
| --- | --- |
| [M4.1 — Stress-test consequential economic assumptions](https://github.com/moatus/livepeer-validator-track/issues/18) | `deliverables/m4/economic-test-results.md` |
| [M4.2 — Run bounded service-validation tests](https://github.com/moatus/livepeer-validator-track/issues/19) | `deliverables/m4/service-validation-results.md` |
| [M4.3 — Draft the evidence review and dispute procedure](https://github.com/moatus/livepeer-validator-track/issues/20) | `deliverables/m4/reviewer-procedure.md` |

## M5 — Validator workflow pilot and delivery handoff

Exercise the supported claim-to-review-to-consequence workflow. Identify what the validation track can recommend, what adjacent tracks need, and what requires the separate protocol decision process.

**Completion:** A bounded pilot with limitations, operating responsibilities and cross-track interfaces, and a prioritized backlog separating supported recommendations from unresolved decisions.

| Task | Planned artifact |
| --- | --- |
| [M5.1 — Pilot an end-to-end validator workflow](https://github.com/moatus/livepeer-validator-track/issues/21) | `deliverables/m5/workflow-pilot.md` |
| [M5.2 — Document operating roles and cross-track interfaces](https://github.com/moatus/livepeer-validator-track/issues/22) | `deliverables/m5/operating-handoff.md` |
| [M5.3 — Deliver recommendations and implementation backlog](https://github.com/moatus/livepeer-validator-track/issues/23) | `deliverables/m5/recommendations-and-backlog.md` |

## Reporting and scope

M1 and M2 artifacts are steps of the research workbench; a reviewed version is recorded by commit. Planned paths for later milestones become links only after artifacts exist. Record source versions, assumptions, findings, limits and reviewed artifact versions in task issues and the [deliverable register](deliverables/README.md). Add research, models and test results here as reviewable artifacts. Keep findings, recommendations and protocol decisions distinct. Update this overview when accepted artifacts or milestone decisions change. Confirm dates before setting native milestone due dates.
