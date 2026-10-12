# M2 runbook

Version **0.9 · 2026-10-12**. Status: **drafted**. Owner: Shane (@moatus).

How M2 work is briefed, carried out, reviewed, integrated and improved. What M2 must produce is in the [specification](SPEC.md); [Slice 2](SLICE-02.md) is drafted and [Slice 2b](SLICE-02B.md) is defined for the next implementation. Different agents carry out different stages; this runbook is written so that each can start cold from its brief.

## 0. Read first, in this order

1. Any instructions specific to your working environment, and this repository's [README](../../README.md).
2. This runbook in full.
3. The [specification](SPEC.md): §1–4, then your slice's section.
4. Your **brief** and the slice's **run log**. Both are kept outside this repository; the integrator gives you their location. The run log holds the status table, earlier handoff notes and open review findings.
5. The workbench Conventions page: `python3 validator-track-workbench-tools/vtw.py show validator-track-workbench.html Conventions`.
6. The records and litepaper lines your brief lists, read with `vtw.py show` and its explicitly named source version: October is `docs/litepaper-2.0.md`; September is `docs/sources/litepaper-2026-09.md`. Old line numbers never silently migrate.

If these conflict, the order of authority is: the owner's instructions, then MILESTONES.md, then the specification, then this runbook, then the brief. Record any conflict in your handoff note.

## 1. Roles

| Role | Who | Does | Does not |
| --- | --- | --- | --- |
| **Owner** | Shane | Approves scope, publishing and any change to a decision in specification §6; reviews a slice before any step is marked reviewed | — |
| **Integrator** | One agent for the whole slice | Opens the slice; writes each stage's brief; launches writers and reviewers; keeps the run log current; decides on review findings; is the **only** agent that imports into the workbench and the only one that commits; folds lessons into this runbook | Write a stage's research or review its own decisions as if independent |
| **Writer** | One agent per stage | Carries out the stage's research; writes its experiment files; prepares its workbench changes as a change-set script and JSON; passes all checks on a scratch copy; writes the handoff note | Import into the main workbench, commit, push, start another stage or mark anything reviewed |
| **Reviewer** | A fresh agent, a different model from the writer | Checks the stage against §6 and records a verdict with exact findings | Edit the work |

One agent may hold different roles in different slices. Nobody reviews their own stage.

## 2. Lifecycle of a slice

```
Open slice → A Reconstruct → Gate A → B Model ┐
                                    → C Evidence ┘→ Gates B, C → D Consolidate → Gate D
          → Owner review → Merge into m2 → Register and report → Retrospective → Runbook update
```

1. **Open the slice** (integrator). Create the branch `m2-slice-NN-<slug>` from an up-to-date `m2` (§7.1). Create the slice folder in the run-log location from its template: the run log, then one folder per stage for briefs, change sets and reports. Confirm applicable decisions and the slice input manifest. October migration and Slice 2 preparation are already authorized; do not ask again. A local branch may be based on the prepared October branch while the pilot awaits human review; record that ancestry without claiming a merge or acceptance.
2. **For each stage:** the integrator writes the brief (§3.1) and launches the writer; the writer delivers (§3.2–3.4); the integrator launches a fresh reviewer (§6); the integrator decides on the findings, has them fixed, imports the change set, runs the checks and commits (§4).
3. **Stage A** must pass Gate A and be committed before B or C starts, because both depend on its register.
4. **Stages B and C** may run in parallel, with different writers in the same working tree. Each writer edits only its own experiment folder and prepares changes only to the records the brief assigns it, using IDs from its reserved block (the active slice brief; specification §5.7 is historical). The integrator imports their change sets one after the other (§4.1). Writers own their assigned progress-table rows; the integrator owns Home, shared summaries, indexes and stale adjacent-field cleanup. Regenerate the second change set against the latest import.
5. **Stage D** starts when B and C are committed, or when the slice omits one.
6. **Owner review.** The owner reviews the slice. Only then may a step's status become `reviewed` (§7.3), and only then is the slice branch merged into `m2` (§7.1).
7. **Retrospective and runbook update** (§9) happen before the next slice opens.

