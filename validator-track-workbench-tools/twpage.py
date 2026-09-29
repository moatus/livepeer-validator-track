"""Shared Playwright helpers for the workbench tools (never saves the wiki)."""
from __future__ import annotations

from pathlib import Path

# Page chrome that is not reading matter: title bar, modifier line, tag pills.
CHROME = ".tc-titlebar, .tc-subtitle, .tc-tags-wrapper, .tc-tiddler-controls"


def open_wiki(page, path: Path) -> None:
    page.goto(path.resolve().as_uri())
    page.wait_for_function("window.$tw && $tw.wiki && document.querySelector('.tc-story-river')")
    # No animation, so a navigation never overlaps the previous page.
    page.evaluate("$tw.wiki.addTiddler({title: '$:/config/AnimationDuration', text: '0'})")


def show(page, title: str, close_details: bool = True):
    """Make `title` the only open tiddler and wait for it to render."""
    page.evaluate("t => $tw.wiki.addTiddler({title: '$:/StoryList', list: [t]})", title)
    page.wait_for_function(
        "t => document.querySelectorAll('.tc-story-river > .tc-tiddler-frame').length === 1"
        " && document.querySelector('.tc-story-river > .tc-tiddler-frame').getAttribute('data-tiddler-title') === t",
        arg=title,
    )
    page.evaluate("window.scrollTo(0, 0)")
    if close_details:
        page.evaluate(
            "t => document.querySelector('[data-tiddler-title=\"' + t + '\"]').querySelectorAll('details').forEach(d => { d.open = false; })",
            title,
        )
    return page.locator(f'.tc-story-river > [data-tiddler-title="{title}"]')


def visible_words(page, title: str) -> int:
    """Words a reader sees on the page with collapsed sections closed.

    Counts every view-template segment of the tiddler (the step beats and the
    mechanism header sit outside the body), not the title bar or tags.
    """
    return page.evaluate(
        """([t, chrome]) => {
          const frame = document.querySelector('[data-tiddler-title="' + t + '"]');
          if (!frame) return -1;
          frame.querySelectorAll('details').forEach(d => { d.open = false; });
          const clone = frame.cloneNode(true);
          clone.querySelectorAll(chrome).forEach(n => n.remove());
          clone.querySelectorAll('details').forEach(d => {
            [...d.children].forEach(c => { if (c.tagName !== 'SUMMARY') c.remove(); });
          });
          clone.style.position = 'absolute'; clone.style.left = '-99999px';
          document.body.appendChild(clone);
          const n = clone.innerText.split(/\\s+/).filter(Boolean).length;
          clone.remove();
          return n;
        }""",
        [title, CHROME],
    )
