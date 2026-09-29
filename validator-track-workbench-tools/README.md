# Validator-track workbench tools (local, private)

Helpers for `validator-track-workbench.html` at the repository root. Not a build step. The wiki is the only editable record set.

Read the [workbench agent runbook](../validator-track-workbench-agent-runbook.md) for the research approach, mechanism and critical-gate structure, system incentive reconstruction, milestone handoffs, and migration guidance. The runbook defines the target research organization; the historical migrations below describe earlier versions.

- `vtw.py` — `export`, `import` (upsert, with a backup first; `--expect-sha` refuses to write if the file changed), `remove`, `lint` (ID patterns, required fields, vocabularies, reference targets and types, reciprocal pairs, source line ranges, litepaper hash, M1/M2 scope terms), `diff` (record-level, field-level), `counts`. The schema is read from the wiki's own `$:/vtw/schema/*`, `$:/vtw/relations` and `$:/vtw/participants` tiddlers.
- `browser_check.py` — Playwright check against a **copy**: `uv run --no-project --with playwright python3 browser_check.py /tmp/copy.html`.
- `migrations/` — one-time 2026-09-28 scripts, kept for provenance; do not edit them to change records. Edit the wiki. The `m1_*` seed scripts produced the initial tiddlers from the litepaper and the M1.1 v0.3 drafts. `m1_restructure_2026_09_28.py` reorganized the path around five questions (Orientation, M1.1 compute, M1.2 data, M1.3 judges, M2.1 behaviour, M2.2 rule or not) and added mechanism stories, questions for humans and contributor notes. `m1_feedback_revision_2026_09_28.py` applied review feedback: `resolved_by` / `spec_settles` / `still_to_test` / `reviewed_by` replace `fix_by_rule`, each concept gains a `requires` chain, and all narrative uses a neutral, impersonal voice. `m1_mechanism_architecture_2026_09_28.py` made mechanisms (`MX`) and critical questions (`GT`) the organizing records and set the path to M1.1–M2.3. `m1_readiness_fixes_2026_09_28.py` and `m1_readiness_fixes2_2026_09_28.py` prepared the current-system map (M1.4). `m1_review_fixes_2026_09_28.py` made chain items carry a basis label instead of defaulting to required.
- Reference copy before the restructure: `../archive_work/validator-track-workbench-v1-2026-09-28.html` (local, git-ignored). Not edited.
- `backups/` — automatic pre-write copies.

One writer at a time: save and close or reload the browser before an agent writes, and reopen afterwards.
