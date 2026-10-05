# M2 runbook

Version **0.5 · 2026-10-05**. Status: **drafted**. Owner: Shane (@moatus).

How M2 work is picked up, carried out, reviewed, handed on and improved. What M2 must produce, and Slice 1 in detail, are in the [specification](SPEC.md). Different agents may run different stages; this runbook is written so that each can start cold.

## 0. Read first, in this order

1. Your agent context file, if the workspace provides one, and this repository's [README](../../README.md).
2. This runbook in full.
3. The [specification](SPEC.md): §1–4, then your slice's section.
4. The slice's run log, `../validator-track-runs/m2/slice-NN.md` relative to the main clone (local, outside the public repository; §7.4): its status table, the previous stage's handoff note, and any open review findings.
5. The workbench Conventions page: `python3 validator-track-workbench-tools/vtw.py show validator-track-workbench.html Conventions`.
6. The records your stage lists as inputs, read with `vtw.py show`.

If any of these conflict, the order of authority is: the owner's instructions, then MILESTONES.md, then the specification, then this runbook. Record any conflict in the run log.

## 1. Roles

| Role | Who | Does | Does not |
| --- | --- | --- | --- |
| **Owner** | Shane | Approves scope, publishing, gate overrides and any change to a decision in specification §6; reviews before a step is marked reviewed | — |
| **Orchestrator** (optional) | An agent or the owner | Opens the slice, assigns stages, launches reviewers, keeps the run log's status table current, folds lessons into this runbook | Do stage work it also reviews |
| **Stage agent** | One agent per stage | Carries out one stage (A, B, C or D) end to end and writes its handoff note | Start the next stage, mark anything reviewed, or push |
| **Gate reviewer** | A fresh agent that did not work on the stage | Checks the stage against §6 and records a verdict in the run log | Fix the work itself (it lists findings) |

One agent may hold several roles over time. It may never review its own stage.

## 2. Lifecycle of a slice

```
Open slice → A Reconstruct → Gate A → B Model ┐
                                    → C Evidence ┘→ Gates B, C → D Consolidate → Gate D
          → Owner review → Register and report → Retrospective → Runbook update
```

1. **Open the slice** (orchestrator or owner). Create the branch `m2-slice-NN-<slug>` from an up-to-date `m2` (§7.1). Copy `../validator-track-runs/m2/_TEMPLATE.md` to `../validator-track-runs/m2/slice-NN.md`, then fill in the header and the status table. Confirm that the owner has settled the decisions in specification §6. Commit the run log in the run-log repository: `M2 slice NN: open run log`.
2. **Stage A.** It must pass Gate A before B or C starts, because both depend on its register.
3. **Stages B and C** may run in parallel, by different agents, on the same branch in the same working tree. Each edits only its own experiment folder and its own records, takes IDs only from its reserved block (specification §5.7), stages only its own paths (`git add <paths>`, never `git add -A` or `git commit -a`), and leaves pages owned by other stages alone. Workbench writes are serialized (§4.1).
4. **Stage D** starts when both B and C have passed their gates, or when the slice omits one.
5. **Owner review.** The owner reviews the slice's changes to the step pages. Only then may a step's status become `reviewed` (§7.3), and only then is the slice branch merged into `m2` (§7.1).
6. **Retrospective and runbook update** (§9) happen before the next slice opens.

**The first slice is a pilot** (specification §5). Its purpose includes testing this runbook, so every stage's retrospective is mandatory and specific, and the runbook update after it is required before Slice 2 opens. Where possible, assign Stages B, C and D to different agents so that cold pickup is tested.

## 3. Standard stage procedure

Every stage agent follows these steps.

### 3.1 Pick up

- Read §0. In the run log's status table, set your stage to `in progress` and fill in the agent and date.
- Check out the slice branch. Run `git status`. Any uncommitted change must belong to a stage listed as `in progress` in the run log; anything else is a stop condition. While B and C run in parallel, expect the other stage's files.
- Record a baseline in the run log:

  ```bash
  sha256sum validator-track-workbench.html
  python3 validator-track-workbench-tools/vtw.py lint validator-track-workbench.html
  python3 validator-track-workbench-tools/vtw.py counts validator-track-workbench.html
  ```

  Lint must start at 0 errors and 0 warnings. If it does not, stop and record why.

### 3.2 Work

