# Validator-track workbench tools

Helpers for `validator-track-workbench.html` at the repository root. They are not a build step: the workbench file is the only editable record set.

- `vtw.py` — `show` and `find` (read and search the workbench's own tiddlers), `export`, `import` (upsert, with a backup first; `--expect-sha` refuses to write if the file changed), `remove`, `lint` (ID patterns, required fields, vocabularies, reference targets and types, reciprocal pairs, source line ranges, litepaper hash, M1/M2 scope terms), `diff` (record-level, field-level), `counts`. The schema is read from the wiki's own `$:/vtw/schema/*`, `$:/vtw/relations` and `$:/vtw/participants` tiddlers.
- `browser_check.py` — Playwright check of reading structure, rendering, saving and reloading, run against a **copy** of the workbench.
- `word_budget.py` — visible words on Home, each step page and each mechanism page.
- `shots.py` — full-page screenshots of a copy, for reviewing layout.
- `twpage.py` — shared Playwright helpers for the three scripts above.
- `tests/` — unit tests for `vtw.py`.
- `backups/` — automatic copies that `vtw.py import` and `remove` write before changing the file. Not tracked by git.

## How to edit the workbench

1. Open `validator-track-workbench.html` in a web browser. Nothing needs to be installed. The workbench's Conventions page sets out the record types, fields, writing rules and editing protocol; read it before changing records.
2. Small edits can be made in the browser. Saving downloads a new HTML file: move it over `validator-track-workbench.html`, then reopen that file. A browser save is also the only thing that rewrites the HTML around the records: the page title and the note for agents at the top of the file (`$:/vtw/agent-note`). `vtw.py import` leaves that HTML untouched, and `lint` warns when it no longer matches the records.
3. To read or search from a terminal, use `vtw.py show` and `find`. They need only Python 3, with nothing to install, and read the workbench's own tiddlers, never the TiddlyWiki core. Don't grep or page through the HTML itself: the core sits on one line of about 2 MB that a text search can match.

   ```bash
   python3 validator-track-workbench-tools/vtw.py show validator-track-workbench.html GT-07 "View: Path history"
   python3 validator-track-workbench-tools/vtw.py show validator-track-workbench.html MX-06 --fields caption,hypothesis
   python3 validator-track-workbench-tools/vtw.py find validator-track-workbench.html "rewards delay" -i --type GT,CN
   python3 validator-track-workbench-tools/vtw.py find validator-track-workbench.html spike -l
   ```

   `find` takes a Python regular expression and prints one snippet per match as `TITLE.field[:line]`; for the embedded litepaper the line is the paper's own line number. `-l` lists matching tiddlers with their captions. Output stops at `--max` matches (default 100).

4. Scripted edits go through `vtw.py`, from the repository root. A change set is a JSON list of whole tiddlers in the export format. Never search and replace over the HTML.

   ```bash
   python3 validator-track-workbench-tools/vtw.py export validator-track-workbench.html --out records.json
   sha256sum validator-track-workbench.html
   python3 validator-track-workbench-tools/vtw.py import validator-track-workbench.html changes.json --expect-sha SHA256
   python3 validator-track-workbench-tools/vtw.py diff before.html validator-track-workbench.html
   ```

5. Run the checks before proposing a change. Lint should report 0 errors and 0 warnings. The browser check needs a copy, because it saves and edits the file it opens.

   ```bash
   python3 validator-track-workbench-tools/vtw.py lint validator-track-workbench.html
   cd validator-track-workbench-tools
   python3 -m unittest discover -s tests
   cp ../validator-track-workbench.html /tmp/workbench-copy.html
   uv run --no-project --with playwright python3 browser_check.py /tmp/workbench-copy.html
   ```

One writer at a time: save and close (or reload) the browser copy before a script writes the file, and reopen it afterwards.