**The first slice is a pilot** (specification §5). Its purpose includes testing this runbook, so every retrospective is mandatory and specific, and the runbook update after it is required before Slice 2 opens. Use a different writer agent for each stage so that cold pickup is tested.

### Slice 2b: three sequential step workloads

Apply [SLICE-02B-IMPLEMENTATION.md](SLICE-02B-IMPLEMENTATION.md) for this owner-requested follow-up. Its design is already defined. Phase 1 implements Stage A/M2.1; Phase 2 implements Stage B/M2.2 and a bounded interpretation of existing EX-07 evidence; Phase 3 implements Stage D/M2.3. Each workload gets one fresh Codex `gpt-6.1-sol` writer and one fresh Claude `claude-opus-5-5` reviewer, replacing generic model choices for this slice only. No separate Stage C assignment is required because new evidence packets/sources are out of scope; existing evidence is not treated as newly established detection. Gates A, B and D and common checks still apply. If new evidence packets become necessary, amend scope explicitly and apply the tolerance-first Gate C; do not silently expand Phase 2.

The integrator freezes a locally committed candidate after writer self-checks for each Opus review. It contains only writer-owned tracked experiment/reader files; the workbench change set is reviewed on a scratch copy, then imported/committed only after the gate passes. A workbench-only candidate may be the unchanged current commit plus explicitly hashed external change set and scratch copy. Fixes are new commits or revised external change sets; never amend, reset or rewrite history. Blocked candidates remain local and unaccepted. This ordering replaces §4.5 for Slice 2b; its gate-close commit imports accepted workbench changes on top of accepted candidates/fixes. Only the integrator imports workbench changes and commits. Phase 2 starts after Phase 1 passes and is integrated; Phase 3 starts after Phase 2 passes and is integrated. Keep human research review, merge and publication boundaries unchanged. Register the six primary assignments and final technical handoff in the execution milestone record before execution; planning documents are not an execution record.

## 3. Stage procedure

### 3.1 The brief (integrator)

Each brief states:

1. the step, the mechanisms, the existing records and the exact litepaper lines, and what the preceding handoff establishes;
2. the research question, the contribution the reward is meant to encourage, the choices compared and the rule interpretations in force;
3. the smallest calculation or evidence inquiry, its inputs and assumptions, and its observation and time boundary;
4. the result that would strengthen, weaken or reject the concern, and the participant or relationship whose consequence must be examined; for judgment-related work, the social burdens to examine (who must make, answer or defend a judgment, and at what cost) and how, or a statement that they are outside the stage;
5. the stopping condition, the expected records and reproducible artifacts, the reserved ID block, the files and records the writer may change, and the deliverables;
6. a compact input manifest with source hashes, source version, observation window, fee denominator, units, costs, ownership, cuts, score and claim assumptions; distinguish permitted illustrative inputs from computed results;
7. adjacent-field ownership (Home, step state, `starting_point`, `would_change`, evidence and experiment back-links), finite sweep bounds and undefined-value display rules. The integrator owns run-log amendments.

### 3.2 Writer: pick up and work

- Read §0 and your brief. Run `git status` and record the workbench baseline in your report:

  ```bash
  sha256sum validator-track-workbench.html
  python3 validator-track-workbench-tools/vtw.py lint validator-track-workbench.html
  python3 validator-track-workbench-tools/vtw.py counts validator-track-workbench.html
  ```

  Lint must start at 0 errors and 0 warnings. Uncommitted files belonging to a parallel stage are expected; anything else unexplained is a stop condition (§8).
- Do only your brief's scope. If the specification or brief is wrong or insufficient, record it in your report, take the most conservative reading and continue; stop if it blocks the stage.
- Write experiment files in the working tree under your assigned folder. Do not commit.
- Prepare workbench changes as a **change-set script** (§4.2) saved with your stage's reports, never by editing the workbench directly.

### 3.3 Writer: self-check

