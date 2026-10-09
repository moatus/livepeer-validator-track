# EX-04: evidence before the claim, self-funded jobs beside release testing

**Historical September evidence tabletop.** All `SRC-LP20` line citations refer to the [archived September source](../../../docs/sources/litepaper-2026-09.md). Packets, tolerances and verdicts retain their original scope and are not a test of October. The payment/execution-versus-purpose distinction transfers as a question; October constitution, governance and claim-time provisions require fresh rule mapping before carrying verdicts forward. See the [October reconciliation](../october-reconciliation/README.md).

Status: **Drafted**. This is a synthetic evidence comparison for M2.2/GT-01, with judgments checked by hand. Structural verification is not a deployed validation result or approved scoring policy.

## Task and question

Can a validator distinguish SC-07 self-funded real jobs from SC-23 release testing by the paper-proposed first claim at n+7, under the two self-dealing standards (I-20/I-21) and both adverse-judgment readings (I-22), within the previously fixed error, review and disclosure tolerances?

The allegations are stated first in [tolerances.md](tolerances.md) and the [packet](packets/sc07-sc23.md). Narrow rows use the explicitly labelled SC-07 purpose-misrepresentation variant. Unmodified SC-07 has no specified narrow conduct; its transparent real self-payment is not silently recast as deception. Whether the reward objective needs the broad distinction remains I-01/VD-19 and GT-03's separate question.

## Source versions

- Primary source: Doug Petkanics, *Livepeer 2.0 Litepaper*, September 2026, SRC-LP20. Snapshot SHA-256, matching EX-01: `5fc153408fb636d9750788ae987ada6daaa9fc3df3e44f70cadde51a6158fb71`. Relevant lines: L47, L53, L83–88, L109, L111–119, L172, L196, L224.
- Existing current-system counterparts, via CS-03/18/21/32: SRC-GOLP commit `9e68815adf5e72b9c285f178bcdd25b42211efbb`; SRC-PROTOCOL commit `e02052a04bde9ba1b3bb187d84209e4592e74cad`, Solidity-tree content hash `168030ca5c7081d4fa3856b14959360735024df84ddc64953ed0fa05525e6ff5`. The packet gives exact source paths. These maps describe inspected source, not demonstrated deployed behavior or a USDC evidence feed.
- Shared interpretation inputs: M2.1 I-01, I-16/I-17, I-19–I-22; CN-22; SC-07/23; CL-01/02/03/05/06/07; VD-09/19. No new current-system inspection or economic computation is claimed.
- Tolerances were fixed in their own preceding commit `3019f43`, before these outcomes. Their SHA-256 is `da37fa01ac0252792e2dd365219f7996ff2d7ca43c63e2c1abeb6cd0d4869681`; they are unchanged.

## Inputs and method

All packet contents, arrival times, source authenticity, available common-control information and competent checks are illustrative assumptions. The order is legitimate SC-23 testing followed by reward-only SC-07, with the added misrepresentation only under the narrow standard. Public evidence establishes payment, execution and correctness. One extra source is SC-23's selectively disclosed release plan plus resulting change, arriving at illustrative n+5. SC-07 supplies no internal explanation by n+7; silence is not proof of its purpose.

Read the packet in arrival order. Compare public records with public records plus that single source. Each record kind cites the paper, an existing current-system source path or **not specified by the paper**. Judge the six prescribed claims separately. Apply reading (a), evidence required, and reading (b), non-explanation may warrant a cut, without converting an evidential unknown into a dishonesty finding.

[matrix.csv](matrix.csv) has the exact prescribed columns and one row per case × standard × level × claim; its evidence values apply to both readings. SC-07/narrow denotes the labelled variant. [verdicts.csv](verdicts.csv) preserves the exact prescribed columns; its `note` begins `reading=a;` or `reading=b;`, supplying both readings without an extra column. Thus each standard/level has separate verdict rows. `arrival_round` is the latest relied-on arrival or the observation cutoff for an unknown, not a claim that absent evidence arrived.

## Results against the fixed tolerances

