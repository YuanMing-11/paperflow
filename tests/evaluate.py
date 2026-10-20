#!/usr/bin/env python3
"""Black-box checks against independent PDF facts; semantic review is not scored.

This reads the auditor's JSON interface, never imports its implementation.
The original gold and fixtures are not modified.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, default=Path(__file__).resolve().parents[1] / "scripts/audit_pdf.py")
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).resolve().parent / "generated")
    parser.add_argument("--out", type=Path, help="Default: FIXTURES/runs")
    parser.add_argument("--end-matter-profile", type=Path)
    args = parser.parse_args()
    out = args.out or args.fixtures / "runs"
    profile = args.end_matter_profile or args.engine.parent.parent / "profiles/end-matter.json"
    gold_path = args.fixtures / "gold.json"
    gold = json.loads(gold_path.read_text())
    evaluation = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "auditor_path": str(args.engine.resolve()),
        "auditor_sha256": sha256(args.engine),
        "gold_sha256": sha256(gold_path),
        "method": "Black-box subprocess runs; immutable fixture observations supply expected values. No implementation import.",
        "interpretation": "Automatic invariant success does not mean the gold's semantic or visual review behaviors passed.",
        "cases": [],
    }

    for case in gold["cases"]:
        case_id = case["id"]
        pdf = args.fixtures / case["file"]
        before = sha256(pdf)
        run_dir = out / case_id
        command = [sys.executable, str(args.engine), str(pdf), "--out", str(run_dir)]
        if case_id == "03_end_matter_exception":
            command.extend(["--profile", str(profile)])
        completed = subprocess.run(command, capture_output=True, text=True)
        result = {
            "case_id": case_id, "fixture_sha256": before,
            "command": command, "exit_code": completed.returncode,
            "automatic_checks": [],
            "manual_review": {
                "status": "not_assessed_by_this_runner",
                "required_behaviors_from_gold": case["expected_review_behavior"],
                "forbidden_claims_from_gold": case["must_not_claim"],
                "note": "A human or agent must inspect renders, contextual intent and the actual final written review."
            }
        }
        evaluation["cases"].append(result)

        def check(name: str, condition: bool, observed=None) -> None:
            result["automatic_checks"].append({
                "check": name, "status": "pass" if condition else "fail", "observed": observed
            })

        check("auditor_completed", completed.returncode == 0, completed.stderr.strip())
        check("input_bytes_unchanged", before == sha256(pdf))
        if completed.returncode:
            continue
        report_path = run_dir / "report.json"
        report = json.loads(report_path.read_text())
        result["report_path"] = str(report_path)
        pages = report["pages"]
        caps = report["captions"]
        refs = report["references"]
        issues = report["issues"]
        coverage = {entry["check"]: entry for entry in report["coverage"]}
        facts = case["observable_facts"]
        check("physical_page_count_matches_gold", report["document"]["page_count"] == facts["pages"], report["document"]["page_count"])
        check("global_status_does_not_claim_pass", report["assessment"]["status"] == "review_required", report["assessment"]["status"])
        check("zero_findings_does_not_imply_pass", report["assessment"]["no_issues_means_pass"] is False)
        check("no_automatic_repairs_claimed", report["assessment"]["automatic_repairs"] == [])
        for name in ("first_substantive_reference", "same_page_reading_distance_and_columns",
                     "figure_bounds_and_graphic_content", "tables_equations_and_typographic_details"):
            check(f"coverage_declares_{name}_unverified",
                  coverage.get(name, {}).get("status") == "not_checked",
                  coverage.get(name, {}).get("status"))

        if case_id == "01_near_vector":
            check("vector_figure_1_caption_found", any(c["kind"] == "figure" and c["number"] == "1" for c in caps))
            check("zero_raster_images_preserved", pages[0]["raster_boxes"] == [])
            check("vector_geometry_preserved", bool(pages[0]["vector_boxes"]))
            check("local_reference_gap_zero", bool(refs) and all(r["page_gap"] == 0 for r in refs))
            check("no_distant_reference_warning", not any(i["rule"] == "reference_caption_page_gap" for i in issues))
        elif case_id in {"02_far_essential", "03_end_matter_exception"}:
            relevant = [r for r in refs if r["kind"] == "figure" and r["number"] == "1" and r["physical_page"] == 1]
            check("far_reference_retained", len(relevant) == 1, len(relevant))
            check("measured_gap_is_three", bool(relevant) and relevant[0]["page_gap"] == 3,
                  relevant[0]["page_gap"] if relevant else None)
            check("caption_is_page_four", any(c["kind"] == "figure" and c["number"] == "1" and c["physical_page"] == 4 for c in caps))
            distant_issues = [i for i in issues if i["rule"] == "reference_caption_page_gap"]
            if case_id == "02_far_essential":
                check("gap_is_flagged_as_review_candidate", bool(distant_issues) and all(i["review_required"] for i in distant_issues))
            else:
                check("declared_end_matter_profile_respected", report["profile"]["float_policy"] == "end_matter")
                check("end_matter_proximity_warning_exempt", not distant_issues)
                check("measured_distance_kept_with_exemption", bool(relevant) and bool(relevant[0]["distance_exemption"]))
        elif case_id == "04_figure_directory":
            check("directory_not_body_reference", not any(r["physical_page"] == 1 for r in refs))
            check("directory_not_extra_caption", not any(c["physical_page"] == 1 for c in caps))
            check("real_caption_and_reference_local", bool(caps) and bool(refs) and
                  all(c["physical_page"] == 3 for c in caps) and
                  all(r["physical_page"] == 3 and r["page_gap"] == 0 for r in refs))
        elif case_id == "05_reference_roles":
            fig_refs = [r for r in refs if r["kind"] == "figure" and r["number"] == "1"]
            check("both_mentions_retained", sorted(r["physical_page"] for r in fig_refs) == [1, 3],
                  sorted(r["physical_page"] for r in fig_refs))
            check("lexical_distances_kept_separate", sorted(r["page_gap"] for r in fig_refs) == [0, 2],
                  sorted(r["page_gap"] for r in fig_refs))
            check("no_claim_of_automatic_substantive_selection",
                  all(g["substantive_reference_id"] is None for g in report["reference_groups"]))
        elif case_id == "06_two_columns":
            check("same_page_gap_zero", bool(refs) and refs[0]["page_gap"] == 0)
            check("no_invented_column_reading_distance", bool(refs) and
                  refs[0]["same_page_geometry"]["reading_order_distance"] is None)
        elif case_id == "07_caption_prose_ambiguity":
            check("one_caption_per_distinct_object_kind",
                  sorted((c["kind"], c["number"]) for c in caps) == [("figure", "1"), ("table", "1")],
                  [(c["kind"], c["number"]) for c in caps])
            check("sentence_beginning_figure_is_body_reference",
                  any(r["kind"] == "figure" and "Figure 1 shows" in r["context"] for r in refs))
            check("figure_and_table_reference_identities_separate",
                  sorted((r["kind"], r["number"]) for r in refs) == [("figure", "1"), ("table", "1")])
        elif case_id == "08_supplementary_panels":
            check("supplementary_identity_preserved",
                  len(caps) == 1 and caps[0]["number"] == "S1", [c["number"] for c in caps])
            check("both_panel_references_retained",
                  sorted((r["number"], r["panel"]) for r in refs) == [("S1", "a"), ("S1", "b")],
                  [(r["number"], r["panel"]) for r in refs])
            check("panel_refs_resolve_to_shared_figure",
                  len(refs) == 2 and len({r["selected_caption_id"] for r in refs}) == 1
                  and refs[0]["selected_caption_id"] is not None)
        elif case_id == "09_typography_and_blank":
            small = [i for i in issues if i["rule"] == "small_text_candidate"]
            check("tiny_body_flagged", any(i["page"] == 2 for i in small))
            check("normal_footnote_not_flagged_as_tiny_body", not any(i["page"] == 1 for i in small))
            check("off_crop_geometry_flagged_for_visual_review",
                  sum(i["rule"] == "text_bbox_outside_page" and i["page"] == 2 for i in issues) >= 2)
            blank = pages[2]
            check("intentional_blank_page_recorded_as_empty",
                  not blank["text_available"] and not blank["raster_boxes"] and not blank["vector_boxes"]
                  and blank["occupied_bbox_fraction"] == 0)
            result["manual_review"]["specific_unscored_observations"] = [
                "Overlapping body baselines on page 2 need visual confirmation; this runner does not infer an automatic pass.",
                "Page 3's spread-opening exception is declared on page 4; only an agent/human semantic review applies it."
            ]
        elif case_id == "10_image_only":
            check("text_unavailable_recorded", pages[0]["text_available"] is False)
            text_coverage = coverage.get("text_spans_and_page_geometry", {})
            check("unsearchable_page_explicit_in_coverage",
                  text_coverage.get("pages_without_searchable_text") == [1])
            check("visible_image_recorded", bool(pages[0]["raster_boxes"]))
            result["manual_review"]["specific_unscored_observations"] = [
                "A visible figure and body reference exist; an empty parsed list does not establish their absence.",
                "OCR/visual inspection, font readability and semantic proximity are still required."
            ]

    checks = [c for case in evaluation["cases"] for c in case["automatic_checks"]]
    evaluation["summary"] = {
        "cases_run": len(evaluation["cases"]),
        "automatic_invariants": len(checks),
        "automatic_invariants_passed": sum(c["status"] == "pass" for c in checks),
        "automatic_invariants_failed": sum(c["status"] == "fail" for c in checks),
        "semantic_or_visual_gold_behaviors_scored": 0,
        "cases_requiring_manual_review": len(evaluation["cases"]),
        "production_accuracy_established": False,
    }
    output_path = args.fixtures / "evaluation.json"
    output_path.write_text(json.dumps(evaluation, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(output_path), **evaluation["summary"]}))
    if evaluation["summary"]["automatic_invariants_failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
