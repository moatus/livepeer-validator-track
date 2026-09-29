#!/usr/bin/env python3
"""Full-page screenshots, one open tiddler each, collapsed sections closed.

uv run --no-project --with playwright python3 shots.py COPY.html OUTDIR [--narrow] [--extra] [--mx]

Default viewport 1400x1000. --narrow also writes OUTDIR/narrow/ at 800x1000;
--extra writes other touched pages to OUTDIR/extra/. --mx shoots every
mechanism page into OUTDIR, with MX-04 and MX-06 also at 800 wide in
OUTDIR/narrow/. Animation is switched off in the page so navigations never
overlap. The wiki is never saved.
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from twpage import open_wiki, show  # noqa: E402

PAGES = (
    ("Home", "home.png"),
    ("How to read this workbench", "how-to-read.png"),
    ("M1.1", "m1.1.png"),
    ("M1.2", "m1.2.png"),
    ("M1.4", "m1.4.png"),
    ("MX-01", "mx-01.png"),
    ("MX-06", "mx-06.png"),
)
# Other pages this phase touches (--extra).
EXTRA = (
    ("View: Mechanism stories", "view-mechanisms.png"),
    ("View: Milestone dashboard", "view-dashboard.png"),
    ("View: Open decisions", "view-design-questions.png"),
    ("M2.1", "m2.1.png"),
    ("VD-09", "vd-09.png"),
    ("CN-08", "cn-08.png"),
    ("LP-07", "lp-07.png"),
)


def run(copy: Path, out: Path, width: int, pages=PAGES) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": width, "height": 1000})
        open_wiki(page, copy)
        for title, name in pages:
            show(page, title)
            page.screenshot(path=str(out / name), full_page=True)
            print(out / name)
        browser.close()


if __name__ == "__main__":
    copy = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve()
    if "--mx" not in sys.argv[3:]:
        run(copy, out, 1400)
    if "--narrow" in sys.argv[3:]:
        run(copy, out / "narrow", 800)
    if "--mx" in sys.argv[3:]:
        # Every mechanism page, plus two at 800 wide.
        mx = tuple((f"MX-{i:02d}", f"mx-{i:02d}.png") for i in range(1, 13))
        run(copy, out, 1400, mx)
        run(copy, out / "narrow", 800, (("MX-04", "mx-04.png"), ("MX-06", "mx-06.png")))
    if "--extra" in sys.argv[3:]:
        run(copy, out / "extra", 1400, EXTRA)
