#!/usr/bin/env python3
"""Tiddler-aware helper for the validator-track workbench (TiddlyWiki 5).

Local authoring aid only. It is not a build step and not a second database:
the workbench HTML is the single editable record set.

  vtw.py export  WIKI [--out FILE] [--all]    records (non-system tiddlers) as JSON
  vtw.py import  WIKI FILE [--expect-sha SHA] upsert tiddlers; backs up WIKI first
  vtw.py remove  WIKI TITLE... [--expect-sha SHA]
  vtw.py lint    WIKI                          ID references, schema, vocabularies, scope
  vtw.py diff    OLD NEW                       record-level, field-level changes (HTML or JSON)
  vtw.py counts  WIKI
  vtw.py show    WIKI TITLE... [--fields F,...]  readable text of whole tiddlers
  vtw.py find    WIKI PATTERN [-i] [--type T,...] [--field F,...] [-l] [--max N]
                                               regex search, one snippet per match

show and find read only the workbench's own tiddlers (records, pages and
$:/vtw/), never the TiddlyWiki core, so their output stays small. Use them to
read or search the workbench instead of grep or reading the HTML directly:
the core sits on one line of about 2 MB that a text search can match.

Only the JSON tiddler store inside the HTML is rewritten, in the same form as a
TiddlyWiki 5 browser save (one tiddler per line, sorted by title, "<" escaped).
The HTML shell, boot code and the $:/core plugin are left byte-for-byte intact.
Only a browser save regenerates the shell (page title, head markup such as the
note for agents); lint warns when the shell no longer matches the store.
One writer at a time: save and close (or reload) the browser before running
import/remove, and reopen the file afterwards before the next browser save.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
from html import unescape
from pathlib import Path

STORE_RE = re.compile(r'(<script class="tiddlywiki-tiddler-store" type="application/json">)(.*?)(</script>)', re.S)
BACKUP_DIR = Path(__file__).resolve().parent / "backups"
# The litepaper snapshot the workbench cites (docs/litepaper-2.0.md in this repository).
LITEPAPER = Path(__file__).resolve().parents[1] / "docs" / "litepaper-2.0.md"

# ---------------------------------------------------------------- store access

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_store(path: Path) -> tuple[str, re.Match, list[dict]]:
    html = path.read_text(encoding="utf-8")
    matches = list(STORE_RE.finditer(html))
    if len(matches) != 1:
        sys.exit(f"{path}: expected exactly one tiddler store, found {len(matches)}")
    m = matches[0]
    return html, m, json.loads(m.group(2))


def load_tiddlers(path: Path) -> dict[str, dict]:
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = read_store(path)[2]
    out = {}
    for t in data:
        if t["title"] in out:
            sys.exit(f"{path}: duplicate tiddler title {t['title']!r}")
        out[t["title"]] = t
    return out


def serialise(tiddlers: list[dict]) -> str:
    lines = []
    for t in sorted(tiddlers, key=lambda t: t["title"]):
        lines.append(json.dumps({k: str(v) for k, v in t.items()}, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003C"))
    return "[\n" + ",\n".join(lines) + "\n]"


def write_store(path: Path, tiddlers: list[dict], expect_sha: str | None) -> None:
    before = sha(path)
    if expect_sha and before != expect_sha:
        sys.exit(f"{path} changed since you last inspected it (sha {before[:12]} != expected {expect_sha[:12]}). "
                 "Reload the browser copy and re-check before writing.")
    html, m, _ = read_store(path)
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    backup = BACKUP_DIR / f"{path.stem}.{stamp}.{before[:12]}.html"
    shutil.copy2(path, backup)
    new_html = html[:m.start(2)] + serialise(tiddlers) + html[m.end(2):]
    tmp = path.with_suffix(".tmp")
    tmp.write_text(new_html, encoding="utf-8")
    tmp.replace(path)
    print(f"backup: {backup}\nbefore: {before}\nafter:  {sha(path)}")


def tw_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S%f")[:17]


def is_system(title: str) -> bool:
    return title.startswith("$:/")


def normalise_tags(value) -> str:
    if isinstance(value, list):
        return " ".join(f"[[{v}]]" if " " in v else v for v in value)
    return value


# ---------------------------------------------------------------- list fields

def parse_list(value: str | None) -> list[str]:
    """TiddlyWiki title list: space separated, [[bracketed titles]] may contain spaces."""
    if not value:
        return []
    return [a or b for a, b in re.findall(r"\[\[(.*?)\]\]|(\S+)", value)]


# ---------------------------------------------------------------- lint

def parse_dictionary(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def schema_from(tiddlers: dict[str, dict]) -> tuple[dict, dict, list[str]]:
    """Schema lives in the wiki: $:/vtw/schema/<type>, $:/vtw/relations, $:/vtw/participants."""
    types = {t.removeprefix("$:/vtw/schema/"): f for t, f in tiddlers.items() if t.startswith("$:/vtw/schema/")}
    if not types or "$:/vtw/relations" not in tiddlers:
        sys.exit("No $:/vtw/schema/* or $:/vtw/relations tiddlers; is this the workbench?")
    relations = {k: (v.split() if v != "*" else "*") for k, v in parse_dictionary(tiddlers["$:/vtw/relations"]["text"]).items()}
    participants = parse_list(tiddlers.get("$:/vtw/participants", {}).get("list"))
    return types, relations, participants


# Reserved vocabulary for the M1/M2 scope rule: terms that belong to later milestones.
# An optional local file of additional reserved terms (one regular expression per line,
# '#' for comments) extends the list when present; without it, lint checks the terms below.
LOCAL_RESERVED_TERMS = Path(__file__).resolve().parent / "reserved-terms.local.txt"


def _scope_terms() -> re.Pattern:
    parts = [r"\bcandidate\b", r"expansion"]
    if LOCAL_RESERVED_TERMS.exists():
        parts += [ln.strip() for ln in LOCAL_RESERVED_TERMS.read_text(encoding="utf-8").splitlines()
                  if ln.strip() and not ln.lstrip().startswith("#")]
    return re.compile("|".join(parts), re.I)


SCOPE_TERMS = _scope_terms()
# Reader-facing vocabulary retired by the restructure (errors since 2026-09-29, when the
# migration completed). Field names and filter expressions are not reader text.
RETIRED_TERMS = (
    (re.compile(r"\bopen pieces?\b", re.I), "open piece(s)"),
    (re.compile(r"\bopen decisions?\b", re.I), "open decision(s)"),
    (re.compile(r"\bthings to build\b", re.I), "things to build"),
    (re.compile(r"\bwhat it leaves to be built\b", re.I), "what it leaves to be built"),
    (re.compile(r"\bstill to build or decide\b", re.I), "still to build or decide"),
    (re.compile(r"\bpieces to follow\b", re.I), "pieces to follow"),
    (re.compile(r"\brequires chain\b", re.I), "requires chain"),
    (re.compile(r"\bscenarios?\b", re.I), "scenario(s)"),
    (re.compile(r"\bfamil(?:y|ies)\b", re.I), "family/families"),
    (re.compile(r"\bgates?\b", re.I), "gate(s)"),
)
# Fields a reader sees: page and step prose, mechanism layout fields, and the
# narrative fields in the schemas' display lists (shown under Record details).
# Identifiers, relations, vocabulary values and editor metadata are not prose.
READER_FIELDS = (
    "text", "caption", "question", "starting_point", "overview", "purpose",
    "statement", "basis", "description", "hypothesis", "current_system",
    "next_step", "operation", "in_paper", "contribute", "lenses", "proposals",
    "ask", "why", "answer", "consequence", "would_change", "situation",
    "paper_says", "impact", "summary",
    # mechanism parts table and step fields
    "requires", "step_next", "step_expected", "step_short", "step_purpose", "step_done", "step_remaining",
    # design questions and findings
    "spec_settles", "still_to_test", "authority", "evidence_needed", "residual_uncertainty",
    "follow_up", "design_question", "evidence", "implication",
    # critical questions
    "cases", "holds_if", "established", "control", "smallest_test",
    # claims, cases, components, experiments and fixtures
    "claim", "does_not_establish", "evidence_types", "ambiguity", "litepaper_outcome",
    "observable", "unknowns", "method", "results", "limits", "inputs", "reproduce", "expected",
)
# Attributes whose literal value is displayed. On widgets "title" and "to" are
# targets, so only these; on HTML elements a title or alt is shown as a tooltip.
WIDGET_DISPLAY_ATTRS = ("text", "emptyMessage", "label", "tooltip", "placeholder", "caption")
HTML_DISPLAY_ATTRS = ("title", "alt", "placeholder", "aria-label")


def _attr_re(names):
    return re.compile(r"""(?<![\w-])(?:%s)\s*=\s*(?:\"\"\"(.*?)\"\"\"|"([^"]*)"|'([^']*)')""" % "|".join(map(re.escape, names)), re.S)


WIDGET_ATTR_RE = _attr_re(WIDGET_DISPLAY_ATTRS)
HTML_ATTR_RE = _attr_re(HTML_DISPLAY_ATTRS)
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^<>]*>")
# Stylesheets, scripts and data carry no reader prose.
NON_PROSE_TYPES = frozenset({"text/css", "application/javascript", "application/json"})
# Verbatim source snapshots: the only tiddlers that may carry source_of. Once
# verified against both the source record and the file, their text field (and
# only that field) is exempt from the vocabulary rules, because it is the
# source's own wording. Every other field stays under the normal rules.
SOURCE_SNAPSHOTS = {"$:/vtw/source/SRC-LP20": ("SRC-LP20", LITEPAPER)}
# Reserved terms are allowed only when stage is exactly one of these.
OPEN_STAGES = frozenset({"M3", "M4", "M5"})
TASK_FIELDS = ("stage", "introduced_by", "last_changed_by", "task", "carried_to")
NARRATIVE_FIELDS = ("text", "starting_point", "overview", "basis", "statement", "paper_note")
NARRATIVE_REF = re.compile(r'<<r (?:"([^"]+)"|(\S+?))>>|tiddler="([^"]+)"')


