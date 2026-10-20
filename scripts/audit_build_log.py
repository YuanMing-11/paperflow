#!/usr/bin/env python3
"""Collect TeX build diagnostics. A warning is evidence, not a visual verdict."""
import argparse
import json
from pathlib import Path
import re
import sys

RULES = [
    ("undefined_reference", re.compile(r"Reference .+? undefined", re.I)),
    ("undefined_citation", re.compile(r"Citation .+? undefined", re.I)),
    ("undefined_summary", re.compile(r"There were undefined (references|citations)", re.I)),
    ("duplicate_label", re.compile(r"Label .+? multiply defined|multiply-defined labels", re.I)),
    ("overfull_box", re.compile(r"Overfull \\[hv]box")),
    ("underfull_box", re.compile(r"Underfull \\[hv]box")),
    ("float_too_large", re.compile(r"Float too large|Too many unprocessed floats", re.I)),
    ("missing_glyph", re.compile(r"Missing character:")),
    ("font_substitution", re.compile(r"Font shape .+? undefined|font shapes were not available|defaults substituted", re.I)),
    ("missing_file", re.compile(r"(?:File|I can't find file).+?(?:not found|does not exist)|^No file .+\.(?:bbl|aux)\.", re.I)),
    ("rerun_needed", re.compile(r"Rerun to get|Please \(re\)run|Label\(s\) may have changed", re.I)),
    ("tex_error", re.compile(r"^! ")),
]


def audit(path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    findings = []
    for idx, line in enumerate(lines):
        for rule, pattern in RULES:
            if pattern.search(line):
                findings.append({
                    "rule": rule,
                    "log_line": idx + 1,
                    "text": line,
                    "context": lines[max(0, idx - 1): min(len(lines), idx + 3)],
                    "evidence_type": "build_diagnostic",
                    "review_required": True,
                    "note": ("Inspect the rendered result before treating this as a layout defect."
                             if rule.endswith("_box") else
                             "Resolve using the final build sequence and source; verify the resulting artifact.")
                })
    return {
        "schema_version": "1.0",
        "input": str(path.resolve()),
        "findings": findings,
        "coverage": {
            "tex_diagnostics": "checked",
            "compiler_exit_code": "not_checked",
            "rendered_layout": "not_checked",
            "note": "Only recognized messages are collected. No findings does not prove successful compilation."
        }
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--out", type=Path, help="JSON output file; defaults to stdout")
    args = parser.parse_args()
    try:
        if args.out and (args.out.resolve() == args.log.resolve()
                         or (args.out.exists() and args.log.exists() and args.out.samefile(args.log))):
            parser.error("--out must not overwrite the input log")
        result = audit(args.log)
        text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
    except OSError as exc:
        print(f"Cannot read/write log report: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
