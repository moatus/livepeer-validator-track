"""Browser verification of a workbench copy (never the working file).

uv run --no-project --with playwright python3 browser_check.py COPY.html
Checks: opens from disk without script errors; reader structure (Home, the
glossary, the five beats on every step page, step status from the step's own
field, conclusion cards with the summary and the full statement collapsed,
the mechanism v2 layout, badges on one line, narrow layout); every view and
record renders without TiddlyWiki errors; concept rollups; sidebar search;
record finder filters; new-record button; browser edit -> save (download) ->
reopen; agent edit (vtw.py import) -> reload. Structure is checked through
ids, classes and headings rather than exact prose, so a later rewrite of step
or mechanism text does not break it.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from twpage import open_wiki, show, visible_words  # noqa: E402

VTW = [sys.executable, str(HERE / "vtw.py")]
copy = Path(sys.argv[1]).resolve()
work = copy.parent
results = []
HOME_BUDGET = 540
STEP_BUDGET = 1500
BEATS = ("question", "start", "worked", "found", "leads")
MX_SECTIONS = ["In plain words", "How it works", "Could it work?", "What exists today", "What is known and what comes next"]


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))


def tw_open(page, path, title=None):
    page.goto(path.as_uri() + (f"#{title}" if title else ""))
    page.wait_for_function("window.$tw && $tw.wiki && document.querySelector('.tc-story-river')")
    page.evaluate("$tw.wiki.addTiddler({title: '$:/config/AnimationDuration', text: '0'})")


def navigate(page, title):
    return show(page, title, close_details=False)


def errors_in(frame):
    txt = frame.inner_text()
    bad = [m for m in ("Filter error", "Undefined widget", "Recursive transclusion", "Missing tiddler", "Unexpected token") if m in txt]
    bad += ["tc-error"] if frame.locator(".tc-error").count() else []
    return bad


BADGES = ".vtw-badge, .vtw-status, .vtw-prov, .vtw-rb, .vtw-sctype, .vtw-chg"


def wrapped_badges(page, title):
    """Badges whose text runs over more than one line (they must never wrap).

    An inline-block badge has one element box however many lines its text
    takes, so this counts the text's own line boxes with a DOM Range.
    """
    return page.evaluate(
        """([t, sel]) => [...document.querySelector('[data-tiddler-title="' + t + '"]').querySelectorAll(sel)]
              .filter(b => b.offsetParent)
              .filter(b => { const r = document.createRange(); r.selectNodeContents(b);
                             const tops = new Set([...r.getClientRects()].filter(x => x.width > 0).map(x => Math.round(x.top)));
                             return tops.size > 1; })
              .map(b => b.textContent.trim())""",
        [title, BADGES],
    )


def in_view(page, selector):
    return page.evaluate(
        """s => { const e = document.querySelector(s); if (!e) return false;
                 const r = e.getBoundingClientRect(); return r.top >= -2 && r.top < window.innerHeight * 0.6; }""",
        selector,
    )


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(accept_downloads=True, viewport={"width": 1400, "height": 1000})
    page = ctx.new_page()
    page_errors = []
    page.on("pageerror", lambda e: page_errors.append(str(e)))
    page.on("console", lambda m: page_errors.append(m.text) if m.type == "error" and "ERR_FILE_NOT_FOUND" not in m.text else None)
    failed = []
    page.on("requestfailed", lambda r: failed.append(r.url))

    tw_open(page, copy)
    path = page.evaluate("$tw.wiki.filterTiddlers('[enlist{$:/vtw/path!!list}]')")

    # ---- reader experience (default mode) ----
    check("reader mode is the default", page.evaluate("$tw.wiki.getTiddlerText('$:/config/vtw/mode')") == "reader")
    check("the sidebar opens on the workbench menu with the glossary and the path",
          page.locator(".tc-sidebar-scrollable .vtw-side").count() == 1
          and page.locator(".tc-sidebar-scrollable .vtw-side a", has_text="How to read this workbench").count() == 1
          and page.locator(".tc-sidebar-scrollable .vtw-side .vtw-dot").count() == len(path))

    h = navigate(page, "Home")
    home = h.inner_text()
    check("Home: concerns, start links, the path, where things stand, how to take part",
          all(h.locator("h2", has_text=x).count() == 1 for x in ("Two concerns under test", "The research path", "Where things stand", "How to take part"))
          and h.locator(".vtw-concerns .vtw-card").count() == 2
          and h.locator("a.vtw-startcard").count() == 3
          and h.locator("a.vtw-startcard", has_text="How to read this workbench").count() == 1
          and not any(w in home.split() for w in ("I", "we", "We", "our", "my")))
    words = visible_words(page, "Home")
    check(f"Home visible words stay within {HOME_BUDGET}", 0 < words <= HOME_BUDGET, str(words))
    status = {s: page.evaluate("s => $tw.wiki.getTiddler(s).fields.step_status || ''", s) for s in path}
    check("every step has a step_status from the vocabulary",
          all(v in ("not started", "handoff received", "in progress", "drafted", "reviewed") for v in status.values()), json.dumps(status))
    cards = {c.locator(".vtw-idsmall").inner_text(): c.locator(".vtw-stepbadge").inner_text() for c in h.locator("a.vtw-pathcard").all()}
    rows = [r.locator("td").nth(1).inner_text().strip() for r in h.locator("table.vtw-stand tr").all()[1:]]
    check("path cards and the status table show each step's own status",
          cards == status and rows == [status[s] for s in path], f"{cards} / {rows}")
    nxt = [r.locator("td").nth(3).inner_text().strip() for r in h.locator("table.vtw-stand tr").all()[1:]]
    caps = [page.evaluate("s => $tw.wiki.getTiddler(s).fields.caption", s) for s in path]
    check("the Next column reads each step's own next line, not the following step's title",
          nxt == [page.evaluate("s => $tw.wiki.getTiddler(s).fields.step_next || '—'", s) for s in path]
          and not any(n == c for n, c in zip(nxt, caps[1:])), str(nxt))
    check("Produced counts link somewhere and zero reads None recorded yet",
          h.locator("table.vtw-stand .vtw-produced a, table.vtw-stand .vtw-produced button").count() >= 3
          and "None recorded yet" in h.locator("table.vtw-stand").inner_text())
    check("at most five headline conclusions, caption links only",
          1 <= h.locator("ul.vtw-headlines li").count() <= 5 and h.locator("ul.vtw-headlines .vtw-status").count() == 0)
    check("a legend sits where step badges first appear on Home",
          h.locator(".vtw-legend .vtw-stepbadge").count() == 5)
    check("no badge wraps on Home", not wrapped_badges(page, "Home"), str(wrapped_badges(page, "Home")))
    probe = page.evaluate("""() => { const b = document.querySelector('[data-tiddler-title="Home"] table.vtw-stand .vtw-stepbadge');
        const was = [b.style.whiteSpace, b.style.width, b.textContent]; b.style.whiteSpace = 'normal'; b.style.width = '25px';
        b.textContent = 'A very long status'; return was; }""")
    detected = wrapped_badges(page, "Home")
    page.evaluate("""w => { const b = document.querySelector('[data-tiddler-title="Home"] table.vtw-stand .vtw-stepbadge');
        b.style.whiteSpace = w[0]; b.style.width = w[1]; b.textContent = w[2]; }""", probe)
    check("the wrap check catches a deliberately wrapped badge, then passes again",
          detected == ["A very long status"] and not wrapped_badges(page, "Home"), str(detected))
    check("For editors and agents stays collapsed", h.locator("details:not([open]) > summary", has_text="For editors and agents").count() == 1)

    g = navigate(page, "How to read this workbench")
    gloss = g.text_content()
    check("glossary: the six terms, both flows, the worked example and every legend",
          g.locator(".vtw-term").count() == 6 and g.locator(".vtw-flow").count() == 2
          and g.locator("ol.vtw-example li").count() >= 5
          and all(page.evaluate("t => $tw.wiki.getTiddler(t).fields.caption", t) in gloss for t in ("MX-06", "GT-01", "SC-07", "CN-08"))
          and g.locator(".vtw-legend").count() == 4
          and all(x in gloss for x in ("possible design option", "handoff received", "supported by text", "a policy choice")))
    check("glossary keeps the six terms and the worked example open and collapses the badges and other words",
          page.evaluate("""() => { const f = document.querySelector('[data-tiddler-title="How to read this workbench"]');
              const inClosed = s => [...f.querySelectorAll(s)].every(e => { const d = e.closest('details'); return d && !d.open; });
              const open = s => [...f.querySelectorAll(s)].every(e => !e.closest('details'));
              return open('.vtw-term') && open('ol.vtw-example') && inClosed('.vtw-legend') && inClosed('dl.vtw-dl-wide'); }"""))
    shown, ids = {}, {}
    for t in ("View: Open decisions", "View: Scenario pairs", "VD", "SC", "View: Mechanism stories", "MX-06", "CN-05", "EX-01", "SRC-LP20", "Home", "M1.2"):
        navigate(page, t)
        shown[t], ids[t] = page.evaluate("""t => { const h = document.querySelector('.tc-story-river > [data-tiddler-title="' + t + '"] .tc-titlebar h2.tc-title');
            const id = h.querySelector('.vtw-titleid'); return [h.childNodes[0].textContent.trim(), id ? id.textContent.trim() : null]; }""", t)
    cap = lambda t: page.evaluate("t => $tw.wiki.getTiddler(t).fields.caption", t)
    check("page headings show the reader caption, with the record ID small beside it; steps and Home keep their title",
          shown == {"View: Open decisions": "Design questions", "View: Scenario pairs": "Case pairs", "VD": "Design questions",
                    "SC": "Cases", "View: Mechanism stories": "Mechanisms", "MX-06": cap("MX-06"), "CN-05": cap("CN-05"),
                    "EX-01": cap("EX-01"), "SRC-LP20": cap("SRC-LP20"), "Home": "Home", "M1.2": "M1.2"}
          and ids["MX-06"] == "MX-06" and ids["CN-05"] == "CN-05" and ids["EX-01"] == "EX-01" and ids["Home"] is None, json.dumps(shown))
    glued = {}
    for t in ("View: Open decisions", "View: Scenario pairs", "View: Claims matrix", "View: Cooperative flow", "View: Parameter sheet", "VD", "SC"):
        body = navigate(page, t).locator(".tc-tiddler-body").inner_text()
        hits = re.findall(r"[A-Z]{2}-\d\d[A-Z]{2}-\d\d|\b\d+[a-z]{3,}\b|''|[a-z]{3}[.;:][A-Za-z]{3}", body)
        if hits:
            glued[t] = hits[:3]
    check("touched views keep their spaces next to links and counts", not glued, json.dumps(glued))
    ot = navigate(page, "Orientation").inner_text()
    check("Orientation is a context page with live fixture data", "context for all four M1 steps" in ot and "752 LPT of the 940" in ot)
    n_mx = page.evaluate("$tw.wiki.filterTiddlers('[tag[MX]]').length")
    check("at least twelve mechanisms", n_mx >= 12, str(n_mx))

    # ---- step pages: five beats, status, no copies ----
    missing = []
    for step in path:
        s = navigate(page, step)
        ids = page.evaluate(
            """t => [...document.querySelector('[data-tiddler-title="' + t + '"]').querySelectorAll('h2.vtw-jh')].map(h => h.id)""", step)
        want = [f"{step}-{b}" for b in BEATS]
        badge = s.locator(".vtw-stepmeta .vtw-stepbadge").inner_text() if s.locator(".vtw-stepmeta .vtw-stepbadge").count() else ""
        if ids != want or s.locator(".vtw-contribute").count() != 1 or badge != status[step] or wrapped_badges(page, step):
            missing.append(f"{step}: {ids} badge={badge!r}")
    check("every step page has the five beats in order, its status and a contribution block", not missing, "; ".join(missing))
    scoped = []
    for step in path:
        navigate(page, step)
        for t in page.evaluate("s => ($tw.wiki.getTiddler(s).fields.step_outputs || '').split(' ').filter(Boolean)", step):
            if t == "CN":
                continue
            want = page.evaluate("""([s, t]) => $tw.wiki.filterTiddlers('[tag[' + t + ']field:introduced_by[' + s + ']] -[field:status[split]] -[field:status[superseded]] +[sort[title]]')""", [step, t])
            sec = page.locator(f"[id='{step}-made-{t}']")
            got = page.evaluate("id => [...(document.getElementById(id) || document.createElement('i')).querySelectorAll('li .vtw-idsmall')].map(e => e.textContent.trim())", f"{step}-made-{t}")
            if want and (got != want or sec.locator("a", has_text="the full catalog").count() != 1):
                scoped.append(f"{step}/{t}: {len(got)} vs {len(want)}")
            if not want and sec.count():
                scoped.append(f"{step}/{t}: empty list shown")
    h = navigate(page, "Home")
    h.locator("table.vtw-stand tr", has=page.locator("td", has_text="M1.4")).locator("button.vtw-linkbtn", has_text="design questions").click()
    page.wait_for_timeout(500)
    check("each produced count lists exactly the records it counts on the step page, with a catalog link",
          not scoped and page.locator(".tc-story-river > [data-tiddler-title='M1.4']").count() == 1 and in_view(page, "[id='M1.4-made-VD']")
          and page.locator("[id='M1.4-made-VD'] li").count() == 2, "; ".join(scoped))
    j = navigate(page, "M1.1")
    jt = j.inner_text()
    check("M1.1: mechanism map with linked counts, no per-mechanism copies, conclusions as cards",
          j.locator("table.vtw-mxmap").count() == 1
          and j.locator("table.vtw-mxmap button.vtw-linkbtn").count() >= n_mx
          and j.locator("details.vtw-mech").count() == 0 and j.locator("table.vtw-chain").count() == 0
          and j.locator(".vtw-found").count() >= 9 and j.locator(".vtw-legend .vtw-status").count() >= 3
          and "Score aggregation is specified; score production is not" in jt)
    glue = re.findall(r"[a-z]{3}[.;:][A-Za-z]{3}|\b\d+[a-z]{3,}\b|[a-z]{3}\((?=[A-Z])", jt)
    check("M1.1 prose keeps spaces around markup", "pressAnswer" not in jt and not glue, str(glue[:3]))

    # "What it found": a conclusion with a summary shows it, with the full statement
    # collapsed in the card; one without shows the full statement. Test both paths
    # in memory (one summary injected, one removed), whatever the file holds.
    cns = page.evaluate("$tw.wiki.filterTiddlers('[tag[CN]field:task[M1.1]!field:status[superseded]contains:carried_to[M1.2]sort[title]]')")
    a, b = cns[0], cns[1]
    kept = page.evaluate("ts => ts.map(t => $tw.wiki.getTiddler(t).fields.summary || null)", [a, b])
    injected = "Injected summary for the browser check."
    page.evaluate("""([a, b, s]) => { $tw.wiki.addTiddler(new $tw.Tiddler($tw.wiki.getTiddler(a), {summary: s}));
                                      $tw.wiki.addTiddler(new $tw.Tiddler($tw.wiki.getTiddler(b), {summary: undefined})); }""", [a, b, injected])
    navigate(page, "M1.1")
    cards = page.evaluate("""() => [...document.querySelectorAll('[data-tiddler-title="M1.1"] .vtw-found')].map(c => {
        const d = c.querySelector('details.vtw-fullstmt');
        return {cap: c.querySelector('.vtw-card-h a').textContent.trim(),
                sum: (c.querySelector('.vtw-found-sum') || {}).textContent || null,
                details: !!d, open: d ? d.open : null, label: d ? d.querySelector('summary').textContent.trim() : null,
                full: d ? d.querySelector('.vtw-card-s').textContent.trim() : (c.querySelector('.vtw-card-s') || {}).textContent.trim(),
                badge: !!c.querySelector('.vtw-card-h .vtw-status')}; })""")
    want = page.evaluate("""() => $tw.wiki.filterTiddlers('[tag[CN]field:task[M1.1]!field:status[superseded]sort[title]]')
        .map(t => ({cap: $tw.wiki.getTiddler(t).fields.caption, sum: $tw.wiki.getTiddler(t).fields.summary || null}))""")
    cap = {t: page.evaluate("t => $tw.wiki.getTiddler(t).fields.caption", t) for t in (a, b)}  # noqa: F811
    by_cap = {c["cap"]: c for c in cards}
    shape_ok = len(cards) == len(want) and all(
        (by_cap[w["cap"]]["details"] and by_cap[w["cap"]]["open"] is False and by_cap[w["cap"]]["label"] == "Full statement"
         and (by_cap[w["cap"]]["sum"] or "").strip() == w["sum"].strip() and len(by_cap[w["cap"]]["full"]) > len(w["sum"]))
        if w["sum"] else (not by_cap[w["cap"]]["details"] and by_cap[w["cap"]]["sum"] is None and by_cap[w["cap"]]["full"])
        for w in want) and all(c["badge"] for c in cards)
    check("What it found: summary with its badge and the full statement collapsed; no summary shows the full statement",
          shape_ok and (by_cap[cap[a]]["sum"] or "").strip() == injected and not by_cap[cap[b]]["details"],
          f"{len(cards)} cards, {sum(1 for w in want if w['sum'])} with summary")
    card_a = page.locator("[data-tiddler-title='M1.1'] .vtw-found", has_text=cap[a])
    card_a.locator("details.vtw-fullstmt > summary").click()
    check("the full statement opens in place", card_a.locator("details.vtw-fullstmt[open] .vtw-card-s").is_visible())
    m12 = navigate(page, "M1.2")
    ca = m12.locator(".vtw-card-compact", has_text=cap[a]).locator(".vtw-clamp").text_content().strip()
    cb = m12.locator(".vtw-card-compact", has_text=cap[b]).locator(".vtw-clamp").text_content().strip()
    check("carried-in cards are unchanged: the summary, else the first sentence, and no collapsed statement",
          ca == injected and cb and m12.locator(".vtw-card-compact details").count() == 0, f"{ca!r} / {cb[:60]!r}")
    page.evaluate("""([a, b, k]) => { $tw.wiki.addTiddler(new $tw.Tiddler($tw.wiki.getTiddler(a), {summary: k[0] || undefined}));
                                      $tw.wiki.addTiddler(new $tw.Tiddler($tw.wiki.getTiddler(b), {summary: k[1] || undefined})); }""", [a, b, kept])
    j2 = navigate(page, "M1.2")
    jt2 = j2.text_content()
    check("M1.2 starts from carried-in conclusion cards and leaves superseded ones out",
          j2.locator(".vtw-cardgrid .vtw-card-compact").count() >= 5
          and page.evaluate("$tw.wiki.getTiddler('CN-14').fields.caption") in jt2
          and page.evaluate("$tw.wiki.getTiddler('CN-04').fields.caption") not in jt2
          and "Does the evidence warrant an adverse finding?" in jt2)
    check("M1.2 contribution block lists its open practitioner questions",
          j2.locator(".vtw-contribute li").count() == page.evaluate("$tw.wiki.filterTiddlers('[tag[HQ]field:step[M1.2]field:status[open]]').length"))
    check("M1.4 is restored as a task", "What exists today, and what would need to be built" in navigate(page, "M1.4").inner_text())
    m22 = navigate(page, "M2.2").inner_text()
    check("M2.2 tests critical questions and points to the moved register", "Testing the critical questions" in m22 and "What would resolve each concern?" in m22)
    r = navigate(page, "M2.3")
    rtxt = r.inner_text()
    kinds = {"specification": "[tag[VD]field:resolved_by[specification]]", "evidence": "[tag[VD]contains:resolved_by[evidence]]",
             "incentive": "[tag[VD]contains:resolved_by[incentives]]", "policy": "[tag[VD]contains:resolved_by[policy]]"}
    rows = {tr.locator("td").first.inner_text().lower(): tr.locator("td").last.inner_text().strip()
            for tr in r.locator(".tc-tiddler-body table tr").all() if tr.locator("td").count() >= 2}
    got = {k: next((v for label, v in rows.items() if k in label), None) for k in kinds}
    want = {k: str(page.evaluate("f => $tw.wiki.filterTiddlers(f).length", f)) for k, f in kinds.items()}
    check("M2.3 shows what would resolve the design questions, by kind, with live counts",
          got == want and "agent proposal, not reviewed" not in rtxt, f"{got} vs {want}")
    ph = navigate(page, "View: Path history")
    check("Path history documents identifier meanings", ph.locator("table.vtw-history tr").count() == 8)
    q = navigate(page, "View: Questions for humans")
    qt = q.inner_text()
    check("Questions for humans shows open questions, policy choices and review status",
          q.locator(".vtw-hq").count() >= 9 and "Policy choices" in qt and "Reviewing classifications" in qt and "press Answer this" in qt)
    md = navigate(page, "View: Milestone dashboard")
    check("Milestone dashboard shows each step's status", md.locator(".vtw-stepbadge").count() == len(path))

    # ---- mechanisms: every mechanism uses layout v2; the earlier layout is kept as a fallback ----
    not_v2 = page.evaluate("$tw.wiki.filterTiddlers('[tag[MX]!layout[v2]]')")
    check("every mechanism uses layout v2", not_v2 == [], str(not_v2))
    for mx in ("MX-01", "MX-12"):
        m = navigate(page, mx)
        check(f"{mx} renders the v2 layout", m.locator(".vtw-mx").count() == 1 and m.locator("table.vtw-chain").count() == 0)
    page.evaluate("$tw.wiki.addTiddler(new $tw.Tiddler($tw.wiki.getTiddler('MX-01'), {layout: undefined}))")
    m = navigate(page, "MX-01")
    check("a mechanism without layout v2 falls back to the earlier layout",
          m.locator(".vtw-header").count() == 1 and m.locator(".vtw-mx").count() == 0)
    page.evaluate("$tw.wiki.addTiddler(new $tw.Tiddler($tw.wiki.getTiddler('MX-01'), {layout: 'v2'}))")
    page.evaluate("$tw.wiki.addTiddler(new $tw.Tiddler($tw.wiki.getTiddler('LP-04'), {layout: 'v2'}))")
    lp4 = navigate(page, "LP-04")
    check("a non-mechanism record with layout v2 keeps its header and rollups",
          lp4.locator(".vtw-header").count() == 1 and lp4.locator(".vtw-rsec").count() >= 3 and lp4.locator(".vtw-mx").count() == 0)
    page.evaluate("$tw.wiki.addTiddler(new $tw.Tiddler($tw.wiki.getTiddler('LP-04'), {layout: undefined}))")
    s7 = navigate(page, "LP-07").inner_text()
    check("LP-07 concept links to the mechanisms that serve it", "Mechanisms that serve this concept" in s7 and page.evaluate("$tw.wiki.getTiddler('MX-06').fields.caption") in s7
          and "Questions for people who run this" in s7)
    mm = navigate(page, "View: Mechanism stories")
    check("Mechanism map lists all mechanisms", mm.locator("table.vtw-mxmap tr").count() == n_mx + 1)
    navigate(page, "View: Contributor notes").locator("button", has_text="Write a note").click()
    page.wait_for_function("$tw.wiki.filterTiddlers('[is[draft]tag[Note]]').length === 1")
    check("Write a note opens a Note draft", True)
    page.evaluate("$tw.wiki.filterTiddlers('[is[draft]tag[Note]]').forEach(t => $tw.wiki.deleteTiddler(t))")
    lp = navigate(page, "LP-04")
    check("LP-04 reader layout: overview first, details collapsed, grouped by question",
          "answer to \"rewards should follow real work\"" in lp.inner_text() and lp.locator("details.vtw-details").count() == 1
          and "Conclusions" in lp.inner_text() and "Design questions" in lp.inner_text())

    # ---- mechanisms: layout v2 (stored in the file) ----
    v2 = navigate(page, "MX-06")
    page.evaluate("document.querySelectorAll('[data-tiddler-title=\"MX-06\"] details').forEach(d => d.open = false)")
    v2t = v2.inner_text()
    heads = page.evaluate("""() => [...document.querySelectorAll('[data-tiddler-title="MX-06"] h2.vtw-mxh')].map(h => h.textContent.trim())""")
    check("MX-06 (layout v2) renders the mechanism sections in order", heads == MX_SECTIONS, str(heads))
    check("v2 page: no earlier header or rollup, one review note, parts table with coloured basis labels",
          v2.locator(".vtw-header").count() == 0
          and page.evaluate("() => [...document.querySelectorAll('[data-tiddler-title=\"MX-06\"] .vtw-rsec')].filter(e => !e.closest('details')).length") == 0
          and v2.locator(".vtw-mx > .vtw-note", has_text="not yet reviewed").count() == 1
          and v2.locator(".vtw-parts-wrap table").count() == 1
          and v2.locator(".vtw-parts-wrap .vtw-basis-required").count() >= 1
          and v2.locator(".vtw-parts-wrap .vtw-prov:not([class*='vtw-basis-'])").count() == 0)
    also = v2.locator(".vtw-also li").all_inner_texts()
    check("Also linked lists design questions not placed in a row", any("VD-19" in a for a in also), str(also))
    n_gt = page.evaluate("$tw.wiki.filterTiddlers('[tag[GT]contains:mechanisms[MX-06]]').length")
    check("critical question cards show the question and cases, with the long fields collapsed",
          v2.locator(".vtw-gt").count() == n_gt and v2.locator(".vtw-gt .vtw-gt-q").count() == n_gt
          and v2.locator(".vtw-caselist li").count() >= 5 and v2.locator(".vtw-look").count() >= 1
          and v2.locator(".vtw-gt details.vtw-gtd:not([open]) > summary", has_text="What would change the assessment").count() == n_gt
          and v2.locator(".vtw-gt details.vtw-gtd:not([open]) > summary", has_text="If it resolves badly").count() == n_gt)
    chips = v2.locator("button.vtw-chip").all_inner_texts()
    check("four chips: design questions, critical questions, cases, today",
          len(chips) == 4 and chips[3].strip() == "Today: none found", str(chips))
    check("Details is collapsed and holds the design-question table",
          v2.locator("details.vtw-mxdetails:not([open])").count() == 1 and v2.locator("details.vtw-mxdetails table.vtw-build").count() == 1)
    check("no badge wraps on the v2 page", not wrapped_badges(page, "MX-06"), str(wrapped_badges(page, "MX-06")))
    jumps = []
    for i, target in enumerate(("MX-06-parts", "MX-06-critical", "MX-06-cases", "MX-06-today")):
        page.evaluate("window.scrollTo(0, 0)")
        v2.locator("button.vtw-chip").nth(i).click()
        page.wait_for_timeout(350)
        jumps.append(in_view(page, f"#{target}"))
    check("each chip jumps to its section", all(jumps), str(jumps))
    j = navigate(page, "M1.1")
    j.locator("table.vtw-mxmap tr", has_text=page.evaluate("$tw.wiki.getTiddler('MX-06').fields.caption")).locator("button.vtw-linkbtn").first.click()
    page.wait_for_timeout(600)
    check("a count in the mechanism map opens that section of the mechanism page",
          page.locator(".tc-story-river > [data-tiddler-title='MX-06']").count() == 1 and in_view(page, "#MX-06-parts"))

    # ---- checkable citations ----
    snap = page.evaluate(r"""async () => { const t = $tw.wiki.getTiddlerText('$:/vtw/source/SRC-LP20') || '';
        const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(t));
        return [[...new Uint8Array(d)].map(b => b.toString(16).padStart(2, '0')).join(''), (t.match(/\n/g) || []).length,
                $tw.wiki.getTiddler('SRC-LP20').fields.sha256, $tw.wiki.getTiddler('SRC-LP20').fields.lines]; }""")
    check("the embedded paper matches the sha256 and line count recorded on SRC-LP20", snap[0] == snap[2] and str(snap[1]) == snap[3], str(snap[:2]))
    src = navigate(page, "SRC-LP20")
    check("the paper's page states its version and shows every line with an anchor",
          src.locator("dl.vtw-srcmeta").count() == 1 and snap[2] in src.locator("dl.vtw-srcmeta").text_content()
          and src.locator(".vtw-lptext .vtw-lpline").count() == int(snap[3]) and src.locator("#lp-L101").count() == 1)
    mx8 = navigate(page, "MX-08")
    link = mx8.locator("a.tc-tiddlylink[href='#SRC-LP20']", has_text="line").first
    link_text = link.text_content()
    wanted = page.evaluate(r"""s => { const a = s.slice(s.search(/lines?/i)); const out = [];
        for (const m of a.matchAll(/(\d+)(?:\s*[-–]\s*(\d+))?/g)) { const x = +m[1], y = m[2] ? +m[2] : x; for (let n = x; n <= y; n++) out.push(String(n)); }
        return out; }""", link_text)
    link.click()
    page.wait_for_timeout(700)
    hl = page.evaluate("() => [...document.querySelectorAll('.vtw-lptext .vtw-lphl .vtw-lpn')].map(e => e.textContent.trim())")
    check("a 'paper, line' citation on a mechanism opens the paper at that passage, highlighted, with context",
          page.locator(".tc-story-river > [data-tiddler-title='SRC-LP20']").count() == 1 and in_view(page, "#lp-cited")
          and hl == wanted and page.locator("#lp-cited .vtw-lpline").count() >= len(wanted) + 3, f"{link_text!r} -> {hl}")
    rl = navigate(page, "RL-13")
    cite = rl.locator(".vtw-header a.vtw-cite").first
    ref = cite.text_content().strip()
    cite.click()
    page.wait_for_timeout(700)
    hl = page.evaluate("() => [...document.querySelectorAll('.vtw-lptext .vtw-lphl .vtw-lpn')].map(e => e.textContent.trim())")
    check("a provision's source reference is visible and lands on the cited line", ref.startswith("L") and hl and hl[0] == ref.lstrip("L").split("–")[0] and in_view(page, "#lp-cited"), f"{ref} -> {hl}")
    page.evaluate("$tw.wiki.deleteTiddler('$:/temp/vtw/lp-cite')")

    # ---- notes on the paper's text, shown on the records they concern ----
    noted = page.evaluate("$tw.wiki.filterTiddlers('[has[paper_note]!is[system]sort[title]]')")
    note_bad = []
    for t in noted:
        note = navigate(page, t).locator(".vtw-header .vtw-papernote")
        if note.count() != 1 or note.locator("a.tc-tiddlylink[href='#SRC-LP20']", has_text="all notes").count() != 1 \
                or not note.locator("a.tc-tiddlylink[href='#SRC-LP20']", has_text="line").count() \
                or note.locator("a.tc-tiddlylink-missing").count():
            note_bad.append(t)
    check("each note on the paper's text shows on its record's page, with a line link and a link back to the full list",
          noted and not note_bad and navigate(page, "RL-10").locator(".vtw-papernote").count() == 0, f"{noted} bad={note_bad}")
    if "RL-30" in noted:
        navigate(page, "RL-30").locator(".vtw-papernote a.tc-tiddlylink[href='#SRC-LP20']", has_text="lines").first.click()
        page.wait_for_timeout(700)
        hl = page.evaluate("() => [...document.querySelectorAll('.vtw-lptext .vtw-lphl .vtw-lpn')].map(e => e.textContent.trim())")
        check("a line link in a record's note opens the paper at those lines", hl == ["109", "224"] and in_view(page, "#lp-cited"), str(hl))
        page.evaluate("$tw.wiki.deleteTiddler('$:/temp/vtw/lp-cite')")

    # ---- role guides ----
    h = navigate(page, "Home")
    roles = h.locator(".vtw-roles a").all_text_contents()
    guide_bad = []
    for guide, p_ in (("For node operators", "operator"), ("For delegators", "delegator"), ("For validators", "validator")):
        gp = navigate(page, guide)
        heads = gp.locator(".tc-tiddler-body h2").all_text_contents()
        missing = gp.locator(".tc-tiddler-body a.tc-tiddlylink-missing").count()
        nq = page.evaluate("p => $tw.wiki.filterTiddlers('[tag[HQ]contains:participants[' + p + ']]').length", p_)
        inv = gp.locator("details:not([open]) > summary", has_text="Additional reference records tagged for").count()
        if heads[:6] != ["What changes", "Rewards and exposure", "Timing", "What is undecided", "Mechanisms to read", "Questions you can help answer"] \
                or missing or gp.locator(".tc-tiddler-body ul.vtw-read li").count() != nq or inv != 1 or not gp.locator(".tc-tiddler-body a[href^='#MX-']").count():
            guide_bad.append(f"{guide}: {heads} missing={missing} inv={inv}")
    check("Home links three role guides; each has its sections, working links, its practitioner questions and a collapsed inventory",
          roles == ["For node operators", "For delegators", "For validators"] and not guide_bad, "; ".join(guide_bad) or str(roles))

    # ---- step summary block, question first, collapsed carried-in, jumps, budget ----
    step_bad, over = [], {}
    for step in path:
        sp = navigate(page, step)
        dts = sp.locator("dl.vtw-stepsum dt").all_text_contents()
        dds = [d.strip() for d in sp.locator("dl.vtw-stepsum dd").all_text_contents()]
        n_in = page.evaluate("s => $tw.wiki.filterTiddlers('[tag[CN]contains:carried_to[' + s + ']!status[superseded]]').length", step)
        closed = sp.locator("details.vtw-carried:not([open]) > summary").count()
        if dts != ["Purpose", "Done", "Remaining", "Next action"] or not all(dds) \
                or dds[3] != page.evaluate("s => $tw.wiki.getTiddler(s).fields.step_next", step) \
                or (n_in and (closed != 1 or f"({n_in})" not in sp.locator("details.vtw-carried > summary").text_content())) \
                or sp.locator("[id='" + step + "-progress']").count() != 1:
            step_bad.append(f"{step}: {dts} carried={n_in}/{closed}")
        words = visible_words(page, step)
        if words > STEP_BUDGET:
            over[step] = words
    check("every step opens with Purpose / Done / Remaining / Next action, the question next, and carried-in conclusions collapsed with their count",
          not step_bad, "; ".join(step_bad))
    check(f"step pages stay within {STEP_BUDGET} visible words", not over, json.dumps(over))
    sp = navigate(page, "M1.2")
    jumps = []
    for label, target in (("Progress", "M1.2-progress"), ("What it found", "M1.2-found"), ("How it is worked", "M1.2-worked")):
        page.evaluate("window.scrollTo(0, 0)")
        sp.locator(".vtw-jumps button", has_text=label).click()
        page.wait_for_timeout(350)
        jumps.append(in_view(page, f"[id='{target}']"))
    check("the step jumps reach How it is worked, Progress and What it found", all(jumps), str(jumps))

    # ---- experiment pages ----
    ex = navigate(page, "EX-01")
    order = page.evaluate("""() => { const f = document.querySelector('[data-tiddler-title="EX-01"] .vtw-header');
        return [...f.querySelectorAll('.vtw-exsum-h, h3.vtw-exh')].filter(e => !e.closest('details')).map(e => e.textContent.trim()); }""")
    n_fx = page.evaluate("$tw.wiki.filterTiddlers('[tag[FX]contains:experiments[EX-01]]').length")
    check("EX-01 shows Checked / Not checked, then Results with its fixtures, Assumptions and How to reproduce; backlinks collapsed",
          order == ["Checked", "Not checked", "Results", "Assumptions", "How to reproduce"]
          and ex.locator("table.vtw-fxtable tr").count() == n_fx + 1
          and ex.locator("details.vtw-rsec-closed:not([open]) > summary", has_text="Used by").count() == 1, str(order))
    check("a proposed experiment says plainly that nothing is checked yet", "Nothing yet" in navigate(page, "EX-02").locator(".vtw-exsum-yes").text_content())

    # ---- reference lists, mechanism index, sidebar, notes ----
    rl10 = navigate(page, "RL-10")
    check("reverse-reference lists are collapsed by default",
          rl10.locator("details.vtw-rsec-closed:not([open]) > summary", has_text="Used by").count() == 1
          and rl10.locator(".vtw-rsec h3", has_text="Used by").count() == 0)
    check("the mechanism index has no duplicate list of drafted stories", "Stories drafted" not in navigate(page, "View: Mechanism stories").text_content())
    side = page.locator(".tc-sidebar-scrollable .vtw-side")
    steps_side = side.locator(".vtw-side-step a").all()
    check("the sidebar shows short step labels with the full name on hover, and secondary lists behind disclosures",
          len(steps_side) == len(path)
          and all(a.get_attribute("title") == page.evaluate("s => $tw.wiki.getTiddler(s).fields.caption", s) for a, s in zip(steps_side, path))
          and side.locator("details:not([open]) > summary", has_text="More views").count() == 1
          and side.locator("details:not([open]) > summary", has_text="Record types").count() == 1)
    notes_text = navigate(page, "View: Contributor notes").text_content()
    check("the note instructions name a mechanism, not a concept ID", "LP-07" not in notes_text and "Honesty assessment and scoring" in notes_text)

    # ---- answering a practitioner question ----
    before_hq = page.evaluate("$tw.wiki.getTiddler('HQ-01').fields")
    qv = navigate(page, "View: Questions for humans")
    card = qv.locator(".vtw-hq", has=page.locator("a", has_text=page.evaluate("$tw.wiki.getTiddler('HQ-01').fields.caption")))
    card.locator("button", has_text="Answer this").click()
    empty_disabled = card.locator("button.vtw-answer-save").is_disabled()
    card.locator("textarea.vtw-answer-text").fill("Browser check answer.")
    card.locator("input.vtw-answer-name").fill("Checker")
    card.locator("label.tc-radio", has_text="both").click()
    page.wait_for_timeout(200)
    card.locator("button", has_text="Save answer").click()
    page.wait_for_timeout(300)
    after_hq = page.evaluate("$tw.wiki.getTiddler('HQ-01').fields")
    check("a practitioner question can be answered with plain labels and one Save; the record gets its answer fields",
          empty_disabled and after_hq.get("answer") == "Browser check answer." and after_hq.get("answered_by") == "Checker"
          and after_hq.get("answer_basis") == "both" and after_hq.get("status") == "answered"
          and "answer basis" not in qv.text_content() and "set ''status''" not in qv.text_content()
          and not page.evaluate("$tw.wiki.tiddlerExists('$:/temp/vtw/answer/HQ-01')"))
    page.evaluate("f => $tw.wiki.addTiddler(new $tw.Tiddler(f))", before_hq)

    # ---- narrow layout ----
    page.set_viewport_size({"width": 800, "height": 1000})
    navigate(page, "Home")
    order = page.evaluate("""() => [document.querySelector('.tc-story-river').getBoundingClientRect().top,
                                    document.querySelector('.tc-sidebar-scrollable').getBoundingClientRect().top]""")
    check("at 800px the page comes before the sidebar, and badges still do not wrap",
          order[0] < order[1] and not wrapped_badges(page, "Home"), str(order))
    page.set_viewport_size({"width": 1400, "height": 1000})
    tw_open(page, copy)  # reload: drop the in-memory test edits

    page.evaluate("$tw.wiki.addTiddler({title:'$:/config/vtw/mode', text:'editor'})")
    navigate(page, "MX-06")
    check("editor view keeps the technical title", page.evaluate("() => document.querySelector('.tc-story-river > [data-tiddler-title=\"MX-06\"] .tc-titlebar h2.tc-title').textContent.trim()") == "MX-06")
    check("opens from disk; Home renders", "Validator track workbench" in page.title() or page.locator('[data-tiddler-title="Home"]').count(), page.title())
    check("TiddlyWiki version recorded", page.evaluate("$tw.version") == "5.4.1" and "tiddlywiki.com/empty.html" in page.evaluate("$tw.wiki.getTiddlerText('About this wiki')"), page.evaluate("$tw.version"))

    # ---- render every view, every record type index, conventions and every record ----
    titles = page.evaluate("""() => $tw.wiki.filterTiddlers('[[Home]] [[Conventions]] [[About this wiki]] [tag[View]] [tag[Task]] [tag[Stage]] [tag[Source]] LP MX GT RL VD CL FR SC EX FX CS HQ [tag[Record]] [tag[FX]] [tag[Context]]')""")
    bad = {}
    for t in titles:
        frame = navigate(page, t)
        e = errors_in(frame)
        if e:
            bad[t] = e
    check(f"{len(titles)} tiddlers render without TiddlyWiki errors", not bad, json.dumps(bad)[:300])
    lp = navigate(page, "LP-04")
    text = lp.inner_text()
    need = ["Provisions", "RL-10", "Design questions", "VD-06", "VD-12", "Claims", "CL-08", "CL-09", "Cases", "Findings", "FR-01", "FR-05", "Experiments", "EX-01"]
    check("LP-04 page reaches provisions, design questions, claims, cases, findings, examples", all(n in text for n in need), ", ".join(n for n in need if n not in text))
    check("LP-04 shows no missing-link markers", lp.locator(".vtw-missing").count() == 0)
    for t, want in (("LP-07", ["RL-25", "VD-09", "CL-07", "SC-11", "FR-14"]), ("LP-03", ["RL-07", "VD-01", "FR-02", "SC-03"]),
                    ("CL-07", ["VD-09", "SC-11"]), ("EX-01", ["EX-01.F2", "FR-24"]), ("VD-06", ["RL-10", "RL-13"])):
        txt = navigate(page, t).inner_text()
        check(f"{t} links resolve both ways", all(w in txt for w in want), ", ".join(w for w in want if w not in txt))

    rc = navigate(page, "View: Reference check")
    check("Reference check view lists no missing targets", rc.locator("td.vtw-missing").count() == 0)
    txt = navigate(page, "View: Open decisions").inner_text()
    check("Design questions view lists VD-06 and excludes split VD-20 when present",
          "VD-06" in txt and ("VD-20" not in txt))
    txt = navigate(page, "View: Parameter sheet").inner_text()
    check("Parameter sheet lists RL-20 N=33 and RL-54 94%", "RL-20" in txt and "33" in txt and "RL-54" in txt)

    # ---- sidebar search (core search) ----
    page.fill("input[type=search]", "transferBond")
    try:
        page.wait_for_function("document.querySelector('.tc-sidebar-search') && document.querySelector('.tc-sidebar-search').innerText.includes('RL-28')", timeout=5000)
    except Exception:
        pass
    srch = page.locator(".tc-sidebar-search").inner_text()
    check("core search finds transferBond records", "RL-28" in srch or "RL-29" in srch, srch[:120].replace("\n", " "))
    page.fill("input[type=search]", "")

    # ---- record finder filters ----
    f = navigate(page, "View: Record finder")
    total = int(re.match(r"\d+", f.locator(".vtw-count").first.inner_text()).group())
    sels = f.locator("select")
    sels.nth(0).select_option("VD")
    sels.nth(1).select_option("LP-04")
    page.wait_for_timeout(300)
    got = f.locator("td.vtw-id").all_inner_texts()
    expect = page.evaluate("$tw.wiki.filterTiddlers('[tag[VD]contains:concepts[LP-04]sort[title]]')")
    check("finder: type + concept filter", got == expect and len(got) > 0, f"{len(got)} of {total}")
    f.locator("input.vtw-q").fill("remainder")
    page.wait_for_timeout(500)
    got = f.locator("td.vtw-id").all_inner_texts()
    check("finder: text search within filters", got == ["VD-12"] or ("VD-12" in got and len(got) < 4), str(got))
    f.locator("button", has_text="clear").click()
    page.wait_for_timeout(300)
    after = int(re.match(r"\d+", f.locator(".vtw-count").first.inner_text()).group())
    check("finder: clear restores all records", after == total, f"{after}/{total}")

    # ---- new-record button produces the next ID with the template's fields ----
    v = navigate(page, "VD")
    v.locator("button.vtw-new").click()
    page.wait_for_timeout(400)
    draft = page.evaluate("""() => { const d = $tw.wiki.filterTiddlers('[is[draft]]'); return d.map(t => $tw.wiki.getTiddler(t).fields); }""")
    nxt = page.evaluate("$tw.wiki.filterTiddlers('[[00]] [tag[VD]removeprefix[VD-]] +[maxall[]add[1]pad[2]addprefix[VD-]]')[0]")
    ok = len(draft) == 1 and draft[0]["draft.title"] == nxt and draft[0].get("record_type") == "VD" and "Record" in draft[0].get("tags", [])
    check("New design question button opens draft with next ID and template fields", ok, str({k: draft[0].get(k) for k in ("draft.title", "record_type", "status", "tags")}) if draft else "no draft")
    page.evaluate("""() => { for (const d of $tw.wiki.filterTiddlers('[is[draft]]')) $tw.wiki.deleteTiddler(d);
                              $tw.wiki.addTiddler({title:'$:/StoryList', list:['Home']}); }""")

    # ---- browser edit -> save -> reopen ----
    page.evaluate("$tw.wiki.deleteTiddler('$:/config/AnimationDuration')")
    marker = "Browser edit check 2026-09-28"
    fr = navigate(page, "FR-24")
    fr.locator('button[class*="Buttons%2Fedit"]').click()
    page.wait_for_selector('[data-tiddler-title="Draft of \'FR-24\'"]')
    ed = page.locator('[data-tiddler-title="Draft of \'FR-24\'"]')
    ed.frame_locator("iframe.tc-edit-texteditor").locator("textarea").fill(marker)
    fld = ed.locator("tr.tc-edit-field").filter(has=page.locator("td.tc-edit-field-name", has_text="caption")).locator("input").first
    fld.fill("MFS leaves part of the node envelope unassigned (browser field edit)")
    ed.locator('button[class*="Buttons%2Fsave"]').click()
    page.wait_for_timeout(300)
    with page.expect_download() as dl:
        page.locator('button[aria-label="save changes"]').first.click()
    saved = work / "browser-saved.html"
    dl.value.save_as(saved)
    check("browser save downloads an HTML file", saved.exists() and saved.stat().st_size > 2_000_000, str(saved.stat().st_size if saved.exists() else 0))
    shutil.copy2(saved, copy)  # editor places the download over the working copy
    tw_open(page, copy, "FR-24")
    txt = navigate(page, "FR-24").inner_text()
    check("browser body and field edits survive save and reopen", marker in txt and "(browser field edit)" in txt)
    saved_store = {t["title"]: t for t in json.loads(subprocess.check_output(VTW + ["export", str(saved), "--all"]))}
    check("the saved file keeps the stored layout and carries no screenshot setting",
          saved_store["MX-06"].get("layout") == "v2" and "$:/config/AnimationDuration" not in saved_store)

    # ---- agent edit -> reload (agent writes the file the browser saved) ----
    agent_marker = "Agent edit check 2026-09-28"
    patch = work / "agent-edit.json"
    tid = json.loads(subprocess.check_output(VTW + ["export", str(copy)]))
    fr24 = next(t for t in tid if t["title"] == "FR-24")
    fr24["text"] = fr24.get("text", "") + "\n\n" + agent_marker
    patch.write_text(json.dumps([fr24]))
    out = subprocess.run(VTW + ["import", str(copy), str(patch)], capture_output=True, text=True)
    check("agent import succeeds on a browser-saved file", out.returncode == 0, out.stdout.strip().splitlines()[-1] if out.stdout else out.stderr[-200:])
    tw_open(page, copy, "FR-24")
    page.reload()
    page.wait_for_function("window.$tw && $tw.wiki && document.querySelector('.tc-story-river')")
    txt = navigate(page, "FR-24").inner_text()
    check("agent edit survives reload (and browser edit is kept)", agent_marker in txt and marker in txt)
    lint = subprocess.run(VTW + ["lint", str(copy)], capture_output=True, text=True)
    check("lint after browser and agent edits", lint.returncode == 0, lint.stdout.strip().splitlines()[-1])
    check("no page script errors", not page_errors, "; ".join(page_errors)[:300])
    print("failed requests (informational):", sorted(set(failed)))
    browser.close()

fails = [r for r in results if not r[1]]
print(f"\n{len(results) - len(fails)}/{len(results)} checks passed")
sys.exit(1 if fails else 0)