def stage_kind(value) -> str:
    """Return open, M1, M2, absent or unrecognized. Only exact M3, M4 and M5 are open."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return "absent"
    if not isinstance(value, str):
        return "unrecognized"
    if value in OPEN_STAGES:
        return "open"
    if value in ("M1", "M2"):
        return value
    return "unrecognized"


def scope_protection(title: str, fields: dict, record_types) -> str | None:
    """Rule that protects this tiddler, or None when reserved terms are allowed.

    Workbench system pages ($:/vtw/) are always protected; other $:/ tiddlers
    are TiddlyWiki runtime, not workbench prose, and are not scanned (as before).
    Step, view, context and shared pages are protected whatever their fields say.
    A record is exempt only when its title is an ID of its own record type and its
    stage is exactly M3, M4 or M5.
    """
    if is_system(title):
        return "system tiddler" if title.startswith("$:/vtw/") else None
    tags = set(parse_list(fields.get("tags")))
    if "Task" in tags or re.fullmatch(r"M\d+\.\d+", title):
        return "step page"
    if "View" in tags or title == "View" or title.startswith("View:"):
        return "view page"
    if "Context" in tags:
        return "context page"
    rt = fields.get("record_type")
    if rt in record_types and title.startswith(f"{rt}-"):
        kind = stage_kind(fields.get("stage"))
        if kind == "open":
            return None
        if kind in ("M1", "M2"):
            return f"{kind} record"
        if kind == "absent":
            return "record with no stage"
        return "record with unrecognized stage"
    return "shared page"


def _skip_bracket(text: str, i: int, open_s: str, close_s: str) -> int:
    j = text.find(close_s, i + len(open_s))
    return len(text) if j < 0 else j + len(close_s)


def _skip_widget(text: str, i: int) -> int:
    """Index just after a <$...> or </$...> tag. Quotes and nested brackets can hold '>'."""
    j = i
    n = len(text)
    quote = ""
    while j < n:
        if quote:
            if text[j] == "\\":
                j += 2
                continue
            if text[j] == quote:
                quote = ""
            j += 1
            continue
        if text.startswith("{{{", j):
            j = _skip_bracket(text, j, "{{{", "}}}")
            continue
        if text.startswith("{{", j):
            j = _skip_bracket(text, j, "{{", "}}")
            continue
        if text.startswith("<<", j):
            j = _skip_bracket(text, j, "<<", ">>")
            continue
        c = text[j]
        if c in "\"'":
            quote = c
            j += 1
            continue
        if c == ">":
            return j + 1
        j += 1
    return n


def _display_attrs(tag: str, pattern) -> str:
    """Literal displayed attribute values of one widget or HTML tag."""
    vals = []
    for m in pattern.finditer(tag):
        val = next((g for g in m.groups() if g is not None), "")
        vals.append(_strip_markup(val))
    return " ".join(vals)


def _strip_markup(text: str) -> str:
    """Reader prose only: drop widgets, macro calls, transclusions, filters and
    link targets, but keep what renders: displayed widget attributes (text,
    emptyMessage, label ...), HTML title attributes and link labels."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("<%", i):
            i = _skip_bracket(text, i, "<%", "%>")
            out.append(" ")
            continue
        if text.startswith("<$", i) or text.startswith("</$", i):
            j = _skip_widget(text, i)
            out.append(" " + _display_attrs(text[i:j], WIDGET_ATTR_RE) + " ")
            i = j
            continue
        if text.startswith("<<", i):
            i = _skip_bracket(text, i, "<<", ">>")
            out.append(" ")
            continue
        if text.startswith("{{{", i):
            i = _skip_bracket(text, i, "{{{", "}}}")
            out.append(" ")
            continue
        if text.startswith("{{", i):
            i = _skip_bracket(text, i, "{{", "}}")
            out.append(" ")
            continue
        if text.startswith("[[", i):
            j = text.find("]]", i + 2)
            if j >= 0:
                inner = text[i + 2:j]
                out.append(" " + (inner.split("|", 1)[0] if "|" in inner else inner) + " ")
                i = j + 2
                continue
        m = HTML_TAG_RE.match(text, i)
        if m:
            out.append(" " + _display_attrs(m.group(0), HTML_ATTR_RE) + " ")
            i = m.end()
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def literal_template_text(text: str) -> str:
    """Visible prose of a template: drop pragmas, widget tags and macro calls."""
    kept = []
    for line in text.splitlines():
        if line.strip().startswith("\\"):
            continue
        kept.append(line)
    return _strip_markup("\n".join(kept))


