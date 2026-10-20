"""Regression tests for observed failures and content-preservation behavior."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import fitz

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


pdf = module("audit_pdf")
diff = module("compare_reports")
log = module("audit_build_log")


class AuditBehavior(unittest.TestCase):
    def run_pdf(self, lines):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.pdf"
            document = fitz.open()
            page = document.new_page()
            for index, text in enumerate(lines):
                page.insert_text((50, 60 + 70 * index), text, fontsize=11)
            document.save(path)
            document.close()
            return pdf.audit(path, Path(directory) / "out", pdf.load_profile(None), False)

    def test_caption_can_reference_another_figure(self):
        result = self.run_pdf([
            "See Figure 1 for the comparison.",
            "Figure 1. Comparison with Figure 2.",
            "Figure 2. Reference condition."
        ])
        self.assertEqual({c["number"] for c in result["captions"]}, {"1", "2"})
        self.assertEqual([r["number"] for r in result["references"]], ["1"])
        self.assertEqual(result["references"][0]["page_gap"], 0)

    def test_initial_plural_reference_is_not_a_caption(self):
        result = self.run_pdf([
            "Figures 1 and 2 show different responses.",
            "Figure 1. First response.", "Figure 2. Second response."
        ])
        self.assertEqual(len(result["captions"]), 2)
        self.assertEqual([r["number"] for r in result["references"]], ["1", "2"])

    def test_supplementary_table_is_separate_from_main_table(self):
        result = self.run_pdf([
            "Compare Table 1 and Supplementary Table 1.",
            "Table 1. Main sample.", "Supplementary Table 1. Additional sample."
        ])
        self.assertEqual({(c["kind"], c["number"]) for c in result["captions"]},
                         {("table", "1"), ("table", "S1")})
        self.assertEqual({(r["kind"], r["number"]) for r in result["references"]},
                         {("table", "1"), ("table", "S1")})
        self.assertTrue(all(r["selected_caption_id"] for r in result["references"]))

    def test_explicit_panel_mismatch_is_not_silently_matched(self):
        result = self.run_pdf(["Figure 1b shows the control.", "Figure 1a. Treatment only."])
        self.assertEqual(result["references"][0]["panel"], "b")
        self.assertIsNone(result["references"][0]["selected_caption_id"])

    def test_wrapped_caption_reference_stays_in_caption(self):
        result = self.run_pdf([
            "See Figure 1 for the response.",
            "Figure 1. A response compared with\nFigure 2 for further context.",
            "Figure 2. Control response."
        ])
        self.assertEqual(len(result["captions"]), 2)
        self.assertEqual([r["number"] for r in result["references"]], ["1"])
        self.assertIn("Figure 2 for further context", result["captions"][0]["text"])

    def test_preservation_diff_exposes_qualifier_and_number_changes(self):
        before = {"pages": [{"text_lines": [{"text": "Only 1.4 units were observed."}]}]}
        after = {"pages": [{"text_lines": [{"text": "2.4 units were observed."}]}]}
        result = diff.compare(before, after)
        removed = {entry["token"] for entry in result["text_token_diff"]["removed"]}
        self.assertTrue({"Only", "1.4"}.issubset(removed))
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["coverage"]["scientific_content_preservation"], "not_checked")

    def test_diagnostics_do_not_certify_visible_defects(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "main.log"
            path.write_text(
                "Underfull \\hbox (badness 10000) in paragraph at lines 2--3\n"
                "LaTeX Warning: Reference `fig:absent' on page 2 undefined on input line 14.\n"
                "Missing character: There is no x in font nullfont!\n"
            )
            result = log.audit(path)
            self.assertEqual({f["rule"] for f in result["findings"]},
                             {"underfull_box", "undefined_reference", "missing_glyph"})
            self.assertEqual(result["coverage"]["rendered_layout"], "not_checked")

    def test_hardlink_outputs_cannot_overwrite_helper_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = [
                ("audit_build_log.py", b"Underfull \\hbox warning\n", "main.log"),
                ("compare_reports.py", json.dumps({"schema_version": "1.0", "pages": []}).encode(), "report.json"),
            ]
            for script, content, name in cases:
                source = root / name
                source.write_bytes(content)
                output = root / f"linked-{name}"
                os.link(source, output)
                args = [sys.executable, str(ROOT / "scripts" / script), str(source)]
                if script == "compare_reports.py":
                    args.append(str(source))
                result = subprocess.run(args + ["--out", str(output)], capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(source.read_bytes(), content)

    def test_pdf_output_collision_preserves_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "report.json"
            document = fitz.open()
            document.new_page()
            source.write_bytes(document.tobytes())
            document.close()
            before = source.read_bytes()
            with self.assertRaises(ValueError):
                pdf.audit(source, root, pdf.load_profile(None), False)
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
