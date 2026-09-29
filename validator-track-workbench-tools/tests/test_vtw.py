#!/usr/bin/env python3
"""Checks for vtw.py.

Stage rule: reserved vocabulary is allowed only on a
non-system record whose stage field is exactly "M3", "M4" or "M5".
"m3", "M3x", "M6" and any padded value such as " M3" are protected
(unrecognized). A missing, empty or whitespace-only stage is protected
(no stage). Shared pages, step pages and system tiddlers stay protected
even if their stage field is M3 or later.

Tests copy the main workbench into a temp directory and lint in memory.
They do not write the main workbench.
"""

import shutil
from pathlib import Path
import tempfile
import unittest
from pathlib import Path

import sys; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import vtw

MAIN = Path(__file__).resolve().parents[2] / "validator-track-workbench.html"


class ScopeAndDependsOn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.copy_path = Path(cls.tmp.name) / "workbench.html"
        shutil.copyfile(MAIN, cls.copy_path)
        cls.base = vtw.load_tiddlers(cls.copy_path)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def edited(self, changes, term_titles=()):
        store = dict(self.base)
        for title, fields in changes.items():
            rec = dict(store[title]) if title in store else {"title": title, "text": ""}
            rec.update(fields)
            rec["title"] = title
            store[title] = rec
        for title in term_titles:
            rec = store[title]
            rec["text"] = (rec.get("text") or "") + " expansion"
        return store

    def lint(self, store):
        return vtw.lint_tiddlers(store)

    def scope_errors(self, store, title):
        errors, _, _ = self.lint(store)
        prefix = f"{title}: reserved term"
        return [e for e in errors if e.startswith(prefix)]

    def test_reserved_term_in_m1_record(self):
        self.assertIn("MX-01", self.base)
        store = self.edited({"MX-01": {"stage": "M1"}}, ("MX-01",))
        errs = self.scope_errors(store, "MX-01")
        self.assertEqual(errs, ["MX-01: reserved term in M1 record: 'expansion'"])

    def test_reserved_term_in_m2_record(self):
        store = self.edited({"MX-01": {"stage": "M2"}}, ("MX-01",))
        errs = self.scope_errors(store, "MX-01")
        self.assertEqual(errs, ["MX-01: reserved term in M2 record: 'expansion'"])

    def test_reserved_term_allowed_in_m3_m4_m5_records(self):
        for stage in ("M3", "M4", "M5"):
            with self.subTest(stage=stage):
                store = self.edited({"MX-01": {"stage": stage}}, ("MX-01",))
                self.assertIn("expansion", store["MX-01"]["text"])
                self.assertEqual(self.scope_errors(store, "MX-01"), [])

    def test_reserved_term_allowed_on_a_non_mechanism_record(self):
        self.assertEqual(self.base["FR-01"].get("record_type"), "FR")
        store = self.edited({"FR-01": {"stage": "M3"}}, ("FR-01",))
        self.assertIn("expansion", store["FR-01"]["text"])
        self.assertEqual(self.scope_errors(store, "FR-01"), [])

    def test_reserved_term_in_record_with_no_stage(self):
        for label, fields in (
            ("missing", {"stage": None}),
            ("empty", {"stage": ""}),
            ("blank", {"stage": "   "}),
        ):
            with self.subTest(label=label):
                store = self.edited({"MX-01": fields}, ("MX-01",))
                if fields["stage"] is None:
                    del store["MX-01"]["stage"]
                errs = self.scope_errors(store, "MX-01")
                self.assertEqual(errs, ["MX-01: reserved term in record with no stage: 'expansion'"])

    def test_malformed_stage_is_protected(self):
        # m3 and M3x are the brief's examples. M6 is unknown. Padding is not
        # stripped: " M3" is not the open stage M3.
        for stage in ("M3x", "m3", "M6", " M3", "M3 ", "M3 M4"):
            with self.subTest(stage=stage):
                store = self.edited({"MX-01": {"stage": stage}}, ("MX-01",))
                errs = self.scope_errors(store, "MX-01")
                self.assertEqual(
                    errs,
                    ["MX-01: reserved term in record with unrecognized stage: 'expansion'"],
                )

    def test_reserved_term_in_system_tiddler(self):
        store = self.edited({"$:/vtw/task-g-probe": {"text": ""}}, ("$:/vtw/task-g-probe",))
        errs = self.scope_errors(store, "$:/vtw/task-g-probe")
        self.assertEqual(errs, ["$:/vtw/task-g-probe: reserved term in system tiddler: 'expansion'"])

    def test_plugin_marker_does_not_exempt_a_workbench_system_page(self):
        for marker in ("plugin", "theme"):
            with self.subTest(marker=marker):
                title = "$:/vtw/review-probe"
                store = self.edited({title: {"stage": "M3", "record_type": "MX", "plugin-type": marker}}, (title,))
                self.assertEqual(self.scope_errors(store, title),
                                 [f"{title}: reserved term in system tiddler: 'expansion'"])

    def test_non_workbench_system_tiddlers_are_not_scanned(self):
        # TiddlyWiki runtime ($:/core, $:/themes/...) is not workbench prose; unchanged from the original tool.
        store = self.edited({"$:/task-g-probe": {"text": ""}}, ("$:/task-g-probe",))
        self.assertEqual(self.scope_errors(store, "$:/task-g-probe"), [])

    def test_record_metadata_does_not_exempt_shared_pages(self):
        cases = (("Home", "shared page"), ("Conventions", "shared page"), ("Orientation", "context page"),
                 ("View: By participant", "view page"), ("M1.1", "step page"))
        for title, rule in cases:
            with self.subTest(title=title):
                store = self.edited({title: {"stage": "M3", "record_type": "MX"}}, (title,))
                self.assertEqual(self.scope_errors(store, title), [f"{title}: reserved term in {rule}: 'expansion'"])

    def test_record_type_needs_a_matching_id(self):
        store = self.edited({"Loose page": {"stage": "M3", "record_type": "MX"}}, ("Loose page",))
        self.assertEqual(self.scope_errors(store, "Loose page"), ["Loose page: reserved term in shared page: 'expansion'"])

    def test_open_stage_does_not_exempt_a_system_tiddler(self):
        title = "$:/vtw/template/MX"
        store = self.edited({title: {"stage": "M3", "record_type": "MX"}}, (title,))
        errs = self.scope_errors(store, title)
        self.assertEqual(errs, [f"{title}: reserved term in system tiddler: 'expansion'"])

    def test_reserved_term_in_step_page(self):
        for title in ("M1.1", "M1.4", "M2.3"):
            with self.subTest(title=title):
                store = self.edited({title: {}}, (title,))
                errs = self.scope_errors(store, title)
                self.assertEqual(errs, [f"{title}: reserved term in step page: 'expansion'"])

    def test_open_stage_does_not_exempt_a_step_page(self):
        store = self.edited({"M1.1": {"stage": "M5"}}, ("M1.1",))
        errs = self.scope_errors(store, "M1.1")
        self.assertEqual(errs, ["M1.1: reserved term in step page: 'expansion'"])

    def test_shared_view_and_context_pages(self):
        cases = (
            ("Home", "shared page"),
            ("Conventions", "shared page"),
            ("Orientation", "context page"),
            ("View: By participant", "view page"),
            ("View", "view page"),
        )
        for title, rule in cases:
            with self.subTest(title=title):
                self.assertIn(title, self.base)
                store = self.edited({title: {"stage": "M3"}}, (title,))
                errs = self.scope_errors(store, title)
                self.assertEqual(errs, [f"{title}: reserved term in {rule}: 'expansion'"])

    def test_core_plugin_is_not_scanned(self):
        # $:/core is a bundled plugin and contains the ordinary word "candidate".
        errors, _, _ = self.lint(self.edited({}))
        self.assertFalse(any(e.startswith("$:/core:") for e in errors))

    def test_reciprocal_depends_on_does_not_warn(self):
        store = self.edited({
            "MX-01": {"depends_on": "MX-08"},
            "MX-08": {"depends_on": "MX-01"},
        })
        _, warnings, _ = self.lint(store)
        reverse = [w for w in warnings if "also stored in reverse" in w and "MX-01" in w and "MX-08" in w]
        self.assertEqual(reverse, [])

    def test_reciprocal_other_relation_still_warns(self):
        store = self.edited({
            "MX-01": {"mechanisms": "MX-08"},
            "MX-08": {"mechanisms": "MX-01"},
        })
        _, warnings, _ = self.lint(store)
        reverse = [w for w in warnings if "also stored in reverse" in w]
        self.assertIn("MX-01.mechanisms -> MX-08 is also stored in reverse (MX-08.mechanisms)", reverse)
        self.assertIn("MX-08.mechanisms -> MX-01 is also stored in reverse (MX-01.mechanisms)", reverse)

    def test_depends_on_still_warns_when_the_reverse_is_another_field(self):
        store = self.edited({
            "MX-01": {"depends_on": "MX-08"},
            "MX-08": {"mechanisms": "MX-01"},
        })
        _, warnings, _ = self.lint(store)
        self.assertIn(
            "MX-01.depends_on -> MX-08 is also stored in reverse (MX-08.mechanisms)",
            warnings,
        )
        self.assertIn(
            "MX-08.mechanisms -> MX-01 is also stored in reverse (MX-01.depends_on)",
            warnings,
        )