def dictionary_values(text: str) -> str:
    vals = []
    for line in text.splitlines():
        if ":" in line:
            vals.append(line.split(":", 1)[1])
    return "\n".join(vals)


def retired_hits(blob: str) -> list[tuple[str, str]]:
    found = []
    for cre, label in RETIRED_TERMS:
        for match in sorted(set(m.group(0) for m in cre.finditer(blob or ""))):
            found.append((label, match))
    return found


def snapshot_problems(title: str, fields: dict, tiddlers: dict[str, dict]) -> list[str]:
    """Errors for a tiddler that carries source_of or holds a registered snapshot title."""
    reg = SOURCE_SNAPSHOTS.get(title)
    if reg is None:
        if fields.get("source_of"):
            return [f"{title}: source_of is only allowed on a registered source snapshot"]
        return []
    of, path = reg
    problems = []
    if fields.get("source_of") != of:
        problems.append(f"{title}: source_of must be {of!r}")
    if fields.get("type") != "text/plain":
        problems.append(f"{title}: a source snapshot must have type text/plain")
    text = fields.get("text", "")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    rec = tiddlers.get(of)
    if not rec:
        problems.append(f"{title}: source record {of!r} does not exist")
    else:
        if digest != rec.get("sha256"):
            problems.append(f"{title}: text sha256 {digest} != {of} sha256 {rec.get('sha256')}")
        if not rec.get("lines") or text.count("\n") != int(rec.get("lines")):
            problems.append(f"{title}: {text.count(chr(10))} lines != {of} lines {rec.get('lines')}")
    if path.exists() and digest != hashlib.sha256(path.read_bytes()).hexdigest():
        problems.append(f"{title}: text differs from {path}")
    return problems


