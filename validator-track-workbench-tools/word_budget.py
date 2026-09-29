#!/usr/bin/env python3
"""Visible words per page, with collapsed sections closed.

uv run --no-project --with playwright python3 word_budget.py COPY.html [BEFORE.html] [--json OUT]

Counts Home, each step on the research path and each mechanism. The count is
what a reader sees in the tiddler frame: the body and the view-template
segments beside it (step beats, record header, mechanism layout), with every
<details> closed. The title bar, the modifier line and the tag pills are not
counted. With a second file, prints before and after side by side. Never
writes the wiki.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from twpage import open_wiki, show, visible_words  # noqa: E402

BUDGETS = {"Home": (0, 540), "step": (800, 1500), "mechanism": (1000, 2000)}


def measure(path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 1000})
        open_wiki(page, path)
        titles = page.evaluate(
            "() => ['Home'].concat($tw.wiki.filterTiddlers('[enlist{$:/vtw/path!!list}]'), $tw.wiki.filterTiddlers('[tag[MX]sort[title]]'))"
        )
        for title in titles:
            show(page, title)
            out[title] = visible_words(page, title)
        browser.close()
    return out


def kind(title: str) -> str:
    return "Home" if title == "Home" else "mechanism" if title.startswith("MX-") else "step"


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    if json_out in args:
        args.remove(json_out)
    after = measure(Path(args[0]).resolve())
    before = measure(Path(args[1]).resolve()) if len(args) > 1 else None
    print(f"{'page':<12} {'before':>7} {'after':>7}  target" if before else f"{'page':<12} {'words':>7}  target")
    for title, n in after.items():
        lo, hi = BUDGETS[kind(title)]
        target = f"{lo}-{hi}" if lo else f"<= {hi}"
        if before:
            print(f"{title:<12} {before.get(title, '—'):>7} {n:7}  {target}")
        else:
            print(f"{title:<12} {n:7}  {target}")
    if json_out:
        Path(json_out).write_text(json.dumps({"after": after, "before": before}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