class RetiredVocabulary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.copy_path = Path(cls.tmp.name) / "workbench.html"
        shutil.copyfile(MAIN, cls.copy_path)
        cls.base = vtw.load_tiddlers(cls.copy_path)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def edited(self, changes):
        store = dict(self.base)
        for title, fields in changes.items():
            rec = dict(store[title]) if title in store else {"title": title, "text": ""}
            rec.update(fields)
            rec["title"] = title
            store[title] = rec
        return store

    def retired(self, store, title):
        """Retired-vocabulary findings for one title (reported as lint errors)."""
        errors, warnings, _ = vtw.lint_tiddlers(store)
        return [w for w in errors + warnings if w.startswith(title + ".") and "retired vocabulary" in w]

    def test_reader_field_warns(self):
        store = self.edited({"MX-01": {"purpose": "One open piece remains."}})
        warnings = self.retired(store, "MX-01")
        self.assertIn("MX-01.purpose: retired vocabulary (open piece(s)): 'open piece'", warnings)

    def test_caption_and_question_are_reader_fields(self):
        store = self.edited({"M1.2": {"question": "Which open decisions remain?"}})
        warnings = self.retired(store, "M1.2")
        self.assertTrue(any("open decision(s)" in w for w in warnings))

    def test_non_reader_field_is_quiet(self):
        store = self.edited({"Probe page": {"migration_note": "an open piece and a scenario and a gate"}})
        self.assertEqual(self.retired(store, "Probe page"), [])

    def test_gateways_and_familiar_do_not_match(self):
        store = self.edited({"Probe page": {"text": "Gateways already choose a node. The path is familiar."}})
        self.assertEqual(self.retired(store, "Probe page"), [])

    def test_macro_call_in_a_reader_field_is_not_prose(self):
        store = self.edited({"Probe page": {"text": 'See <<vtw-gates "MX-01">> for the questions.'}})
        self.assertEqual(self.retired(store, "Probe page"), [])

    def test_template_literal_warns(self):
        store = self.edited({"$:/vtw/probe": {"text": "<p>Twelve mechanism families remain.</p>"}})
        warnings = self.retired(store, "$:/vtw/probe")
        self.assertTrue(any("family/families" in w and "families" in w for w in warnings))

    def test_filter_and_macro_text_is_not_literal(self):
        store = self.edited({
            "$:/vtw/probe": {"text": '\\procedure vtw-gates(mx)\n<$list filter="[get[scenarios]]"><<vtw-gates>>ok</$list>\n\\end\n'},
        })
        self.assertEqual(self.retired(store, "$:/vtw/probe"), [])

    def test_conditional_filter_is_not_prose(self):
        store = self.edited({
            "$:/vtw/probe": {"text": "<%if [all[current]get[scenarios]!is[blank]] %>family<%endif%>\n"},
        })
        warnings = self.retired(store, "$:/vtw/probe")
        self.assertTrue(any("family" in w for w in warnings))
        self.assertFalse(any("scenario" in w for w in warnings))

    def test_retired_phrase_inside_a_filter_attribute_is_not_prose(self):
        store = self.edited({
            "$:/vtw/probe": {
                "text": '<$let req={{{ [search-replace:g[Still to build or decide],[Design questions]] }}}>\nfamily\n</$let>\n'
                '<$list filter="[<id>get[scenarios]enlist-input[]]">kept</$list>\n',
            },
        })
        warnings = self.retired(store, "$:/vtw/probe")
        self.assertTrue(any("family" in w for w in warnings))
        self.assertFalse(any("still to build" in w or "scenario" in w for w in warnings))

    def test_dictionary_key_is_not_scanned(self):
        store = self.edited({
            "$:/vtw/probe-dict": {
                "type": "application/x-tiddler-dictionary",
                "text": "scenarios: SC IDs.\nnote: fine\n",
            },
        })
        self.assertEqual(self.retired(store, "$:/vtw/probe-dict"), [])

    def test_dictionary_value_is_scanned(self):
        store = self.edited({
            "$:/vtw/probe-dict": {
                "type": "application/x-tiddler-dictionary",
                "text": "requires: still to build or decide\n",
            },
        })
        warnings = self.retired(store, "$:/vtw/probe-dict")
        self.assertTrue(any("still to build or decide" in w for w in warnings))

    def test_schema_name_is_scanned_and_display_list_is_not(self):
        store = self.edited({
            "$:/vtw/schema/SC": {"name": "Scenario", "plural": "Scenarios", "display": "scenarios pair_with"},
        })
        warnings = self.retired(store, "$:/vtw/schema/SC")
        self.assertTrue(any(".name:" in w and "Scenario" in w for w in warnings))
        self.assertTrue(any(".plural:" in w for w in warnings))
        self.assertFalse(any(".display:" in w for w in warnings))

    def test_stylesheet_and_script_are_not_prose(self):
        store = self.edited({
            "$:/vtw/probe.css": {"type": "text/css", "text": "/* scenario family gates */ .vtw-gate { color: red; }"},
            "$:/vtw/probe.js": {"type": "application/javascript", "text": "// open pieces\nvar scenario = 1;"},
        })
        self.assertEqual(self.retired(store, "$:/vtw/probe.css"), [])
        self.assertEqual(self.retired(store, "$:/vtw/probe.js"), [])

    def test_template_literal_after_widgets_warns(self):
        store = self.edited({"$:/vtw/probe": {"text": '<$link to="View: Open decisions">Open decisions</$link>'}})
        warnings = self.retired(store, "$:/vtw/probe")
        self.assertEqual(len(warnings), 1)
        self.assertIn("'Open decisions'", warnings[0])

    def test_requires_table_heading_warns(self):
        # The earlier parts-table heading, as the mechanisms carried it before the v2 migration.
        table = '<table class="vtw-grid vtw-chain"><tbody>\n<tr><th>Step</th><th>What the paper specifies</th><th>Still to build or decide</th></tr>\n</tbody></table>'
        store = self.edited({"MX-01": {"requires": table}})
        warnings = self.retired(store, "MX-01")
        self.assertIn("MX-01.requires: retired vocabulary (still to build or decide): 'Still to build or decide'", warnings)

    def test_v2_parts_table_heading_is_quiet(self):
        table = '<table class="vtw-grid vtw-parts"><tbody>\n<tr><th>Part</th><th>What happens</th><th>What the paper says</th><th>Design questions</th></tr>\n</tbody></table>'
        store = self.edited({"MX-01": {"requires": table}})
        self.assertFalse(any(w.startswith("MX-01.requires:") for w in self.retired(store, "MX-01")))

    def test_new_reader_fields_warn(self):
        store = self.edited({
            "M2.2": {"step_next": "Waits for the open pieces.", "step_expected": "A scenario list."},
            "VD-09": {"spec_settles": "things to build", "still_to_test": "each gate"},
            "GT-01": {"cases": "Cooperative scenario first (<<r SC-01>>)."},
        })
        self.assertTrue(any(w.startswith("M2.2.step_next:") for w in self.retired(store, "M2.2")))
        self.assertTrue(any(w.startswith("M2.2.step_expected:") for w in self.retired(store, "M2.2")))
        vd = self.retired(store, "VD-09")
        self.assertTrue(any(w.startswith("VD-09.spec_settles:") for w in vd))
        self.assertTrue(any(w.startswith("VD-09.still_to_test:") for w in vd))
        self.assertTrue(any(w.startswith("GT-01.cases:") and "'scenario'" in w for w in self.retired(store, "GT-01")))

    def test_editor_metadata_is_quiet(self):
        store = self.edited({"Probe page": {"migrated_from": "open decisions draft", "source_ref": "gates.md", "reviewed_by": "family"}})
        self.assertEqual(self.retired(store, "Probe page"), [])

    def test_literal_display_attributes_warn(self):
        store = self.edited({"$:/vtw/probe": {"text": '<$text text="Open pieces"/>\n<$list filter="[tag[GT]]" emptyMessage="No gates yet"/>\n<$transclude $variable="vtw-section" label="Scenarios"/>'}})
        warnings = self.retired(store, "$:/vtw/probe")
        self.assertTrue(any("'Open pieces'" in w for w in warnings))
        self.assertTrue(any("'gates'" in w for w in warnings))
        self.assertTrue(any("'Scenarios'" in w for w in warnings))

    def test_non_literal_and_target_attributes_are_quiet(self):
        store = self.edited({"$:/vtw/probe": {"text": '<$text text={{!!caption}}/><$list filter="[get[scenarios]]" emptyMessage=<<none>>/><$link to="View: Open decisions">Design questions</$link><$action-sendmessage $message="tm-new-tiddler" title="Scenario note"/>'}})
        self.assertEqual(self.retired(store, "$:/vtw/probe"), [])

    def test_aliased_link_scans_the_label_not_the_target(self):
        quiet = self.edited({"Probe page": {"text": "See [[Design questions|View: Open decisions]]."}})
        self.assertEqual(self.retired(quiet, "Probe page"), [])
        loud = self.edited({"Probe page": {"text": "See [[Open decisions|VD]]."}})
        self.assertTrue(any("'Open decisions'" in w for w in self.retired(loud, "Probe page")))

    def test_plain_link_shows_its_title(self):
        store = self.edited({"Probe page": {"text": "See [[View: Scenario pairs]]."}})
        self.assertTrue(any("'Scenario'" in w for w in self.retired(store, "Probe page")))

    def test_html_title_attribute_warns_and_class_does_not(self):
        store = self.edited({"Probe page": {"text": '<span class="vtw-gates" title="family">x</span>'}})
        warnings = self.retired(store, "Probe page")
        self.assertEqual(len(warnings), 1)
        self.assertIn("'family'", warnings[0])

    def test_retired_term_is_an_error(self):
        store = self.edited({"Home": {"caption": "open decisions"}})
        errors, warnings, _ = vtw.lint_tiddlers(store)
        self.assertTrue(any("Home.caption: retired vocabulary" in e for e in errors))
        self.assertFalse(any("retired vocabulary" in w for w in warnings))

    def test_reserved_rule_still_errors_on_the_same_page(self):
        store = self.edited({"Home": {"text": (self.base["Home"].get("text") or "") + " expansion"}})
        errors, _, _ = vtw.lint_tiddlers(store)
        self.assertIn("Home: reserved term in shared page: 'expansion'", errors)