| Standard | Evidence level | Reading (a) | Reading (b) |
| --- | --- | --- | --- |
| Narrow, labelled variant | public | does not separate | does not separate |
| Narrow, labelled variant | public+disclosed | does not separate | does not separate; procedural consequence in the note |
| Broad | public | does not separate | does not separate |
| Broad | public+disclosed | does not separate | does not separate; procedural consequence in the note |

| Standard and reading | False cut (strict) | Missed violation | Effort and disclosure ceilings |
| --- | --- | --- | --- |
| Narrow (a), Broad (a) | Met at both levels: no cut on SC-23 or unmodified SC-07 | No violation is established at either level; the unresolved allegation is the tolerance's accepted limitation, not an effective defense | Routine review only at public; bounded review and redacted D1 only at disclosed, by construction |
| Narrow (b), Broad (b), public | Not met: non-explanation can cut legitimate SC-23, and unmodified SC-07 under narrow | No violation is established; a cut would not show detection | Routine review; no disclosure supplied |
| Narrow (b), Broad (b), public+disclosed | Met for SC-23 only if D1 is authentic, adequate, safe and in time; not met for an unexplained legitimate job, and not for unmodified SC-07 under narrow | No violation is established; a cut on unexplained SC-07 would not show detection | Within the ceilings by construction; feasibility unmeasured |

No cell establishes the SC-07 violation, so none shows that a defined violation can be established at acceptable error, effort and timing; the only established change at the disclosed level is that D1 clears SC-23. Whether enough validators would act on such evidence is a separate inquiry.

Payment, execution and correctness are established in every controlled cell. Independent demand is contradicted under the trustworthy common-control assumption, without imposing independent-customer eligibility. Economic value remains unknown. The selected dishonesty claim is unknown at public level. Disclosure contradicts that allegation against SC-23 under both standards, while SC-07 remains unknown, including falsity and knowledge in the narrow variant.

Under (a), missing proof is an accepted inquiry limitation, not a successful defense. D1 can protect legitimate testing but does not establish the alleged violation. Under (b), public-only cuts can reach SC-23 and fail the strict false-cut tolerance. With timely adequate D1, reading (b) would spare SC-23 and permit a cut on unexplained SC-07. That cut answers non-explanation, not evidence of the violation, and the same rule would cut any job whose legitimate explanation stays undisclosed. No level, standard or reading establishes the SC-07 violation, so every verdict is "does not separate". The readings differ in who is exposed to a cut, not in what the evidence supports. Disclosure is one-sided: D1 exists for SC-23 and the packet supplies no purpose source for SC-07. Applying (b) to unmodified SC-07 solely for silence would also fail the narrow false-cut tolerance.

The disclosed branch fits the bounded question/response and redacted-source ceilings by construction. Authenticity, safe disclosure and feasibility by n+7 remain conditions, not measured accomplishments. No score-to-median response, empirical detection probability or eventual correction is assumed.

## Limits and next dependencies

Synthetic packets test logical support; they do not measure accuracy, reviewer time, privacy cost, source access, prevalence or dispute incidence. This pair cannot establish universal inability to distinguish jobs. A release plan does not price subsidy value or settle I-01. The paper's delay and shared investigation retain their intended uses: time for actionable evidence and less duplicated investigation, conditional on evidence reaching reviewers. They do not make internal purpose records publicly available. Validator effort incentives and social costs belong to later inquiries; economic significance and the need for different treatment pass to M2.3.

## Reproduce

From the repository root, Python 3.10+ with the standard library only:

```bash
python3 experiments/m2/evidence-self-funded/verify.py
```

The verifier reads beside itself, checks exact schemas, nonempty cells, allowed values, source-locator syntax, duplicate keys, complete paired claim coverage, both reading labels and complete verdict coverage. It does not compute or validate the judgments, prove citations substantively correct, time review or inspect hidden purpose. It writes no outputs. Defaults reflect the prescribed standards, levels and claims; the optional `--readings` argument supports reuse of the same schema where an inquiry carries a different set of reading labels.