def verified_snapshot(title: str, fields: dict, tiddlers: dict[str, dict]) -> bool:
    """True only for a registered snapshot whose identity checks all pass."""
    return title in SOURCE_SNAPSHOTS and not snapshot_problems(title, fields, tiddlers)


def retired_warnings_for(title: str, fields: dict, exempt_text: bool = False) -> list[str]:
    """Warnings for retired reader vocabulary. Does not change the scope rule.

    exempt_text skips the text field only; it is set for a verified source snapshot.
    """
    out = []
    if fields.get("type") in NON_PROSE_TYPES:
        return out
    if is_system(title):
        if not title.startswith("$:/vtw/"):
            return out
        if fields.get("type") == "application/x-tiddler-dictionary":
            blobs = [("text", dictionary_values(fields.get("text", "")))]
        elif title.startswith("$:/vtw/schema/"):
            blobs = [(name, fields.get(name, "")) for name in ("name", "plural", "text")]
        else:
            blobs = [("text", literal_template_text(fields.get("text", "")))]
            for name in ("caption", "name", "plural", "description"):
                if fields.get(name):
                    blobs.append((name, fields.get(name, "")))
    else:
        # Strip macros and widgets so a call such as <<vtw-gates>> is not reader prose.
        blobs = [(name, literal_template_text(fields.get(name, ""))) for name in READER_FIELDS if fields.get(name)]
    for field, blob in blobs:
        if exempt_text and field == "text":
            continue
        for label, match in retired_hits(blob):
            out.append(f"{title}.{field}: retired vocabulary ({label}): {match!r}")
    return out


