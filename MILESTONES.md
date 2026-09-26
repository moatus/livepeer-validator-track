# Milestone overview

Owner: Shane (@moatus). [Project board](https://github.com/users/moatus/projects/1). Target dates are **to agree**. M1 is in progress; M2–M5 are planned. No research deliverables have been accepted yet.

Research path: **understand the litepaper → test its assumptions → develop the validator-track expansion → test the expansion → hand off a validator workflow**. The expansion gives the litepaper's goals and mechanisms more detail, with proposed additions grounded in evidence. Work may overlap across milestones.

| Milestone | Intended outcome | Tracking | Target date | Accepted deliverables |
| --- | --- | --- | --- | --- |
| [M1 — Objectives, assumptions and validation requirements](https://github.com/moatus/livepeer-validator-track/milestone/1) | Baseline, required claims, early threats and current-system map. | [#1](https://github.com/moatus/livepeer-validator-track/issues/1) | To agree | None |
| [M2 — Test litepaper incentives and evidence limits](https://github.com/moatus/livepeer-validator-track/milestone/2) | Substantiate material concerns and evidence limits. | [#2](https://github.com/moatus/livepeer-validator-track/issues/2) | To agree | None |
| [M3 — Litepaper expansion and integration map](https://github.com/moatus/livepeer-validator-track/milestone/3) | Develop and assess an economic and validation expansion of the litepaper. | [#3](https://github.com/moatus/livepeer-validator-track/issues/3) | To agree | None |
| [M4 — Bounded economic and work-validation tests](https://github.com/moatus/livepeer-validator-track/milestone/4) | Test consequential assumptions and reviewer methods. | [#4](https://github.com/moatus/livepeer-validator-track/issues/4) | To agree | None |
| [M5 — Validator workflow pilot and delivery handoff](https://github.com/moatus/livepeer-validator-track/milestone/5) | Exercise a bounded workflow and hand off supported recommendations. | [#5](https://github.com/moatus/livepeer-validator-track/issues/5) | To agree | None |

## M1 — Objectives, assumptions and validation requirements

Use the Livepeer 2.0 litepaper as the design foundation. Separate its desired outcomes from proposed mechanisms and assumptions. Explain the intended cooperative flow of payments, rewards, costs and participant incentives. Identify claims reward eligibility relies on, what evidence could establish them, and where even perfect execution evidence would leave an economic problem. Inspect current Livepeer components enough to show the scale of the litepaper's changes.

**Completion:** A concise baseline map, claim/evidence decision note, representative attack and legitimate scenarios, and a versioned current-system → litepaper impact map covering contracts, off-chain components and participant roles. Mark unresolved choices and unknowns.

| Task | Planned artifact |
| --- | --- |
| [M1.1 — Map litepaper objectives, mechanisms and incentives](https://github.com/moatus/livepeer-validator-track/issues/6) | `deliverables/m1/litepaper-baseline-map.md` |
| [M1.2 — Determine what reward eligibility needs to establish](https://github.com/moatus/livepeer-validator-track/issues/7) | `deliverables/m1/claim-evidence-decision-note.md` |
| [M1.3 — Define adversarial scenarios and legitimate lookalikes](https://github.com/moatus/livepeer-validator-track/issues/8) | `deliverables/m1/initial-threat-scenarios.md` |
| [M1.4 — Map the current system to the litepaper](https://github.com/moatus/livepeer-validator-track/issues/14) | `deliverables/m1/current-to-litepaper-impact-map.md` |

## M2 — Test litepaper incentives and evidence limits

Use small worked examples to test the litepaper's material economic assumptions. Begin with intended cooperative behavior, then vary a pivotal condition or strategic action. Stop when an example supports or rejects the specific concern; a full network simulation is unnecessary. Examine only evidence relevant to those concerns.

**Completion:** Reproducible examples with explicit assumptions and limits, a focused assessment of what validators can observe, and a findings register linking litepaper provisions, assumptions, evidence, current-system implications and design questions. Distinguish modeled vulnerability from observed prevalence.

| Task | Planned artifact |
| --- | --- |
| [M2.1 — Test litepaper incentives with bounded examples](https://github.com/moatus/livepeer-validator-track/issues/10) | `deliverables/m2/litepaper-incentive-examples.md` |
| [M2.2 — Assess evidence for material claims and scenarios](https://github.com/moatus/livepeer-validator-track/issues/9) | `deliverables/m2/focused-evidence-assessment.md` |
| [M2.3 — Consolidate findings and design requirements](https://github.com/moatus/livepeer-validator-track/issues/15) | `deliverables/m2/findings-and-requirements.md` |

## M3 — Litepaper expansion and integration map

Explore additions that give the litepaper's economic and validation goals practical form: reward integrity, open market participation, participant incentives, credible validation and implementation. Develop a proposed expansion with explicit roles and unresolved decisions. Model scenarios only where they clarify a design choice or failure boundary.

**Completion:** An assessment of possible additions to the litepaper; a proposed validator-track expansion; small cooperative, ordinary-market and selected adversarial scenarios or equivalent worked cases; and an integration map tracing **current system → litepaper**, **litepaper → expanded design** and **current system → expanded design** across contracts, off-chain components, workflows and migration considerations. Identify what M4 should test and where an addition needs a corresponding adjustment to an existing mechanism.

| Task | Planned artifact |
| --- | --- |
| [M3.1 — Explore economic and validation additions to the litepaper](https://github.com/moatus/livepeer-validator-track/issues/11) | `deliverables/m3/expansion-options.md` |
| [M3.2 — Develop the litepaper expansion and participant incentives](https://github.com/moatus/livepeer-validator-track/issues/12) | `deliverables/m3/litepaper-expansion.md` |
| [M3.3 — Explore expanded design scenarios and test priorities](https://github.com/moatus/livepeer-validator-track/issues/17) | `deliverables/m3/expansion-scenarios.md` |
| [M3.4 — Map the litepaper expansion onto the current system](https://github.com/moatus/livepeer-validator-track/issues/13) | `deliverables/m3/expansion-integration-map.md` |

## M4 — Bounded economic and work-validation tests

Test consequential assumptions of the proposed litepaper expansion and validator judgments. A small table, calculation or targeted experiment suffices if it answers the question. Useful service-validation tests can begin before every economic choice is settled.

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

Planned paths become links only after artifacts exist. Record source versions, assumptions, findings, limits and reviewed artifact versions in task issues and the [deliverable register](deliverables/README.md). Add research, models and test results here as reviewable artifacts. Keep findings, recommendations and protocol decisions distinct. Update this overview when accepted artifacts or milestone decisions change. Confirm dates before setting native milestone due dates.