- Apply your change set to a scratch copy and run lint (0/0), the unit tests (`cd validator-track-workbench-tools && python3 -m unittest discover -s tests`) and, if page text changed, the browser check and word budget on that copy (§4.4).
- Fresh-tree checks must include the named paper snapshots, workbench tools, patched workbench and local lint policy; local policy stays outside tracked files. Scratch workbench imports write ignored backups: inspect `vtw.py import --help` and use its temporary backup option if available; otherwise move only the scratch import backup into the external run folder and record that path. Do not assume a `--no-backup` option exists.
- Experiments: run the reproduce line in a fresh copy of the working tree without Git metadata (`rsync -a --exclude .git ./ /tmp/slice-check-X/`), so that nothing depends on untracked local state outside your folder.
- Go through the gate checklist for your stage (§6) and list any item you could not satisfy.
- Scope scan: no successor or rival-design framing, no adoption language, no first person in records. Lint checks reserved terms; fix every hit rather than rewording around it.

### 3.4 Writer: deliver

Save, with your stage's reports: the change-set script and its JSON; a short report with before and after excerpts of changed records and the checks you ran with their results; and the **handoff note** (template in the run log): what was produced (record IDs, paths), what was decided and why, the open issues, what the next stage must know, and the retrospective answers (§9). Tell the integrator you are done.

## 4. Workbench procedure (integrator)

### 4.1 One writer to the file

Only the integrator imports into the main workbench, one change set at a time. Close any browser copy first. Immediately before importing, check the file's hash; if it changed since the writer's script ran (for example because another stage was imported), rerun the script against the current file, review the new JSON, lint it on a scratch copy, then import with `--expect-sha`. If an import is rejected, rebuild; never force it.

### 4.2 Change-set scripts

A change-set script takes the workbench path, exports with `vtw.py export --all`, edits whole tiddlers, and prints the JSON change set. It fails loudly when text it replaces is missing or occurs more than once, reproduces the same JSON when rerun on the same source, and strips `created`, `modified` and `modifier`. Never search and replace over the HTML, and never page through the HTML directly.

```bash
W=validator-track-workbench.html; T=validator-track-workbench-tools/vtw.py
python3 $T show $W GT-03 SC-07                     # read
python3 $T find $W "stake share" -i --type FR,CN   # search
cp $W /tmp/scratch.html                            # scratch copy
python3 $T import /tmp/scratch.html changes.json   # trial
python3 $T diff $W /tmp/scratch.html               # review the change
python3 $T lint /tmp/scratch.html
sha256sum $W                                       # then, on the main file:
python3 $T import $W changes.json --expect-sha <SHA>
```

### 4.3 Records

- **IDs:** use the stage's reserved block where the specification gives one; otherwise the next free number (`vtw.py counts`, then `find '^FR-' -l`). Never reuse or rename an ID; retire a record with a status instead. Register rows use `I-NN`, numbered across all slices.
- **Required fields** come from `$:/vtw/schema/<TYPE>`; lint enforces them. New M2 records: `stage: M2`, `introduced_by` the step that creates them (M2.1, M2.2 or M2.3). Changing an M1 record: keep `stage: M1` and `introduced_by`; set `last_changed_by` to the M2 step.
- **Writing rules** (Conventions page): neutral, impersonal voice; one question per record; every number labelled paper-proposed, illustrative or measured; hedging goes in `status`; counterevidence in `would_change`; no QA narrative inside records. Use the paper's framing ("the contribution the reward is meant to encourage", "work of the kind the paper means to pay for"), and let numbers and the paper's own words carry weight rather than emphatic adjectives.
- **Findings in M2** carry `resolved_by`, `spec_settles` and `still_to_test`, and follow this order: what the test establishes, its conditions and boundary, the participant and relationship affected, what the tested defenses achieve, and what would resolve the rest. Reuse `FR-01` for the overarching hypothesis and add distinct conditional findings where assumptions differ. Leave `reviewed_by` blank; only the owner or a human reviewer the owner names fills it.
- **Conclusions** carry `basis`, `task` and `carried_to`.
- **Reader vocabulary:** workbench text uses mechanism, part, design question, critical question, case, finding and conclusion. Stage, undefined slice labels, pilot, gate and writer/reviewer roles are process vocabulary; keep them out of research prose. Human readers follow questions and results.

