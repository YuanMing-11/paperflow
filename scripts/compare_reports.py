#!/usr/bin/env python3
"""Triage before/after PDF evidence; never certifies visual or semantic equality."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import unicodedata


def text_tokens(report):
    pieces = []
    for page in report.get("pages", []):
        for line in page.get("text_lines", []):
            # Suppress known running furniture; unknown/page-specific numbering
            # can still cause a difference and must be reviewed.
            if line.get("is_running_matter") or line.get("role") in {
                "running_matter", "header", "footer", "repeated_header_or_footer_candidate"
            }:
                continue
            pieces.append(line.get("text", ""))
    text = unicodedata.normalize("NFKC", "\n".join(pieces))
    # Collapse line-break hyphenation only between letters, not numeric minus signs.
    text = re.sub(r"([^\W\d_])-\s*\n\s*([^\W\d_])", r"\1\2", text)
    tokens = re.findall(r"[+-]?\d+(?:[.,]\d+)*(?:[eE][+-]?\d+)?|[^\W\d_]+|[%±≤≥<>]", text)
    return Counter(tokens)


def compact(counter):
    return [{"token": word, "count": count} for word, count in sorted(counter.items())]


def load_report(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema_version") != "1.0" or not isinstance(value.get("pages"), list):
        raise ValueError(f"Not an audit_pdf schema 1.0 report: {path}")
    return value


def compare(before, after):
    old_rules = Counter(x["rule"] for x in before.get("issues", []))
    new_rules = Counter(x["rule"] for x in after.get("issues", []))
    old_tokens, new_tokens = text_tokens(before), text_tokens(after)
    return {
        "schema_version": "1.0",
        "status": "review_required",
        "profiles_equal": before.get("profile") == after.get("profile"),
        "page_count": {"before": len(before["pages"]), "after": len(after["pages"])},
        "candidate_count_by_rule": [
            {"rule": rule, "before": old_rules[rule], "after": new_rules[rule]}
            for rule in sorted(old_rules.keys() | new_rules.keys())
        ],
        "text_token_diff": {
            "removed": compact(old_tokens - new_tokens),
            "added": compact(new_tokens - old_tokens),
            "available": bool(old_tokens) and bool(new_tokens),
            "note": "Token counts disregard order and cannot prove meaning preservation. OCR, ligatures, page numbers and line wrapping can create false differences."
        },
        "reference_distances": {
            side: [
                {key: ref.get(key) for key in ("id", "kind", "number", "panel", "physical_page", "context", "page_gap", "signed_page_delta", "selected_caption_id")}
                for ref in value.get("references", [])
            ] for side, value in (("before", before), ("after", after))
        },
        "coverage": {
            "candidate_and_token_comparison": "checked",
            "pixel_comparison": "not_checked",
            "scientific_content_preservation": "not_checked",
            "visual_regressions": "not_checked",
            "note": "A lower issue count is not proof of improvement. Inspect matched objects, all affected mentions and changed pages with neighbors."
        }
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        if args.out and any(
            args.out.resolve() == source.resolve()
            or (args.out.exists() and source.exists() and args.out.samefile(source))
            for source in (args.before, args.after)
        ):
            parser.error("--out must not overwrite an input report")
        result = compare(load_report(args.before), load_report(args.after))
        text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
    except (OSError, ValueError, KeyError) as exc:
        print(f"Cannot compare reports: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
