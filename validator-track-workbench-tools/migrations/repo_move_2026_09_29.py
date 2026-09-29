"""Repository move (2026-09-29): the workbench, runbook and tools now live at the root of
the livepeer-validator-track repository; outdated M1 drafts and process logs moved to the
git-ignored archive_work/. Paths in reader and editor pages become repository-relative.

Usage: python3 repo_move_2026_09_29.py WIKI > repo_move.json
"""
import json, subprocess, sys
from pathlib import Path

VTW = Path(__file__).resolve().parents[1] / "vtw.py"
cur = {t["title"]: t for t in json.loads(subprocess.check_output([sys.executable, str(VTW), "export", sys.argv[1], "--all"]))}
out = {}

def edit(title, field, a, b):
    r = out.get(title) or {k: v for k, v in cur[title].items() if k not in ("created", "modified", "modifier")}
    if r.get(field, "").count(a) != 1:
        sys.exit(f"{title}.{field}: expected one match for {a[:70]!r}")
    r[field] = r[field].replace(a, b)
    out[title] = r

A = "About this wiki"
edit(A, "text", "* Working file: `/home/mav/repos/livepeer/validator-track-workbench.html` (private, outside the public repository).",
     "* Working file: `validator-track-workbench.html` at the root of the livepeer-validator-track repository.")
edit(A, "text", "`/home/mav/repos/livepeer/validator-track-workbench-tools/vtw.py`", "`validator-track-workbench-tools/vtw.py`")
edit(A, "text", "* Reference copy before the 2026-09-28 restructure: `/home/mav/repos/livepeer/validator-track-workbench-v1-2026-09-28.html`. It is kept for comparison and is not edited.",
     "* Reference copy before the 2026-09-28 restructure: `archive_work/validator-track-workbench-v1-2026-09-28.html` (local, not published). It is kept for comparison and is not edited.")
edit(A, "text", "`/home/mav/repos/livepeer/validator-track-workbench-agent-runbook.md`", "`validator-track-workbench-agent-runbook.md` (local agent context)")
edit(A, "text", "`/home/mav/repos/livepeer/validator-track-workbench-tools/backups/validator-track-workbench.20260928-before-mechanism-migration.html`",
     "`validator-track-workbench-tools/backups/validator-track-workbench.20260928-before-mechanism-migration.html` (local, not published)")
edit("Conventions", "text", "<code>/home/mav/repos/livepeer/validator-track-workbench-agent-runbook.md</code>", "<code>validator-track-workbench-agent-runbook.md</code>")
edit("Home", "text", "<code>/home/mav/repos/livepeer/validator-track-workbench-agent-runbook.md</code>", "<code>validator-track-workbench-agent-runbook.md</code>")
edit("EX-01", "repo_path", "deliverables/m1/litepaper-baseline-accounting.xlsx", "archive_work/deliverables-m1/litepaper-baseline-accounting.xlsx (local; rebuilt by build.py)")
S = "SRC-M1-DRAFTS"
edit(S, "text", "They remain in the repository working tree, untracked and unreviewed, until Shane approves their replacement.",
     "On 2026-09-29 the drafts moved to the local, git-ignored `archive_work/deliverables-m1/`; the workbench replaces them. The experiment code stays in `experiments/m1/`.")
edit(S, "text", "|!File (repository working tree)|!sha256|", "|!File (path at migration time; drafts now under archive_work/deliverables-m1/)|!sha256|")
json.dump(list(out.values()), sys.stdout, indent=1, ensure_ascii=False)