### 4.4 Step pages

The integrator updates each stage's step page's `step_status`, `step_done`, `step_remaining` and `step_next`, and replace "not run" text with results as they exist. Step pages accumulate across slices, so `step_status` stays `in progress` until the last slice's part of that step is complete; record each slice's completion in `step_done`. Keep pages readable for people: prose first, records as evidence. Put long tables (the register, control map and timeline) in collapsed `<details>` blocks so that a step page stays within 800–1,500 visible words. An over-budget page is a gate finding, not a failure. Accumulate per-study details in collapsed sections; reserve Home headroom because it renders step summaries. Review the complete rendered path, including cards and first-use symbol definitions.

Run the browser check and the word budget each on its own fresh copy, because the browser check saves into the copy it opens:

```bash
cp validator-track-workbench.html /tmp/workbench-browser.html
cp validator-track-workbench.html /tmp/workbench-words.html
cd validator-track-workbench-tools
timeout 900 uv run --no-project --with playwright python3 browser_check.py /tmp/workbench-browser.html
uv run --no-project --with playwright python3 word_budget.py /tmp/workbench-words.html
```

### 4.5 Commit

After a stage passes its gate and its change set is imported, the integrator runs lint, the unit tests and, for experiments, a clean-clone rebuild (`git clone --branch <branch> . /tmp/slice-clone && cd /tmp/slice-clone && <reproduce line>`) after committing, and records the commit in the run log. Commit messages: `M2 slice NN stage X: <what>`. Never commit generated outputs, backups or credentials.

## 5. Experiment procedure