def lint_tiddlers(tiddlers: dict[str, dict]) -> tuple[list[str], list[str], int]:
    types, relations, participants = schema_from(tiddlers)
    errors, warnings = [], []
    records = {t: f for t, f in tiddlers.items() if f.get("record_type") in types and not is_system(t)}
    captions: dict[str, str] = {}
    lp_lines = int(tiddlers.get("SRC-LP20", {}).get("lines", "0") or 0)

    for title, f in sorted(records.items()):
        rt = f["record_type"]
        spec = types[rt]
        tags = parse_list(f.get("tags"))
        if not re.match(spec.get("id-pattern", "^$"), title):
            errors.append(f"{title}: title does not match {rt} ID pattern {spec.get('id-pattern')}")
        for tag in parse_list(spec.get("required-tags")):
            if tag not in tags:
                errors.append(f"{title}: missing tag {tag!r}")
        for field in parse_list(spec.get("required")):
            if not f.get(field, "").strip():
                errors.append(f"{title}: required field {field!r} is empty")
        for key, vocab in spec.items():
            if key.startswith("vocab-"):
                field, allowed = key[6:], parse_list(vocab)
                if f.get(field) and f[field] not in allowed:
                    errors.append(f"{title}: {field}={f[field]!r} not in {allowed}")
            if key.startswith("pattern-"):
                field = key[8:]
                if f.get(field) and not re.match(vocab, f[field]):
                    errors.append(f"{title}: {field}={f[field]!r} does not match {vocab}")
        for field in TASK_FIELDS:
            for v in parse_list(f.get(field)):
                if v not in tiddlers:
                    errors.append(f"{title}: {field}={v!r} has no stage/task tiddler")
        for p in parse_list(f.get("participants")):
            if p not in participants:
                errors.append(f"{title}: participant {p!r} not in {participants}")
        if spec.get("needs-concepts") == "yes" and not parse_list(f.get("concepts")):
            errors.append(f"{title}: record has no concepts")
        cap = f.get("caption", "").strip().lower()
        if cap:
            if cap in captions:
                warnings.append(f"{title}: caption duplicates {captions[cap]}")
            captions[cap] = title
        for field, allowed in relations.items():
            refs = parse_list(f.get(field))
            if len(refs) != len(set(refs)):
                warnings.append(f"{title}: {field} lists an ID twice")
            for ref in refs:
                target = tiddlers.get(ref)
                if target is None:
                    errors.append(f"{title}: {field} -> {ref} does not exist")
                elif ref == title:
                    errors.append(f"{title}: {field} refers to itself")
                elif allowed != "*" and target.get("record_type") not in allowed:
                    errors.append(f"{title}: {field} -> {ref} is {target.get('record_type')}, expected {allowed}")
                elif allowed == "*" and target.get("record_type") not in types:
                    errors.append(f"{title}: {field} -> {ref} is not a record")
                elif field == "pair_with" and title not in parse_list(target.get("pair_with")):
                    errors.append(f"{title}: pair_with -> {ref} is not reciprocated")
                elif field not in ("pair_with", "related"):
                    back = [bf for bf in relations if bf not in ("pair_with",) and title in parse_list(target.get(bf))]
                    # Mutual depends_on is two real edges (each consumes an output
                    # of the other), not a derived reverse stored twice.
                    if field == "depends_on":
                        back = [bf for bf in back if bf != "depends_on"]
                    if back and not (rt == "LP" or target.get("record_type") == "LP"):
                        warnings.append(f"{title}.{field} -> {ref} is also stored in reverse ({ref}.{back[0]})")
        for part in [p.strip() for p in f.get("source_ref", "").split(";") if p.strip()]:
            m = re.match(r"^(SRC-[A-Z0-9-]+)(.*)$", part)
            if not m or m.group(1) not in tiddlers:
                errors.append(f"{title}: source_ref {part!r} does not start with an existing SRC id")
                continue
            if m.group(1) == "SRC-LP20":
                ranges = re.findall(r"L(\d+)(?:[-–](\d+))?", m.group(2))
                if not ranges:
                    errors.append(f"{title}: source_ref {part!r} has no line locator")
                for a, b in ranges:
                    if not (1 <= int(a) <= int(b or a) <= lp_lines):
                        errors.append(f"{title}: litepaper line range L{a}-{b} outside 1-{lp_lines}")
    # record references inside narrative text (journeys, overviews, conclusions)
    for title, f in sorted(tiddlers.items()):
        if is_system(title):
            continue
        for field in NARRATIVE_FIELDS:
            for m in NARRATIVE_REF.finditer(f.get(field, "")):
                ref = m.group(1) or m.group(2) or m.group(3)
                if ref not in tiddlers and not ref.startswith("$:/"):
                    errors.append(f"{title}.{field}: narrative link to {ref!r} does not exist")
    # Reserved terms: allowed only on records staged exactly M3, M4 or M5.
    for title, f in sorted(tiddlers.items()):
        rule = scope_protection(title, f, types)
        if rule is None:
            continue
        skip = ("created", "modified", "text") if verified_snapshot(title, f, tiddlers) else ("created", "modified")
        body = " ".join(str(v) for k, v in f.items() if k not in skip)
        for hit in sorted(set(m.group(0).lower() for m in SCOPE_TERMS.finditer(body))):
            errors.append(f"{title}: reserved term in {rule}: {hit!r}")
    # Retired reader vocabulary (errors); the scope rule above is unchanged.
    for title, f in sorted(tiddlers.items()):
        errors.extend(retired_warnings_for(title, f, exempt_text=verified_snapshot(title, f, tiddlers)))
    # litepaper snapshot identity
    src = tiddlers.get("SRC-LP20")
    if not src:
        errors.append("SRC-LP20 missing")
    elif LITEPAPER.exists():
        actual = hashlib.sha256(LITEPAPER.read_bytes()).hexdigest()
        if actual != src.get("sha256"):
            errors.append(f"SRC-LP20: litepaper sha256 {actual} != recorded {src.get('sha256')}")
        if len(LITEPAPER.read_text(encoding="utf-8").splitlines()) != lp_lines:
            errors.append("SRC-LP20: recorded line count does not match the file")
    # Source snapshots: only registered titles may carry source_of, and they
    # must match their source record and file exactly.
    for title, f in sorted(tiddlers.items()):
        if f.get("source_of") or title in SOURCE_SNAPSHOTS:
            errors.extend(snapshot_problems(title, f, tiddlers))
    return errors, warnings, len(records)


