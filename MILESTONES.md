# Milestone overview

Owner: Shane (@moatus). [Project board](https://github.com/users/moatus/projects/1). M1 September versions are reviewed; October revisions remain drafted. M2 is complete. M3 closed on 2026-11-13 as an evidence assessment and testnet handoff: M3.1 reviewed, M3.2 accepted only as a bounded contribution with its source still partial, and M3.3/M3.4 deferred. The plan was revised on 2026-11-18: M4 is the launched testnet, M5 is testnet simulation, M6 is an agent-run contribution pipeline, and the validation campaigns that need a running testnet are deferred to 2027. Testnet results are not yet accepted. The original M5 is archived. Exact evidence and limits are in the [deliverable register](deliverables/README.md).

Research path: **understand the litepaper → test its assumptions → assess evidence and unresolved gaps → establish and test the litepaper baseline**. Expansion options remain open and return to evaluation when concrete proposals are ready for testing. Work may overlap across milestones.

| Milestone | Intended outcome | Tracking | Budget (USD) | Accepted deliverables |
| --- | --- | --- | ---: | --- |
| [M1 — Objectives, assumptions and validation requirements](https://github.com/moatus/livepeer-validator-track/milestone/1) | Baseline, required claims, early threats and current-system map. | [#1](https://github.com/moatus/livepeer-validator-track/issues/1) | — | [M1.1–M1.4](deliverables/README.md) |
| [M2 — Test litepaper incentives and evidence limits](https://github.com/moatus/livepeer-validator-track/milestone/2) | Substantiate material concerns and evidence limits. | [#2](https://github.com/moatus/livepeer-validator-track/issues/2) | $800 | [M2.1–M2.10 and shared snapshot](deliverables/README.md) |
| [M3 — Evidence assessment and testnet handoff](https://github.com/moatus/livepeer-validator-track/milestone/3) | Evidence assessment and testnet handoff; no expansion selected. | [#3](https://github.com/moatus/livepeer-validator-track/issues/3) | $1,200 | M3.1 reviewed; M3.2 bounded contribution accepted |
| [M4 — Launched economic testnet](https://github.com/moatus/livepeer-validator-track/milestone/4) | Launch the litepaper baseline as a public testnet with a reconciled reward cycle, buy-and-burn and an outside operator. | [#4](https://github.com/moatus/livepeer-validator-track/issues/4) | $9,000 | None |
| [M5 — Testnet simulation](https://github.com/moatus/livepeer-validator-track/milestone/6) | Switchable, parameter-driven simulated activity on the testnet. | [#44](https://github.com/moatus/livepeer-validator-track/issues/44) | Not set | None |
| [M6 — Agent-run contribution pipeline](https://github.com/moatus/livepeer-validator-track/milestone/7) | Outside contributions checked, reviewed and summarized by agents for human maintainers. | [#47](https://github.com/moatus/livepeer-validator-track/issues/47) | Not set | None |

**Total M2–M4 budget: $11,000 USD.** Budgets for M5 and M6 are not set in the 2026-11-18 revision. Target dates: M2 2026-10-19 (completed 2026-10-27), M3 2026-11-22, M4 2026-12-31, M5 2026-12-31, M6 2027-01-31. The board and native milestones mirror these dates.

## M1 — Objectives, assumptions and validation requirements

Use the October Livepeer 2.0 litepaper as the current design foundation. Preserve the reviewed September versions and their source-scoped results; October amendments are drafted until reviewed. Separate its desired outcomes from proposed mechanisms and assumptions. Explain the intended cooperative flow of payments, rewards, costs and participant incentives. Examine each mechanism for what its success depends on that is not yet established, including the claims reward eligibility relies on, what evidence could establish them, and where even perfect execution evidence would leave an economic problem. Inspect current Livepeer components enough to show the scale of the litepaper's changes.

**Completion:** A baseline of the twelve mechanisms; a pass through each mechanism with eight lenses (calculation, observation, inference, policy and authority, individual incentives, collective behaviour, social and operational effects, and system feedback), with proposed critical questions wherever its success depends on something not yet established; representative attack and legitimate scenarios; and a versioned current-system → litepaper impact map covering contracts, off-chain components and participant roles. Mark unresolved choices and unknowns.

| Task | Artifact | Status |
| --- | --- | --- |
| [M1.1 — Map litepaper objectives, mechanisms and incentives](https://github.com/moatus/livepeer-validator-track/issues/6) | Workbench step M1.1, "How the architecture works, mechanism by mechanism" | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/2c697f9f5b29911d2fb26fa5b26d76c61f5fdc1a/validator-track-workbench.html) (`2c697f9`) |
| [M1.2 — Identify what each mechanism depends on and its critical questions](https://github.com/moatus/livepeer-validator-track/issues/7) | Workbench step M1.2, "What each mechanism depends on, and its critical questions" | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/2c697f9f5b29911d2fb26fa5b26d76c61f5fdc1a/validator-track-workbench.html) (`2c697f9`) |
| [M1.3 — Define adversarial scenarios and legitimate lookalikes](https://github.com/moatus/livepeer-validator-track/issues/8) | Workbench step M1.3, "Which cases matter most" | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/2c697f9f5b29911d2fb26fa5b26d76c61f5fdc1a/validator-track-workbench.html) (`2c697f9`) |
| [M1.4 — Map the current system to the litepaper](https://github.com/moatus/livepeer-validator-track/issues/14) | Workbench step M1.4, "What exists today, and what would need to be built" | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/2c697f9f5b29911d2fb26fa5b26d76c61f5fdc1a/validator-track-workbench.html) (`2c697f9`) |

## M2 — Test litepaper incentives and evidence limits

Reassemble the mechanisms from the M1 handoff into one system: participants and their overlapping roles, their choices, information, timing and payoffs. Rank what to test. Then test the critical questions in that order, with small economic examples and focused evidence inquiries. Begin with intended cooperative behavior, then vary a pivotal condition or strategic action. Stop when a test supports or rejects the specific concern; a full network simulation is unnecessary. Examine only evidence relevant to those concerns.

**Completion:** A reconstruction of the combined system with a ranked list of what to test; one shared, network-grounded scenario ledger connecting capability entry, prices, outside demand/routing, controlled purchases, unit costs, stake, commissions and scores, reporting jobs, fees, participant income, burn, actual issuance and unminted allowance; reproducible economic examples and focused evidence inquiries with explicit assumptions and limits, including what validators can observe; and a consolidated record of what the tests show and what would resolve each concern (a specification, better evidence, a change in incentives or a policy choice), linking litepaper provisions, assumptions, evidence, current-system implications and design questions. Distinguish modeled vulnerability from observed prevalence. Hand M3 the concerns that remain unresolved and the areas the paper leaves unaddressed.

| Task | Artifact | Status |
| --- | --- | --- |
| [M2.1 — Reconstruct how the mechanisms behave together](https://github.com/moatus/livepeer-validator-track/issues/10) | Workbench step M2.1, "How the mechanisms behave together" | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/92120477015ed16ccf15e7a9cc396e497bd191a7/validator-track-workbench.html) (`9212047`); later slices add to this page |
| [M2.2 — Test the critical questions](https://github.com/moatus/livepeer-validator-track/issues/9) | Workbench step M2.2, "Testing the critical questions" | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/92120477015ed16ccf15e7a9cc396e497bd191a7/validator-track-workbench.html) (`9212047`); later slices add to this page |
| [M2.3 — Consolidate findings and design requirements](https://github.com/moatus/livepeer-validator-track/issues/15) | Workbench step M2.3, "What would resolve each concern?" | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/92120477015ed16ccf15e7a9cc396e497bd191a7/validator-track-workbench.html) (`9212047`); later slices add to this page |
| [M2.4 — Slice 1: self-funded real usage (September)](https://github.com/moatus/livepeer-validator-track/issues/26) | Slice 1: EX-03, EX-04, EX-05 and workbench additions | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/92120477015ed16ccf15e7a9cc396e497bd191a7/validator-track-workbench.html) (`9212047`) |
| [M2.5 — Slice 2: capability, pricing and self-funded traffic](https://github.com/moatus/livepeer-validator-track/issues/27) | Slice 2: EX-06, EX-07 and workbench additions | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/92120477015ed16ccf15e7a9cc396e497bd191a7/validator-track-workbench.html) (`9212047`) |
| [M2.6 — Slice 2b: strategic self-funding across network conditions](https://github.com/moatus/livepeer-validator-track/issues/28) | Slice 2b: EX-08 and workbench additions | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/92120477015ed16ccf15e7a9cc396e497bd191a7/validator-track-workbench.html) (`9212047`) |
| [M2.7 — P1: current-system data notes](https://github.com/moatus/livepeer-validator-track/issues/29) | [EX-09](https://github.com/moatus/livepeer-validator-track/tree/229bb1a9ebff4cce7300e5f119002e23436f4c03/experiments/m2/current-system-data-notes) and workbench additions | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/229bb1a9ebff4cce7300e5f119002e23436f4c03/validator-track-workbench.html) (`229bb1a`) |
| [M2.8 — E2: evidence and operator response](https://github.com/moatus/livepeer-validator-track/issues/30) | [EX-10](https://github.com/moatus/livepeer-validator-track/tree/ca44c8d67e57c32882003261c22f62dddb28bb3c/experiments/m2/evidence-operator-response) and workbench additions | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/ca44c8d67e57c32882003261c22f62dddb28bb3c/validator-track-workbench.html) (`ca44c8d`) |
| [M2.9 — Slice 3: validator scoring](https://github.com/moatus/livepeer-validator-track/issues/31) | [EX-11](https://github.com/moatus/livepeer-validator-track/tree/6029c6163034ac0f7a81c1bac0ec189f1576d35c/experiments/m2/validator-scoring) and workbench additions | [Reviewed](https://github.com/moatus/livepeer-validator-track/blob/6029c6163034ac0f7a81c1bac0ec189f1576d35c/validator-track-workbench.html) (`6029c61`) |
| [M2.10 — M2 consolidation pass](https://github.com/moatus/livepeer-validator-track/issues/32) | [Complete workbench assessment](https://github.com/moatus/livepeer-validator-track/blob/14e457e5434d615fa444ae406d88510da5a16c51/validator-track-workbench.html) and [EX-12](https://github.com/moatus/livepeer-validator-track/tree/14e457e5434d615fa444ae406d88510da5a16c51/experiments/m2/consolidation) | Reviewed and accepted ([`14e457e`](https://github.com/moatus/livepeer-validator-track/commit/14e457e5434d615fa444ae406d88510da5a16c51)) |

M2 closed after acceptance of the final assessment and [shared snapshot](https://github.com/moatus/livepeer-validator-track/blob/14e457e5434d615fa444ae406d88510da5a16c51/experiments/m2/network-snapshot/livepeer-arbitrum-2026-10-09-v1.json). Unresolved questions pass to M3/M4; closure does not adopt protocol rules.

The [M2 specification](docs/m2/SPEC.md) preserves every study identity. The M2 framework and Slices 1, 2 and 2b were reviewed. Specification 0.11 consolidates the remaining program into P1 (current-system data notes), E2 (evidence, with operator response), Slice 3 and a close pass, each tracked as a task issue. Studies 4–8 keep their identities: study 4 is merged into E2, and studies 5–8 receive dispositions in the close pass.

## M3 — Evidence assessment and testnet handoff

**Closed 2026-11-13, revised scope approved by Shane.** M3 closes under a revised scope: the gap assessment is reviewed, the available prototype findings and limitations are recorded, and the next testnet questions are identified. No expansion mechanism has been selected or validated. Broader option comparisons, expansion scenarios and expansion integration mapping remain deferred. M4 will establish and test the litepaper baseline.

**Original completion criteria (preserved, not all met):** A list of the unresolved concerns, gaps and conflicts, with the evidence for each; an evaluation of the options for each, with participant incentives and a recommendation; small cooperative, ordinary-market and selected adversarial scenarios, or equivalent worked cases, for the options worth pursuing; and, for any recommended expansion, an integration map tracing **current system → litepaper**, **litepaper → recommended expansion** and **current system → recommended expansion** across contracts, off-chain components, workflows and migration considerations. Identify what M4 should test, and where a recommendation adjusts an existing mechanism.

**Revised completion:** the reviewed gap assessment at an exact version; the bounded prototype findings and limitations accepted as input to M4; linked exploratory economic models without new validation claims; and explicit gap dispositions and return conditions below. The original option/incentive comparison remains partial. This scope change does not conclude that no expansion is needed.

| Task | Artifact or disposition | Status |
| --- | --- | --- |
| [M3.1 — Gap assessment](https://github.com/moatus/livepeer-validator-track/issues/11) | [Workbench M3.1](https://github.com/moatus/livepeer-validator-track/blob/1f096b7a8a23476c8a875ef826b31f7330265895/validator-track-workbench.html), `1f096b7` | Reviewed by Shane; complete |
| [M3.2 — Prototype findings and limitations](https://github.com/moatus/livepeer-validator-track/issues/12) | [Workbench M3.2](https://github.com/moatus/livepeer-validator-track/blob/1f096b7a8a23476c8a875ef826b31f7330265895/validator-track-workbench.html), `1f096b7` | Bounded contribution accepted; source Drafted (partial); broader evaluation unfinished |
| [M3.3 — Expansion scenarios](https://github.com/moatus/livepeer-validator-track/issues/17) | No completed expansion scenarios | Deferred; closed as not planned |
| [M3.4 — Expansion integration map](https://github.com/moatus/livepeer-validator-track/issues/13) | No completed expansion integration map | Deferred; closed as not planned |

Revisit the unfinished comparisons, scenarios and integration mapping when a concrete expansion is selected for testing. Baseline implementation and test cases do not fulfill those expansion deliverables. The [PoC index](https://github.com/moatus/livepeer-validator-track/blob/1f096b7a8a23476c8a875ef826b31f7330265895/poc/README.md) and [exploratory models](https://github.com/moatus/livepeer-validator-track/blob/1f096b7a8a23476c8a875ef826b31f7330265895/experiments/m3/README.md) retain their stated limits. No combined integrity/QoS scoring mechanism is selected.

### Gap dispositions

Task references in the last column were updated on 2026-11-18 to follow the revised plan; the dispositions themselves are unchanged.

| Gap | Disposition for the initial testnet | Next work or return condition |
| --- | --- | --- |
| G01 — Reward objective and self-funded work | Keep the October baseline and measure its conditional exposure. Evidence of real execution does not resolve the reward incentive. Whether the reward objective must change remains open. | Deferred to 2027: [#18](https://github.com/moatus/livepeer-validator-track/issues/18); revisit expansion options when results support a concrete proposal. |
| G02 — Job evidence and collection | Test bounded request/delivery records and claim-specific checks; evidence custody, cost and coverage remain unresolved. | Deferred to 2027: [#19](https://github.com/moatus/livepeer-validator-track/issues/19). |
| G03 — Credible review and operator response | Measure actual evidence access and review on known cases; scripted scores do not demonstrate credible judgment. | Deferred to 2027: [#19](https://github.com/moatus/livepeer-validator-track/issues/19), [#20](https://github.com/moatus/livepeer-validator-track/issues/20). |
| G04 — Delegation, liquidity and control | State the test profile's stake/authority rules and test their consequences. Neither beneficial control nor a policy resolution is established. | Deferred to 2027: [#18](https://github.com/moatus/livepeer-validator-track/issues/18); exercise supported staking/unbonding paths, with bond transfers deferred. |
| G05 — Service quality and availability | Combined integrity/QoS scoring remains a direction to evaluate, not a selected mechanism. Keep service performance distinct from dishonesty. | Bounded claim tests deferred to 2027: [#19](https://github.com/moatus/livepeer-validator-track/issues/19); any combined reward mechanism needs a later option comparison. |
| G06 — Supply before demand | No protocol change proposed for the initial testnet; whether commercial provision suffices remains untested. | Retain in the M4.4 results index ([#39](https://github.com/moatus/livepeer-validator-track/issues/39)); revisit when a concrete unmet service need is evidenced. |
| G07 — Practical discovery | No protocol change proposed for the initial testnet; practical access and commercial adequacy remain untested. | Retain in the M4.4 results index ([#39](https://github.com/moatus/livepeer-validator-track/issues/39)); revisit with operator/customer discovery evidence. |
| G08 — Buyer remedies | No protocol change proposed for the initial testnet; adequacy of commercial remedies remains untested. | The deferred dispute-procedure task ([#20](https://github.com/moatus/livepeer-validator-track/issues/20), 2027) can expose response gaps; retain unresolved remedy design in the M4.4 results index ([#39](https://github.com/moatus/livepeer-validator-track/issues/39)). |
| G09 — Rules and pending rewards | Explicitly state and exercise the test profile's applicability and authority rules. No new protocol policy is adopted by this closeout. | M4.2 ([#38](https://github.com/moatus/livepeer-validator-track/issues/38)) and M4.3 ([#43](https://github.com/moatus/livepeer-validator-track/issues/43)). |
| G10 — Executable buybacks | Execute purchase and burn through a declared controlled test pool. Real-market liquidity and manipulation resistance remain untested. | M4.3 ([#43](https://github.com/moatus/livepeer-validator-track/issues/43)); preserve GT-10 in the deferred economic campaign ([#18](https://github.com/moatus/livepeer-validator-track/issues/18)) and the M4.4 results index ([#39](https://github.com/moatus/livepeer-validator-track/issues/39)) for 2027 or later. |

## M4 — Launched economic testnet

**Revised 2026-11-18 at Shane's direction.** M4 now covers the launched testnet alone, in four dated steps. The economic stress campaign, the service-evidence and reviewer tests and the dispute procedure depend on a running testnet and are deferred to 2027 (below). The evidence package is the closing checklist of M4.4, not a separate task. Budget: **$9,000**; target: **2026-12-31**.

Status at 2026-11-18: the implementation team reports the local paid-job path and local reward cycle complete (M4.1). Their source is not yet public, and no M4 result is reviewed or accepted.

| Task | Expected outcome | Target |
| --- | --- | --- |
| [M4.1 — Run a paid node and a full reward cycle locally](https://github.com/moatus/livepeer-validator-track/issues/42) | A stake-free node paid in test USDC and a full reward cycle reconciled against the independent calculator, on a local chain | Closes with M4.2 |
| [M4.2 — First public deployment](https://github.com/moatus/livepeer-validator-track/issues/38) | Contracts on Arbitrum Sepolia; a team-run node paid; one reward cycle reconciled; implementation source public and its demonstration runnable from the published instructions | 2026-12-01 |
| [M4.3 — Close the loop and survive trouble](https://github.com/moatus/livepeer-validator-track/issues/43) | Controlled-pool purchase and burn; accounting reconciles after a key rotation, a restart during settlement and a parameter change; redeployed | 2026-12-08 |
| [M4.4 — Outside operators](https://github.com/moatus/livepeer-validator-track/issues/39) | At least one operator outside the implementation team registers, is paid and claims; balances reconcile; results index with limits and open decisions | 2026-12-15 |

Task numbers changed in this revision: the former M4.4 is M4.2, the former M4.5 is split between M4.3 and M4.4, and the former M4.6 ([#40](https://github.com/moatus/livepeer-validator-track/issues/40)) is closed as not planned and folded into M4.4.

Try the unmodified node first, documenting minimal required changes if necessary. Scripted scores test accounting and reward consequences, not judgment quality. A declared controlled test pool must execute purchase and burn of test LPT; merely holding the network fee share is insufficient. This does not demonstrate real-market liquidity or manipulation resistance. List all test-profile interpretations, deviations and stand-ins. No expansion-specific mechanism is selected by this plan.

Upgradeability, real-market DEX buyback validation, Explorer/subgraph integration and bond transfers are deferred to 2027 or later. Preserve GT-10 in the M4.4 results index; controlled-pool accounting does not close it. Expansion-specific scenarios and integration mapping return when an expansion is selected for testing.

## M5 — Testnet simulation

Added 2026-11-18 at Shane's direction; target **2026-12-31**; budget not set in this revision. Give the testnet simulated activity that can be switched on and off, driven by parameters, with simulated work in place of real compute. The aim is to open the way to economic simulations on the testnet, especially of validation. Work has not started.

| Task | Expected outcome | Target |
| --- | --- | --- |
| [M5.1 — Build the simulator and run it locally](https://github.com/moatus/livepeer-validator-track/issues/45) | A stand-in model service with settings for delay, failure and wrong answers; many participants driven by one scenario file; a local run reconciled against the independent calculator | 2026-12-22 |
| [M5.2 — Run a live simulation on the testnet](https://github.com/moatus/livepeer-validator-track/issues/46) | The same scenarios run as a campaign on the public testnet, can be started and stopped, with a public read-only view | 2026-12-31 |

Simulated work establishes nothing about service quality, and simulated activity is labelled as such. A client for outside participants is not in this milestone. Overview: [#44](https://github.com/moatus/livepeer-validator-track/issues/44).

## M6 — Agent-run contribution pipeline

Added 2026-11-18 at Shane's direction; target **2027-01-31**; budget not set in this revision. Let outside contributors open pull requests and issues against the testnet implementation, with an agent-run process that checks, reviews and summarizes each one for human maintainers. Work has not started.

| Task | Expected outcome | Target |
| --- | --- | --- |
| [M6.1 — Open a public contribution path](https://github.com/moatus/livepeer-validator-track/issues/48) | Outside pull requests accepted, checked automatically, with a contributor guide | 2027-01-15 |
| [M6.2 — Automated review report on every pull request](https://github.com/moatus/livepeer-validator-track/issues/49) | A report for maintainers on each pull request: what changed, what the checks and review found, what was not checked | 2027-01-22 |
| [M6.3 — Automated issue triage](https://github.com/moatus/livepeer-validator-track/issues/50) | Each issue classified, reproduced where possible, labelled and answered | 2027-01-29 |

Outside content is assessed, never treated as instructions. Checks on outside code run without credentials or write access. Automation has spending limits. A human maintainer decides what is merged. Agent-drafted fixes are a later step, not scheduled. Overview: [#47](https://github.com/moatus/livepeer-validator-track/issues/47).

## 2027 — Validation campaigns on the testnet

Deferred from M4 on 2026-11-18. These tasks stay open under the [2027 milestone](https://github.com/moatus/livepeer-validator-track/milestone/8) with the `deferred-2027` label; nothing in them has been run or accepted, and no dates or budget are set.

| Task | Expected outcome |
| --- | --- |
| [Economic stress campaign](https://github.com/moatus/livepeer-validator-track/issues/18) (former M4.1) | Cooperative, ordinary-market and strategic cases, including self-funded work and supported stake movement |
| [Service-evidence and reviewer tests](https://github.com/moatus/livepeer-validator-track/issues/19) (former M4.2) | Actual claim checks and reviewer performance, distinct from predetermined scores |
| [Evidence review and dispute procedure](https://github.com/moatus/livepeer-validator-track/issues/20) (former M4.3) | A bounded exercised procedure, operator response and unresolved authority/cost questions |

## Former M5 — Archived

Archived 2026-11-13 at Shane's direction; original work is retained in [#5](https://github.com/moatus/livepeer-validator-track/issues/5) and its tasks, closed as not planned. A broader validator workflow pilot is deferred until a concrete workflow is ready for external testing. Archival is not acceptance of the original M5 criteria. The number M5 was reused on 2026-11-18 for the unrelated simulation milestone above.

## Reporting and scope

M1 and M2 artifacts are steps of the research workbench; a reviewed version is recorded by commit. Planned paths for later milestones become links only after artifacts exist. Record source versions, assumptions, findings, limits and reviewed artifact versions in task issues and the [deliverable register](deliverables/README.md). Add research, models and test results here as reviewable artifacts. Keep findings, recommendations and protocol decisions distinct. Update this overview when accepted artifacts or milestone decisions change. Scheduling changes belong on the project board.
