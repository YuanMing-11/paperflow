#!/usr/bin/env python3
"""Verify layout-only edits against the preserved baseline and final PDF."""
import ast
from collections import Counter
from hashlib import sha256
import difflib
import json
from pathlib import Path
import re

import fitz

ROOT = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def source_inventory(path):
    tree = ast.parse(path.read_text())
    chart = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "chart")
    paragraphs = [
        ast.literal_eval(n.args[0])
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Paragraph"
    ]
    return ast.dump(chart, include_attributes=False), paragraphs


def vector_inventory(document):
    drawings = [d for page in document for d in page.get_drawings()]
    points = [
        p
        for drawing in drawings
        for item in drawing["items"]
        for p in item[1:]
        if isinstance(p, fitz.Point)
    ]
    origin = (min(p.x for p in points), min(p.y for p in points))
    normalized = []
    for drawing in drawings:
        items = []
        for item in drawing["items"]:
            assert item[0] == "l", "Unexpected non-line primitive; inspect manually."
            items.append([
                item[0],
                *[[round(p.x - origin[0], 4), round(p.y - origin[1], 4)] for p in item[1:]],
            ])
        normalized.append({
            "items": items,
            "color": drawing["color"],
            "width": drawing["width"],
            "stroke_opacity": drawing["stroke_opacity"],
        })
    return normalized, origin


def font_inventory(document):
    return Counter(
        (span["text"], span["font"], round(span["size"], 3))
        for page in document
        for block in page.get_text("dict")["blocks"]
        if "lines" in block
        for line in block["lines"]
        for span in line["spans"]
    )


before_source = ROOT / "source-before.py"
after_source = ROOT / "source.py"
before_pdf = fitz.open(ROOT / "before.pdf")
after_pdf = fitz.open(ROOT / "after.pdf")
before_chart, before_paragraphs = source_inventory(before_source)
after_chart, after_paragraphs = source_inventory(after_source)
before_text = normalize(" ".join(page.get_text() for page in before_pdf))
after_text = normalize(" ".join(page.get_text() for page in after_pdf))
before_vectors, before_origin = vector_inventory(before_pdf)
after_vectors, after_origin = vector_inventory(after_pdf)

checks = {
    "paragraph_strings_exactly_preserved": Counter(before_paragraphs) == Counter(after_paragraphs),
    "paragraph_text_present_in_both_pdfs": all(
        normalize(p) in before_text and normalize(p) in after_text for p in before_paragraphs
    ),
    "chart_function_ast_identical": before_chart == after_chart,
    "pdf_vectors_identical_up_to_translation": before_vectors == after_vectors,
    "pdf_text_spans_and_font_sizes_identical": font_inventory(before_pdf) == font_inventory(after_pdf),
    "pdf_text_token_multiset_identical": Counter(before_text.split()) == Counter(after_text.split()),
    "page_dimensions_unchanged": all(tuple(p.rect) == (0, 0, 612, 792) for p in [*before_pdf, *after_pdf]),
}
result = {
    "checks": checks,
    "all_automated_preservation_checks_pass": all(checks.values()),
    "paragraph_count": len(before_paragraphs),
    "vector_path_count": len(before_vectors),
    "vector_translation_pt": [after_origin[i] - before_origin[i] for i in range(2)],
    "page_count": {"before": len(before_pdf), "after": len(after_pdf)},
    "hashes_sha256": {
        name: digest(ROOT / name) for name in ["before.pdf", "after.pdf", "source-before.py", "source.py"]
    },
    "limits": [
        "Automated comparisons do not replace rendered-page inspection.",
        "The paragraph order changes because the complete figure/caption block moves.",
        "No independent scientific-claim or accessibility-conformance assessment.",
    ],
}
(ROOT / "verification.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
(ROOT / "source.diff").write_text("".join(difflib.unified_diff(
    before_source.read_text().splitlines(True),
    after_source.read_text().splitlines(True),
    fromfile="source-before.py",
    tofile="source.py",
)))
print(json.dumps(result, indent=2, ensure_ascii=False))
assert all(checks.values()), "Content preservation check failed."