def shell_warnings(shell: str, tiddlers: dict[str, dict]) -> list[str]:
    """The HTML around the tiddler store is written only by a browser save; import
    and remove leave it byte-for-byte. Warn when it no longer reflects the store:
    raw markup for the head (such as the note for agents) and the page title."""
    out = []
    for title, t in sorted(tiddlers.items()):
        if "$:/tags/RawMarkup" in parse_list(t.get("tags")) and t.get("text", "") not in shell:
            out.append(f"{title}: text is not in the file's <head>; save once from a browser to write it")
    site = tiddlers.get("$:/SiteTitle", {}).get("text", "")
    m = re.search(r"<title>(.*?)</title>", shell, re.S)
    if site and not (m and site in unescape(m.group(1))):
        out.append(f"$:/SiteTitle: the file's <title> does not show {site!r}; save once from a browser to write it")
    return out


def lint(path: Path) -> int:
    errors, warnings, n = lint_tiddlers(load_tiddlers(path))
    if path.suffix != ".json":
        html, m, _ = read_store(path)
        warnings += shell_warnings(html[:m.start(2)] + html[m.end(2):], load_tiddlers(path))
    for e in errors:
        print("ERROR  ", e)
    for w in warnings:
        print("warning", w)
    print(f"{n} records checked: {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


# ---------------------------------------------------------------- diff and counts

IGNORED_DIFF_FIELDS = {"modified", "created", "modifier", "creator", "revision", "bag"}


def diff(old: Path, new: Path) -> None:
    a, b = load_tiddlers(old), load_tiddlers(new)
    skip = lambda t: t.startswith("$:/temp") or t.startswith("$:/state") or t in ("$:/StoryList", "$:/HistoryList") or t == "$:/core"
    created = sorted(t for t in b if t not in a and not skip(t))
    removed = sorted(t for t in a if t not in b and not skip(t))
    changed = []
    for t in sorted(set(a) & set(b)):
        if skip(t):
            continue
        fa, fb = a[t], b[t]
        fields = sorted((set(fa) | set(fb)) - IGNORED_DIFF_FIELDS)
        delta = [(k, fa.get(k), fb.get(k)) for k in fields if fa.get(k) != fb.get(k)]
        if delta:
            changed.append((t, delta))
    print(f"created {len(created)} · modified {len(changed)} · removed {len(removed)}")
    for t in created:
        print(f"+ {t}  {b[t].get('caption', '')}")
    for t in removed:
        print(f"- {t}  {a[t].get('caption', '')}")
    for t, delta in changed:
        print(f"~ {t}")
        for k, x, y in delta:
            short = lambda s: "∅" if s is None else (s if len(s) < 100 else s[:97] + "…")
            print(f"    {k}: {short(x)!r} -> {short(y)!r}")


def counts(path: Path) -> None:
    tiddlers = load_tiddlers(path)
    types, _, _ = schema_from(tiddlers)
    by: dict[str, int] = {}
    for t, f in tiddlers.items():
        rt = f.get("record_type")
        if rt in types and not is_system(t):
            by[rt] = by.get(rt, 0) + 1
    for rt in sorted(types):
        print(f"{rt:4} {by.get(rt, 0):4}  {types[rt].get('plural', '')}")


# ---------------------------------------------------------------- show and find

# Editor metadata: not useful when reading a tiddler.
READ_SKIP_FIELDS = ("created", "modified", "modifier", "creator", "revision", "bag")
SNIPPET = 70  # characters of context each side of a match


def is_workbench(title: str) -> bool:
    """Records, pages and $:/vtw/ tiddlers; not the TiddlyWiki core, themes or runtime state."""
    return not is_system(title) or title.startswith("$:/vtw/")


def split_names(values: list[str] | None) -> list[str]:
    """--fields a,b --fields c -> [a, b, c]."""
    return [v.strip() for arg in values or [] for v in arg.split(",") if v.strip()]


def show_text(tiddlers: dict[str, dict], titles: list[str], fields: list[str] | None = None) -> tuple[str, list[str]]:
    """Readable text of whole tiddlers, and the titles that were not found."""
    out, missing = [], []
    for title in titles:
        t = tiddlers.get(title)
        if t is None or not is_workbench(title):
            missing.append(title)
            continue
        cap = t.get("caption", "")
        out.append(f"== {title}" + (f"  {cap}" if cap else ""))
        names = fields if fields else [k for k in t if k not in READ_SKIP_FIELDS and k != "title"]
        for k in names:
            if k not in t:
                continue
            v = str(t[k])
            if "\n" in v:
                out.append(f"{k}:")
                out.extend("    " + line for line in v.splitlines())
            else:
                out.append(f"{k}: {v}")
        out.append("")
    return "\n".join(out), missing


def find_hits(tiddlers: dict[str, dict], pattern: str, ignore_case: bool = False,
              types: list[str] | None = None, fields: list[str] | None = None) -> list[tuple[str, str, int | None, str]]:
    """(title, field, line, snippet) for every match in the workbench's own tiddlers.

    line is the 1-based line within the field when the field has several lines
    (for the embedded litepaper, that is the paper's line number), else None.
    """
    cre = re.compile(pattern, re.I if ignore_case else 0)
    hits = []
    for title in sorted(tiddlers):
        t = tiddlers[title]
        if not is_workbench(title) or (types and t.get("record_type") not in types):
            continue
        for k in sorted(t):
            if k in READ_SKIP_FIELDS or (fields and k not in fields):
                continue
            v = str(t[k])
            lines = v.splitlines() or [v]
            for n, line in enumerate(lines, 1):
                for m in cre.finditer(line):
                    a, b = max(0, m.start() - SNIPPET), min(len(line), m.end() + SNIPPET)
                    snip = " ".join(line[a:b].split())
                    snip = ("…" if a else "") + snip + ("…" if b < len(line) else "")
                    hits.append((title, k, n if len(lines) > 1 else None, snip))
    return hits


def find(path: Path, pattern: str, ignore_case: bool, types: list[str], fields: list[str],
         titles_only: bool, limit: int) -> int:
    tiddlers = load_tiddlers(path)
    hits = find_hits(tiddlers, pattern, ignore_case, types, fields)
    titles = list(dict.fromkeys(h[0] for h in hits))
    if titles_only:
        for title in titles:
            cap = tiddlers[title].get("caption", "")
            print(title + (f"  {cap}" if cap else ""))
    else:
        for title, k, n, snip in hits[:limit]:
            print(f"{title}.{k}" + (f":{n}" if n else "") + f"  {snip}")
        if len(hits) > limit:
            print(f"… {len(hits) - limit} more matches not shown (narrow with --type/--field, use -l, or raise --max)")
    sys.stdout.flush()
    print(f"{len(hits)} matches in {len(titles)} tiddlers", file=sys.stderr)
    return 0 if hits else 1


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("export"); p.add_argument("wiki", type=Path); p.add_argument("--out", type=Path); p.add_argument("--all", action="store_true")
    p = sub.add_parser("import"); p.add_argument("wiki", type=Path); p.add_argument("file", type=Path); p.add_argument("--expect-sha")
    p = sub.add_parser("remove"); p.add_argument("wiki", type=Path); p.add_argument("titles", nargs="+"); p.add_argument("--expect-sha")
    p = sub.add_parser("lint"); p.add_argument("wiki", type=Path)
    p = sub.add_parser("diff"); p.add_argument("old", type=Path); p.add_argument("new", type=Path)
    p = sub.add_parser("counts"); p.add_argument("wiki", type=Path)
    p = sub.add_parser("show"); p.add_argument("wiki", type=Path); p.add_argument("titles", nargs="+")
    p.add_argument("--fields", action="append", help="only these fields, comma separated")
    p = sub.add_parser("find"); p.add_argument("wiki", type=Path); p.add_argument("pattern", help="Python regular expression")
    p.add_argument("-i", "--ignore-case", action="store_true")
    p.add_argument("--type", action="append", help="only these record types, comma separated (e.g. GT,SC)")
    p.add_argument("--field", action="append", help="only these fields, comma separated")
    p.add_argument("-l", "--titles-only", action="store_true", help="list matching tiddlers with their captions")
    p.add_argument("--max", type=int, default=100, help="most matches to print (default 100)")
    args = ap.parse_args()

    if args.cmd == "export":
        ts = load_tiddlers(args.wiki)
        sel = [ts[t] for t in sorted(ts) if args.all or (not is_system(t) or t.startswith("$:/vtw/"))]
        text = json.dumps(sel, indent=1, ensure_ascii=False)
        if args.out:
            args.out.write_text(text, encoding="utf-8")
            print(f"{len(sel)} tiddlers -> {args.out}")
        else:
            print(text)
    elif args.cmd == "import":
        _, _, store = read_store(args.wiki)
        existing = {t["title"]: t for t in store}
        incoming = json.loads(args.file.read_text(encoding="utf-8"))
        now = tw_now()
        n_new = n_upd = 0
        for t in incoming:
            t = {k: normalise_tags(v) for k, v in t.items() if v is not None}
            old = existing.get(t["title"])
            if old:
                same = {k: v for k, v in old.items() if k not in IGNORED_DIFF_FIELDS} == {k: v for k, v in t.items() if k not in IGNORED_DIFF_FIELDS}
                if same:
                    continue
                t.setdefault("created", old.get("created", now))
                n_upd += 1
            else:
                t.setdefault("created", now)
                n_new += 1
            t["modified"] = now
            t.setdefault("modifier", "agent")
            existing[t["title"]] = t
        write_store(args.wiki, list(existing.values()), args.expect_sha)
        print(f"imported: {n_new} new, {n_upd} updated")
    elif args.cmd == "remove":
        _, _, store = read_store(args.wiki)
        keep = [t for t in store if t["title"] not in set(args.titles)]
        missing = set(args.titles) - {t["title"] for t in store}
        if missing:
            sys.exit(f"not found: {sorted(missing)}")
        write_store(args.wiki, keep, args.expect_sha)
    elif args.cmd == "lint":
        return lint(args.wiki)
    elif args.cmd == "diff":
        diff(args.old, args.new)
    elif args.cmd == "counts":
        counts(args.wiki)
    elif args.cmd == "show":
        text, missing = show_text(load_tiddlers(args.wiki), args.titles, split_names(args.fields))
        print(text, end="")
        if missing:
            print(f"not found (or not a workbench tiddler): {missing}", file=sys.stderr)
            return 1
    elif args.cmd == "find":
        try:
            return find(args.wiki, args.pattern, args.ignore_case, split_names(args.type),
                        split_names(args.field), args.titles_only, args.max)
        except re.error as e:
            sys.exit(f"invalid pattern {args.pattern!r}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