- **Folder:** `experiments/m2/<slug>/`, named in the specification. Add a line for it to `experiments/README.md`.
- **Economic examples:** `build.py` writes its tables (CSV or Markdown; a workbook only where the specification asks for one) beside itself; `verify.py` imports the calculation function and checks hand-computed fixtures written as constants, never read back from the output. Pin dependencies in the reproduce line. Generated files are not committed; add them to `.gitignore` if needed.
- **Evidence tabletops:** packets in Markdown, the matrix and verdicts in CSV, and `verify.py` checking allowed values and source citations. `tolerances.md` is committed in its own commit, before the matrix or verdicts exist; the integrator commits it as soon as Gate C's first check (tolerances stated) passes, then the writer continues.
- **Data notes:** the query script, a dated extract with its source and range, and a note that labels the result as today's system.
- **README sections:** task and question; source versions (the litepaper SHA-256 in EX-01's README); inputs with their status; method; results; limits; reproduce. Separate simulations from measured observations.
- **The EX record** mirrors the README: `question`, `inputs`, `method`, `formula`, `results`, `limits`, `reproduce`, `repo_path`. Its status becomes `reproducible` only after the clean-clone rebuild.

## 6. Review gates

### 6.1 Procedure

1. The integrator launches a **fresh** reviewer, a different model from the writer, with this runbook, the specification section, the brief, the writer's report, handoff note and change set, and the paths of the files changed.
2. The reviewer uses `vtw.py diff` and a field-level comparison of exports to inspect exact scope, then checks the common and stage checklists and records: verdict (`pass`, `pass with fixes` or `block`); numbered findings, each with file or record, problem, evidence and exact replacement text or fix; and what it checked and how.
3. The integrator decides on each finding (accept, modify or reject, with a reason), has accepted findings fixed by the writer or fixes them itself, and records the decisions in the run log. A `block` goes to the owner.
4. A gate pass is not review in the deliverable sense. Never infer a review from silence.

### 6.2 Common checklist (every stage)

- [ ] Scope: litepaper only; no successor mechanism, comparison or framing; no adoption language.
- [ ] Every open rule used is in the register, labelled, and not filled with the reading most adverse to the paper.
- [ ] Cooperative case first, then market pressure, then strategic; each case beside its legitimate lookalike.
- [ ] Claims kept distinct (payment, execution, correctness, availability, independent demand, economic value); the multiplier concerns dishonesty; common ownership alone is not misconduct.
- [ ] No result presented as prevalence, equilibrium or forecast; modelled and observed results separated.
- [ ] Counterevidence and the paper's defenses that held are recorded with their actual reach.
- [ ] Records follow the schema and writing rules; lint 0/0 on the scratch copy; tests pass; IDs come from the reserved block.
- [ ] Every number labelled; every litepaper citation points to the correct lines.
- [ ] No stale “not run / untested” assertion survives on an affected reader path; historical exemptions name their source/version.
- [ ] Model premises are not described as findings, and follow-ups cite the formula/result that can change a sign; their direction is checked across boundaries.
- [ ] The handoff note is complete and the next stage could start from it alone.

### 6.3 Stage checklists

**Gate A (reconstruct).** Active slices use their own source-version timeline and control-map requirements (Slice 2: SLICE-02.md); the remaining details in this paragraph preserve the pilot checklist. The register covers every rule Stages B and C need, each row with its design question, base reading and variants. The control map covers the three setups. The timeline matches L109 and L223–224 without merging the paper's differing delay phrases. Each intended relationship has a stated condition. Test amendments are justified, and GT-03's and GT-01's `smallest_test` fields match them.

**Gate B (model).** Also apply the active slice’s accounting invariants and finite sweep, including zero-denominator cases; when a probability threshold has zero after-reward, report “undefined” or “no finite threshold” as the algebra requires, never infinity as a measured risk. Rebuild and verify in a fresh copy. Recompute at least two fixtures by hand. Check that internal transfers cancel, the network half is lost once, outside delegators' shares are excluded from the organization's take (in the code, since the pilot fixes `ω = 1`), LPT and USDC are separated until a stated price, and a zero median removes the whole round reward. Each sweep dimension other than the emissions concepts can change a sign. No positive return is described as misconduct or as showing what validators can detect.

**Gate C (evidence).** `tolerances.md` was committed before the matrix and verdicts existed. The alleged violation is stated before evidence. Every record kind cites the paper, a current-system path, or "not specified by the paper". Every matrix cell holds an allowed value. The limits state that synthetic packets do not measure accuracy, effort or prevalence. Verdicts assess separation by obtainable evidence. Procedural adverse consequences belong in a named judgment-reading column or note and burden, never as proof of a violation. Trace every cited source path and quote; report tolerances individually.

**Gate D (consolidate).** Every listed finding and design question has a checked classification. Each of the paper's defenses is assessed against its operating condition in the active source and slice brief (specification §5.6 preserves the September pilot). Plausible completions are options the paper states or plainly implies; none is a new mechanism. GT status changes follow from results. Each M3 handoff item is an unresolved concern with evidence that plausible completions leave it open, or an area the paper leaves unaddressed; specification-only items stay on the build list. The paper's retained strengths are listed.

## 7. Git, publishing and reporting

### 7.1 Branches and commits

M2 work happens outside `main`. The integration branch is `m2`; it holds the specification, this runbook and every merged slice. Each slice gets its own branch, `m2-slice-NN-<slug>`, from `m2` (a hyphen, not a slash: Git cannot hold both `m2` and `m2/…`). After the owner has reviewed a slice, the integrator merges the slice branch into `m2` with a merge commit; never rebase or squash it. When and how `m2` reaches `main` is the owner's decision. Normal commits only: no force-push and no history rewriting. **October preparation exception:** the owner authorized preparing the next slice from `m2-october-preparation`, based on pilot commit `31edc45`. Slice 2 may branch from that preparation commit without first claiming pilot acceptance or merging into `m2`. This is a local preparation/start-path exception, not publication or review approval. **Slice 2b continuation:** the owner requested defining the follow-up and its implementation plan from the existing Slice 2 foundation. Use local branch `m2-slice-02b-strategic-self-funding`, descended from Slice 2 commit `e0c66a69bfea64a5484ffa55bf96535874553bb6`; this does not assert review or merge of either earlier slice.

### 7.2 Publishing

The repository is public, and every pushed commit publishes the workbench. Nobody pushes, opens PRs, comments on issues or edits the Project board without the owner's approval for that action. A PR body summarizes the slice, lists the records and experiments produced and states the review status; it does not link or quote run logs, briefs or review reports.

### 7.3 After owner review

Only after the owner has reviewed: set a step's `step_status` to `reviewed` if the step is complete, add or update the row in the [deliverable register](../../deliverables/README.md) with the exact commit, update the task issue's Deliverables table and MILESTONES.md, and note the outcome in the monthly update. These edits also need approval to publish.

### 7.4 Run logs stay outside the repository

Run logs, briefs, change-set scripts, reports and review verdicts are kept outside this public repository, in a location the integrator provides. Do not copy them into the repository, link them from public artifacts, or quote them in PRs or issues. Write them to the same scope and writing standards as public material, because the owner may publish them once the process is settled.

### 7.5 Work in the main clone

Run M2 stages in the main clone, not in separate Git worktrees: local files that lint and the scope checks rely on are untracked, so a worktree does not have them.

## 8. Stop and tell the integrator (who tells the owner) when

- a result appears to need a mechanism outside the paper, or a large simulation;
- a rule must be filled in and no reading in the register is defensible;
- a data source requires credentials, payment or terms acceptance;
- a gate returns `block`, or a reserved ID block runs out;
- the specification and the evidence disagree in a way that would change the slice's question;

Evidence that weakens a working hypothesis is a required result: report it plainly and continue within the declared question. It is not itself a blocker.

For a blocking condition above, the integrator records the question in the run log under *Owner decisions needed*, with the options and a recommendation, and marks the affected stage `blocked`.

## 9. Improving this runbook

Each handoff note and review ends with retrospective answers:

1. What in the runbook, specification or brief was missing, wrong or ambiguous?
2. What took longer than it should have, and why?
3. What did the review catch that the self-check should have caught?
4. What would you change for the next slice?

After each slice, or sooner if a problem blocks later stages, the integrator proposes changes to this runbook and the specification; the owner accepts or rejects them; accepted changes bump the minor version and get a change-log entry. Reusable patterns (a packet format, a sweep layout, a brief that worked) go into §5 or the specification's slice catalogue.

## 10. Change log

| Version | Date | Change | Motivated by |
| --- | --- | --- | --- |
| 0.1 | 2026-10-05 | First draft, written before Slice 1 | M2 planning discussion |
| 0.2 | 2026-10-05 | Run logs moved out of the public repository | Owner decision |
| 0.3 | 2026-10-05 | Slice 1 designated a pilot: mandatory retrospectives, required runbook update | Owner decision |
| 0.4 | 2026-10-05 | Fixes from an independent review: parallel-stage rules, ID blocks, main-clone rule, step status across slices, word budget, `reviewed_by` | Independent review |
| 0.5 | 2026-10-05 | Branching: `m2` integration branch; slices on `m2-slice-NN-<slug>` | Owner decision |
| 0.6 | 2026-10-06 | Roles changed to integrator, writer and reviewer: only the integrator imports and commits; writers deliver change-set scripts; reviewers are a different model from writers. Brief requirements (§3.1). Finding order and paper framing (§4.3). No references to material outside the repository | Owner decision on roles; alignment with the workbench's existing agent workflow |
| 0.7 | 2026-10-09 | October source and next-slice handoff; applied pilot lessons on explicit inputs, finite scope, adjacent fields, parallel ownership, evidence verdicts, source checks, scratch backups and rendered review | Owner request to prepare Slice 2; Slice 1 recorded retrospectives |
| 0.8 | 2026-10-12 | Slice 2b's three sequential step workloads, GPT-6.1-Sol/Opus 5.5 pairs, frozen-candidate review and local branch continuation; existing evidence reused within its scope | Owner request to define Slice 2b and a phased implementation specification |
| 0.9 | 2026-10-12 | Clarified Slice 2b candidate versus workbench integration commits, append-only fixes and execution-record wording | Independent preparation review |