class SourceSnapshot(unittest.TestCase):
    """A verbatim source snapshot (field source_of) is exempt from the vocabulary
    rules because it reproduces the source, and must match the source's hash."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.copy_path = Path(cls.tmp.name) / "workbench.html"
        shutil.copyfile(MAIN, cls.copy_path)
        cls.base = vtw.load_tiddlers(cls.copy_path)
        cls.paper = vtw.LITEPAPER.read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def lint(self, fields, title="$:/vtw/source/SRC-LP20"):
        store = dict(self.base)
        store[title] = dict({"title": title, "type": "text/plain"}, **fields)
        errors, _, _ = vtw.lint_tiddlers(store)
        return [e for e in errors if e.startswith(title)]

    def test_verbatim_paper_is_clean(self):
        self.assertEqual(self.lint({"source_of": "SRC-LP20", "text": self.paper}), [])

    def test_paper_words_would_fail_without_the_exemption(self):
        errors = self.lint({"text": self.paper})
        self.assertTrue(any("retired vocabulary" in e for e in errors))

    def test_changed_text_fails_the_hash(self):
        errors = self.lint({"source_of": "SRC-LP20", "text": self.paper.replace("21 rounds", "22 rounds", 1)})
        self.assertTrue(any("sha256" in e for e in errors))

    def test_line_count_is_checked(self):
        errors = self.lint({"source_of": "SRC-LP20", "text": self.paper + "extra\n"})
        self.assertTrue(any("lines" in e for e in errors))

    def test_unknown_source_record_fails(self):
        errors = self.lint({"source_of": "SRC-NOPE", "text": "x"})
        self.assertTrue(any("source_of must be 'SRC-LP20'" in e for e in errors))

    def test_source_of_is_rejected_outside_the_registered_snapshot(self):
        # Review P4 finding 1: Home, a mechanism or any other page cannot claim the exemption.
        for title in ("Home", "MX-01", "$:/vtw/source/SRC-FAKE"):
            with self.subTest(title=title):
                store = dict(self.base)
                rec = dict(store.get(title, {"title": title}))
                rec.update({"source_of": "SRC-LP20", "text": self.paper, "caption": "expansion scenarios gates"})
                store[title] = rec
                errors, _, _ = vtw.lint_tiddlers(store)
                mine = [e for e in errors if e.startswith(title)]
                self.assertTrue(any("source_of is only allowed" in e for e in mine), mine)
                self.assertTrue(any("reserved term" in e or "retired vocabulary" in e for e in mine), mine)

    def test_snapshot_caption_is_still_checked(self):
        errors = self.lint({"source_of": "SRC-LP20", "text": self.paper, "caption": "expansion scenarios gates"})
        self.assertTrue(any("reserved term" in e for e in errors), errors)
        self.assertTrue(any("caption: retired vocabulary" in e for e in errors), errors)

    def test_snapshot_must_be_plain_text(self):
        errors = self.lint({"source_of": "SRC-LP20", "text": self.paper, "type": "text/vnd.tiddlywiki"})
        self.assertTrue(any("text/plain" in e for e in errors), errors)

    def test_exemption_does_not_cover_other_tiddlers(self):
        store = dict(self.base)
        store["$:/vtw/probe"] = {"title": "$:/vtw/probe", "text": "Two scenarios and a gate."}
        errors, _, _ = vtw.lint_tiddlers(store)
        self.assertTrue(any(e.startswith("$:/vtw/probe") for e in errors))

if __name__ == "__main__":
    unittest.main()


class NewStepFields(unittest.TestCase):
    """Review P4 finding 3: step summary fields are reader text."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.copy_path = Path(cls.tmp.name) / "workbench.html"
        shutil.copyfile(MAIN, cls.copy_path)
        cls.base = vtw.load_tiddlers(cls.copy_path)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_step_summary_fields_are_checked(self):
        for field in ("step_short", "step_purpose", "step_done", "step_remaining"):
            with self.subTest(field=field):
                store = dict(self.base)
                rec = dict(store["M1.2"]); rec[field] = "Two scenarios and a gate."
                store["M1.2"] = rec
                errors, _, _ = vtw.lint_tiddlers(store)
                self.assertTrue(any(e.startswith(f"M1.2.{field}: retired vocabulary") for e in errors), field)