- Do only your stage's scope, as given in the specification. If the work reveals that the specification is wrong or insufficient, record it in the run log under *Issues*, take the most conservative reading, and continue. If the problem blocks the stage, stop (§8).
- Commit at meaningful checkpoints with messages of the form `M2 slice NN stage X: <what>`. Never force-push. Never commit the generated workbooks, backups or credentials.

### 3.3 Self-check before handing off

- Lint: 0 errors, 0 warnings. Workbench unit tests pass (`cd validator-track-workbench-tools && python3 -m unittest discover -s tests`, about a minute). If any page text changed, run the browser check and the word budget (§4.4).
- Experiments: rebuild and verify from a clean clone of the branch (`git clone --branch <branch> . /tmp/slice-check`, then the reproduce line).
- Go through the gate checklist for your stage (§6) and note any item you could not satisfy.
- Scope scan: no successor or rival-design framing, no adoption language, no first person in records. Lint checks reserved terms; fix every hit rather than rewording around it.

### 3.4 Hand off

Write the stage's **handoff note** in the run log (template in `../validator-track-runs/m2/_TEMPLATE.md`): what was produced (with record IDs, paths and commit), what was decided and why, the open issues, what the next stage must know, and the retrospective notes (§9). Set the stage's status to `ready for gate`. Commit your work on the slice branch, then commit the run log in the run-log repository.

## 4. Workbench procedure

### 4.1 One writer at a time

The workbench is a single file. Only one agent writes to it at a time. Before writing, claim it in the run log's *Workbench lock* line with your stage and time; release it after your import commit. While holding the lock, **re-export every existing tiddler you are about to change** and apply your edits to that fresh export, never to an export taken before the lock: `import` replaces whole tiddlers, so an old export would erase another stage's changes. Import, run lint, commit the workbench, then release the lock. Parallel stages prepare their records as JSON change sets and import them one after the other. Close any browser copy first.

### 4.2 Read, change, check

```bash
W=validator-track-workbench.html; T=validator-track-workbench-tools/vtw.py
python3 $T show $W GT-03 SC-07                     # read
python3 $T find $W "stake share" -i --type FR,CN   # search
python3 $T export $W --out /tmp/before.json        # snapshot
sha256sum $W                                       # note the SHA
python3 $T import $W /tmp/changes.json --expect-sha <SHA>
python3 $T diff /tmp/before.json $W                # review your own change
python3 $T lint $W
```

A change set is a JSON list of whole tiddlers in export format; to change a record, export it, edit it, then import it. Never search and replace over the HTML, and never page through the HTML directly.

### 4.3 Records

- **IDs:** use the stage's reserved block where the specification gives one; otherwise take the next free number for the type (`vtw.py counts`, then `find '^FR-' -l` or similar). Never reuse or rename an ID; retire a record with a status instead. Register rows use `I-NN`, numbered across all slices.
- **Required fields** come from `$:/vtw/schema/<TYPE>`; `vtw.py lint` enforces them. For M2 records: `stage: M2`, `introduced_by` set to the step that creates the record (M2.1, M2.2 or M2.3), and `last_changed_by` set to the step on substantive change.
- **Writing rules** (Conventions page): neutral, impersonal voice; one question per record; every number labelled paper-proposed, illustrative or measured; hedging goes in `status`, not in sentences; counterevidence goes in `would_change`; no QA narrative inside records.
- **Findings in M2** carry `resolved_by`, `spec_settles` and `still_to_test`. Leave `reviewed_by` blank. Only the owner or a human reviewer the owner names fills it; gate-reviewer agents never do.
- **Changing an M1 record:** keep `stage: M1` and `introduced_by`; set `last_changed_by` to the M2 step.
- **Conclusions** carry `basis`, `task` and `carried_to`. A conclusion states what the evidence supports, not what the agent expects.

### 4.4 Step pages

Each stage updates its step page's summary fields: `step_status`, `step_done`, `step_remaining` and `step_next`, and replaces "not run" text with results as they exist. Step pages accumulate across slices, so `step_status` stays `in progress` until the last slice's part of that step is complete; it becomes `drafted` only then. Record each slice's completion in `step_done`. Keep the page readable for people: prose first, with records as evidence. Put long tables (the register, control map and timeline) in collapsed `<details>` blocks so that the page stays within its word budget (800–1,500 visible words for a step page). An over-budget page is a gate finding, fixed by collapsing or moving detail, not a failure.

After page changes, run the browser check and the word budget, each on its own fresh copy, because the browser check saves into the copy it opens:

```bash
cp validator-track-workbench.html /tmp/workbench-browser.html
cp validator-track-workbench.html /tmp/workbench-words.html
cd validator-track-workbench-tools
uv run --no-project --with playwright python3 browser_check.py /tmp/workbench-browser.html
uv run --no-project --with playwright python3 word_budget.py /tmp/workbench-words.html
```

## 5. Experiment procedure

- **Folder:** `experiments/m2/<slug>/`, named in the specification. Add a line for it to `experiments/README.md`.
- **Economic examples** follow EX-01's fixture pattern: `build.py` writes its tables (CSV or Markdown; a workbook only where the specification asks for one) beside itself; `verify.py` imports the calculation function, checks hand-computed fixtures written as constants (never read back from the output), and, for a workbook, checks that the saved formulas have caches and no errors. Pin dependencies in the reproduce line (`uv run --no-project --with xlsxwriter==3.2.9 …`). Generated files are not committed; add them to `.gitignore` if needed.
- **Evidence tabletops:** packets in Markdown, the matrix and verdicts in CSV, and `verify.py` checking allowed values and source citations. The commit that adds `tolerances.md` precedes the commit that adds the matrix or verdicts.
- **Data notes:** the query script, a dated extract with its source and range, and a note that labels the result as today's system.
- **README sections** for every experiment: task and question; source versions (the litepaper SHA-256 from EX-01's README); inputs with their status; method; results; limits; reproduce. Separate simulations from measured observations.
- **The EX record** mirrors the README in its fields: `question`, `inputs`, `method`, `formula`, `results`, `limits`, `reproduce`, `repo_path`. Its status becomes `reproducible` only after a clean-clone verification.

## 6. Review gates

### 6.1 Procedure

1. The orchestrator, or the stage agent if there is none, launches a **fresh** reviewer with: this runbook, the specification section, the run log, and the stage's commit range.
2. The reviewer works through the common checklist and the stage checklist, then records in the run log: verdict (`pass`, `pass with fixes` or `block`), a numbered list of findings (each with file or record, the problem, and a proposed fix), and what it checked and how.
3. On `pass with fixes`, the stage agent (or a new one) fixes the findings, notes each fix by number, and the reviewer, or another fresh reviewer, confirms. On `block`, the finding goes to the owner.
4. A gate pass is not review in the deliverable sense. Never infer a review from silence.

### 6.2 Common checklist (every stage)

- [ ] Scope: litepaper only; no successor mechanism or comparison; no adoption language; public framing respected.
- [ ] Every open rule used is in the register, labelled, and not filled with the reading most adverse to the paper.
- [ ] Cooperative case first, then market pressure, then strategic; each case beside its legitimate lookalike.
- [ ] Claims kept distinct (payment, execution, correctness, availability, independent demand, economic value; the multiplier concerns dishonesty).
- [ ] No result presented as prevalence, equilibrium or forecast. Modelled and observed results are separated.
- [ ] Counterevidence and the paper's defenses that held are recorded.
- [ ] Records follow the schema and writing rules; lint 0/0; tests pass; IDs are new and unique.
- [ ] Every number is labelled; every paper citation points to the correct lines.
- [ ] The handoff note is complete and the next stage could start from it alone.

### 6.3 Stage checklists

**Gate A (reconstruct).** The register covers every rule Stage B and C need; each row names its design question, base reading and variants. The control map covers the three setups. The timeline matches L109 and L223–224 and does not merge the paper's differing delay phrases. The intended relationships each have a stated condition. Test amendments are justified.

**Gate B (model).** Rebuild and verify from a clean clone. Recompute at least two fixtures by hand. Check that internal transfers cancel, the network half is lost once, outside delegators' shares are excluded from the organization's take (in the code), LPT and USDC are separated until a stated price, and a zero median removes the whole round reward. Check that each sweep dimension other than the emissions concepts can change a sign; remove dimensions that cannot (all four concepts stay, as the specification requires). Where an input is fixed in the pilot (for example `ω = 1`), check its term in the code rather than in the results. Check that no positive return is described as misconduct or as showing what validators can detect.

**Gate C (evidence).** The commit order shows that error and cost tolerances were fixed before outcomes. The alleged violation is stated before evidence. Every record kind cites the paper, a current-system path, or "not specified by the paper". Each claim cell holds an allowed value. The limits state that synthetic packets do not measure accuracy or prevalence.

**Gate D (consolidate).** Every listed finding and design question has a checked classification. Plausible completions are options the paper states or plainly implies; none is a new mechanism. GT status changes follow from results. Each M3 handoff item is either an unresolved concern with evidence that plausible completions leave it open, or an area the paper leaves unaddressed; specification-only items stay on the build list. The paper's retained strengths are listed.

## 7. Git, GitHub and reporting

### 7.1 Branches and commits

M2 work happens outside `main`. The integration branch is `m2`; it holds the specification, this runbook and every merged slice. Each slice gets its own branch, `m2-slice-NN-<slug>`, created from `m2` (a hyphen, not a slash: Git cannot hold both `m2` and `m2/…`). After the owner has reviewed a slice, the slice branch is merged into `m2` with a merge commit; never rebase or squash it. When and how `m2` reaches `main` is the owner's decision. Make normal commits only: no force-push and no history rewriting. End commit messages with the attribution line the environment provides. Never stage local-only agent context files.

### 7.2 Publishing

The repository is public, and every pushed commit publishes the workbench. Agents do not push, open PRs, comment on issues or edit the Project board without the owner's approval for that action. When a slice passes Gate D, the orchestrator asks the owner to approve a push and a PR. The PR body summarizes the run, lists the records and experiments produced, and states the review status. It does not link or quote the local run log.

### 7.3 After owner review

Only after the owner has reviewed: set the step page's `step_status` to `reviewed` (if the step is complete; otherwise it stays `drafted`), add or update the row in the [deliverable register](../../deliverables/README.md) with the exact commit, update the task issue's Deliverables table and MILESTONES.md, and note the outcome in the monthly update. These edits also need approval to publish.

### 7.4 Run logs are local

Run logs, handoff notes and gate verdicts live in the **run-log repository**, a local Git repository with no remote that sits beside the main clone (`../validator-track-runs/m2/`). Its exact location is given in the local agent context file. Commit run-log changes there with the same message style. Do not copy run logs into the public repository, link them from public artifacts, or quote them in PRs or issues. Write them to the same scope and writing standards as public material all the same, because the owner may migrate them to the public repository once the process is settled; that migration is the owner's decision.

### 7.5 Work in the main clone

Run M2 stages in the main clone, not in separate Git worktrees. Local-only files that lint and scope checks rely on are untracked, so a worktree does not have them, and the relative run-log path assumes the main clone.

## 8. Stop and ask the owner when

- a result appears to need a mechanism outside the paper, or a large simulation;
- a rule must be filled in and no reading in the register is defensible;
- a data source requires credentials, payment or terms acceptance;
- a gate returns `block`;
- the specification and the evidence disagree in a way that would change the slice's question;
- evidence weakens part of the project's working hypotheses. Report it plainly; do not soften or reframe it.

Record the question in the run log under *Owner decisions needed*, with the options and a recommendation, and leave the stage `blocked`.

## 9. Improving this runbook

Each handoff note ends with retrospective answers:

1. What in the runbook or specification was missing, wrong or ambiguous?
2. What took longer than it should have, and why?
3. What did the gate reviewer catch that the self-check should have caught?
4. What would you change for the next slice?

After each slice (or sooner, if a problem blocks later stages), the orchestrator or owner:

- folds the accepted changes into this runbook and the specification, bumping the minor version;
- adds a change-log entry below, citing the run log that motivated it;
- adds reusable patterns to the slice catalogue or §5 (for example a packet format or a sweep layout that worked).

Agents propose runbook changes in the run log. They edit this file only when assigned to fold in lessons.

## 10. Change log

| Version | Date | Change | Motivated by |
| --- | --- | --- | --- |
| 0.1 | 2026-10-05 | First draft, written before Slice 1 | M2 planning discussion |
| 0.2 | 2026-10-05 | Run logs moved out of the public repository to a local run-log repository (§0, §2, §3.4, §7.2, §7.4) | Owner decision |
| 0.3 | 2026-10-05 | Slice 1 designated a pilot: mandatory retrospectives, required runbook update, different agents per stage where possible (§2) | Owner decision (specification 0.3) |
| 0.4 | 2026-10-05 | Fixes from an independent review: rules for parallel stages (shared tree, own paths, re-export under the lock, ID blocks); relative run-log path and main-clone rule (§7.4, §7.5); `step_status` stays in progress across slices; word budget and separate check copies; unit-test command; Gate B exemptions; `reviewed_by` only by the owner or a named human; scope-scan wording | Independent review of specification 0.3 and runbook 0.3 |
| 0.5 | 2026-10-05 | Branching: `m2` is the integration branch; slices use `m2-slice-NN-<slug>` from `m2` and merge back after owner review (§2, §7.1) | Owner decision |
