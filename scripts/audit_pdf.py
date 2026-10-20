#!/usr/bin/env python3
"""Collect local PDF layout evidence; never modify the PDF.

Requires Python 3.10+ and PyMuPDF (``python -m pip install PyMuPDF``).
Usage: python audit_pdf.py manuscript.pdf --out audit --render

This is an evidence collector, not a typography or scientific-accuracy grader.
Text roles and caption/reference matches are candidates requiring review.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import html
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

VERSION = "0.1.0"
SCHEMA_VERSION = "1.0"
DEFAULT_PROFILE = {
    "far_reference_page_gap": 2,
    "float_policy": "inline",
    "minimum_font_pt": 7.0,
    "minimum_body_font_ratio": 0.65,
    "sparse_page_max_occupied_fraction": 0.12,
    "page_edge_tolerance_pt": 0.5,
    "render_dpi": 110,
    "exempt_pages": [],
}

# Deliberately bounded grammar: Arabic section numbers and supplementary S1.
# Roman numbering, OCR repair and cross-line references are not implemented.
NUMBER = r"(?:[Ss]\s*)?\d+(?:\.\d+)*"
PANEL = r"(?:\s*\(([A-Za-z](?:\s*[,–—-]\s*[A-Za-z])*)\)|([A-Za-z])\b)?"
KIND = r"(?P<label>(?:Supplementary\s+)?(?:Figures?|Figs?\.?|Tables?)|图|表)"
MARKER_RE = re.compile(
    rf"(?<![A-Za-z]){KIND}\s*(?P<number>{NUMBER}){PANEL}", re.IGNORECASE
)
ITEM_RE = re.compile(rf"(?P<number>{NUMBER}){PANEL}", re.IGNORECASE)
TAIL_RE = re.compile(
    r"\s*(?P<join>(?:,|，|、)\s*(?:and\b|和|及)?|and\b|&|和|及|to\b|[–—-])\s*", re.I
)
BODY_VERB_RE = re.compile(
    r"^(?:shows?|illustrates?|presents?|demonstrates?|reports?|compares?|"
    r"summarizes?|summarises?|contains?|provides?|depicts?|displays?|"
    r"lists?|indicates?|suggests?|reveals?|is|are|was|were|can|also|"
    r"confirms?|supports?|plots?|describes?|evaluates?|analy[sz]es?)\b|"
    r"^(?:显示|表明|展示|说明|给出|汇总|比较|反映|证明|可见|中|所示|为)",
    re.I,
)
NAV_HEADING_RE = re.compile(
    r"^(?:table of contents|contents|list of (?:figures|tables)|"
    r"figures and tables|目录|目\s*录|插图目录|图目录|表目录|图表目录)\s*$",
    re.I,
)
BIB_HEADING_RE = re.compile(r"^(?:references|bibliography|参考文献)\s*$", re.I)


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reject_source_output_collision(source: Path, targets: list[Path]) -> None:
    """Protect source contents even through output symlinks or hard links."""
    resolved_source = source.resolve()
    for target in targets:
        collision = target.resolve() == resolved_source
        if not collision and target.exists():
            collision = target.samefile(source)
        if collision:
            raise ValueError(f"output would overwrite the input PDF: {target}; choose a different --out directory")


def load_profile(path: Path | None) -> dict:
    profile = {**DEFAULT_PROFILE, "exempt_pages": []}
    if path:
        with path.open(encoding="utf-8") as handle:
            supplied = json.load(handle)
        if not isinstance(supplied, dict):
            raise ValueError("profile must be a JSON object")
        unknown = sorted(set(supplied) - set(profile))
        if unknown:
            raise ValueError("unknown profile key(s): " + ", ".join(unknown))
        profile.update(supplied)
    for key in ("far_reference_page_gap", "render_dpi"):
        if not isinstance(profile[key], int) or isinstance(profile[key], bool):
            raise ValueError(f"{key} must be an integer")
    if profile["far_reference_page_gap"] < 1:
        raise ValueError("far_reference_page_gap must be >= 1")
    if not 72 <= profile["render_dpi"] <= 300:
        raise ValueError("render_dpi must be between 72 and 300")
    if profile["float_policy"] not in ("inline", "end_matter"):
        raise ValueError("float_policy must be 'inline' or 'end_matter'")
    for key in ("minimum_font_pt", "minimum_body_font_ratio",
                "sparse_page_max_occupied_fraction", "page_edge_tolerance_pt"):
        if not finite_number(profile[key]):
            raise ValueError(f"{key} must be a finite number")
    if profile["minimum_font_pt"] <= 0 or profile["page_edge_tolerance_pt"] < 0:
        raise ValueError("minimum_font_pt must be positive; page_edge_tolerance_pt must be >= 0")
    for key in ("minimum_body_font_ratio", "sparse_page_max_occupied_fraction"):
        if not 0 < profile[key] < 1:
            raise ValueError(f"{key} must be strictly between 0 and 1")
    pages = profile["exempt_pages"]
    if not isinstance(pages, list) or any(
        not isinstance(n, int) or isinstance(n, bool) or n < 1 for n in pages
    ):
        raise ValueError("exempt_pages must be an array of positive physical page integers")
    profile["exempt_pages"] = sorted(set(pages))
    return profile


def box(value) -> list[float]:
    return [round(float(v), 3) for v in value]


def merge_boxes(values: list[list[float]]) -> list[float]:
    return [min(v[0] for v in values), min(v[1] for v in values),
            max(v[2] for v in values), max(v[3] for v in values)]


def valid_box(value) -> bool:
    return (len(value) == 4 and all(finite_number(v) for v in value)
            and value[2] >= value[0] and value[3] >= value[1])


def normalize_number(number: str) -> str:
    return re.sub(r"\s+", "", number).upper()


def marker_number(number: str, label: str) -> str:
    number = normalize_number(number)
    if label.lower().startswith("supplementary") and not number.startswith("S"):
        return "S" + number
    return number


def marker_kind(label: str) -> str:
    return "table" if re.search(r"\btables?\b", label, re.I) or label == "表" else "figure"


def panel_from_match(match) -> str | None:
    # The named label in MARKER_RE shifts the unnamed panel group numbers.
    groups = match.groups()
    panels = groups[-2:]
    return next((re.sub(r"\s+", "", value).lower() for value in panels if value), None)


def parse_markers(text: str) -> list[dict]:
    """Return explicit markers, lists and bounded integer ranges from one line."""
    result = []
    consumed_until = -1
    for match in MARKER_RE.finditer(text):
        if match.start() < consumed_until:
            continue
        kind = marker_kind(match.group("label"))
        base = {
            "kind": kind, "number": marker_number(match.group("number"), match.group("label")),
            "panel": panel_from_match(match), "start": match.start(), "end": match.end(),
            "syntax": "explicit",
        }
        group = [base]
        cursor = match.end()
        while True:
            join = TAIL_RE.match(text, cursor)
            if not join:
                break
            item = ITEM_RE.match(text, join.end())
            if not item:
                break
            entry = {
                "kind": kind, "number": marker_number(item.group("number"), match.group("label")),
                "panel": panel_from_match(item), "start": match.start(), "end": item.end(),
                "syntax": "list_item",
            }
            if join.group("join").lower() in ("-", "–", "—", "to"):
                left = re.fullmatch(r"(S?)(\d+)", group[-1]["number"])
                right = re.fullmatch(r"(S?)(\d+)", entry["number"])
                if left and right and left[1] == right[1] and not group[-1]["panel"] and not entry["panel"]:
                    first, last = int(left[2]), int(right[2])
                    if 1 < last - first <= 20:
                        for n in range(first + 1, last):
                            group.append({**entry, "number": f"{left[1]}{n}",
                                          "syntax": "range_expanded"})
                    elif last - first > 20 or last <= first:
                        entry["syntax"] = "range_endpoint_only"
                else:
                    entry["syntax"] = "range_endpoint_only"
            group.append(entry)
            cursor = item.end()
        consumed_until = cursor
        for entry in group:
            entry["matched_text"] = text[entry["start"]:cursor]
        result.extend(group)
    return result


def bbox_occupancy(rectangles: list[list[float]], width: float, height: float) -> float:
    """Approximate bbox union on a 100x100 grid; not measured ink or whitespace."""
    cells = set()
    for rect in rectangles:
        if not valid_box(rect):
            continue
        x0, y0, x1, y1 = rect
        if x1 <= 0 or y1 <= 0 or x0 >= width or y0 >= height:
            continue
        xa = max(0, min(99, int(100 * x0 / width)))
        xb = max(0, min(99, math.ceil(100 * x1 / width) - 1))
        ya = max(0, min(99, int(100 * y0 / height)))
        yb = max(0, min(99, math.ceil(100 * y1 / height) - 1))
        cells.update((x, y) for x in range(xa, xb + 1) for y in range(ya, yb + 1))
    return round(len(cells) / 10000, 4)


def normalize_recurring(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip()).lower()
    if re.fullmatch(r"(?:page\s*)?\d+(?:\s*/\s*\d+)?", text):
        return "<page-number>"
    return text


def extract_pages(document) -> list[dict]:
    pages = []
    for page_index, page in enumerate(document):
        # All coordinates are PDF points in the unrotated page coordinate system,
        # matching get_text/get_drawings. The rotated render may look different.
        bounds = page.rect * page.derotation_matrix
        bounds = box(bounds)
        width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
        lines = []
        try:
            text_dict = page.get_text(
                "dict", flags=0, sort=False,
                clip=(-2147483648.0, -2147483648.0, 2147483520.0, 2147483520.0),
            )
        except Exception as error:
            raise ValueError(f"text extraction failed on physical page {page_index + 1}: {error}") from error
        for block_index, block in enumerate(text_dict.get("blocks", [])):
            if block.get("type", 0) != 0:
                continue
            for line_index, line in enumerate(block.get("lines", [])):
                spans = []
                for span in line.get("spans", []):
                    spans.append({
                        "text": span.get("text", ""),
                        "bbox": box(span["bbox"]),
                        "font": span.get("font", ""),
                        "font_size_pt": round(float(span.get("size", 0)), 3),
                        "flags": span.get("flags", 0),
                    })
                text = "".join(span["text"] for span in spans).strip()
                if not text:
                    continue
                lines.append({
                    "id": f"p{page_index + 1}-b{block_index}-l{line_index}",
                    "block_index": block_index, "line_index": line_index,
                    "extraction_index": len(lines), "text": text,
                    "bbox": box(line["bbox"]), "spans": spans,
                    "direction": list(line.get("dir", (1, 0))),
                    "role": "body_candidate",
                })
        raster_boxes, vector_boxes = [], []
        extraction_notes = []
        try:
            raster_boxes = [box(info["bbox"]) for info in page.get_image_info()]
        except Exception as error:
            extraction_notes.append(f"Raster geometry unavailable: {type(error).__name__}")
        try:
            vector_boxes = [box(drawing["rect"]) for drawing in page.get_drawings()]
        except Exception as error:
            extraction_notes.append(f"Vector geometry unavailable: {type(error).__name__}")
        graphics = raster_boxes + vector_boxes
        occupancy_boxes = [line["bbox"] for line in lines] + graphics
        try:
            page_label = page.get_label() or str(page_index + 1)
        except Exception:
            page_label = str(page_index + 1)
        character_count = sum(len(line["text"]) for line in lines)
        pages.append({
            "physical_page": page_index + 1, "page_label": page_label,
            "width_pt": round(width, 3), "height_pt": round(height, 3),
            "page_bbox": bounds, "rotation_degrees": page.rotation,
            "text_available": bool(character_count),
            "text_status": "searchable_text_present" if character_count else "no_searchable_text",
            "character_count": character_count, "text_lines": lines,
            "raster_boxes": raster_boxes, "vector_boxes": vector_boxes,
            "occupied_bbox_fraction": bbox_occupancy(occupancy_boxes, width, height),
            "occupancy_method": "100x100 grid union of extracted text, raster and vector bounding boxes; not ink density",
            "extraction_notes": extraction_notes, "page_role": "content_candidate",
        })
    return pages


def assign_page_roles(pages: list[dict]) -> None:
    occurrences = collections.defaultdict(set)
    for page in pages:
        height = page["height_pt"]
        for line in page["text_lines"]:
            if line["bbox"][1] < 0.10 * height or line["bbox"][3] > 0.90 * height:
                key = normalize_recurring(line["text"])
                if key:
                    occurrences[key].add(page["physical_page"])
    threshold = max(2, math.ceil(len(pages) * 0.5))
    recurring = {key for key, seen in occurrences.items() if len(seen) >= threshold}
    for page in pages:
        height = page["height_pt"]
        for line in page["text_lines"]:
            near_edge = line["bbox"][1] < 0.10 * height or line["bbox"][3] > 0.90 * height
            if near_edge and normalize_recurring(line["text"]) in recurring:
                line["role"] = "repeated_header_or_footer_candidate"
        top_lines = sorted(page["text_lines"], key=lambda line: (line["bbox"][1], line["bbox"][0]))
        for line in top_lines[:12]:
            if line["bbox"][1] > height * 0.45:
                continue
            if NAV_HEADING_RE.fullmatch(line["text"].strip()):
                page["page_role"] = "navigation_candidate"
                page["role_evidence"] = line["text"]
                for other in page["text_lines"]:
                    if other["role"] == "body_candidate":
                        other["role"] = "navigation_candidate"
                break
        if page["page_role"] == "content_candidate":
            for line in top_lines[:6]:
                if BIB_HEADING_RE.fullmatch(line["text"].strip()) and line["bbox"][1] < height * 0.35:
                    page["page_role"] = "bibliography_candidate"
                    page["role_evidence"] = line["text"]
                    for other in page["text_lines"]:
                        if other["role"] == "body_candidate":
                            other["role"] = "bibliography_candidate"
                    break


def near_visual(line_box: list[float], page: dict) -> bool:
    x0, y0, x1, y1 = line_box
    for graphic in page["raster_boxes"] + page["vector_boxes"]:
        gx0, gy0, gx1, gy1 = graphic
        if gx1 - gx0 < 20 or gy1 - gy0 < 2:
            continue
        overlap = max(0, min(x1, gx1) - max(x0, gx0))
        if overlap < 0.25 * max(1, min(x1 - x0, gx1 - gx0)):
            continue
        vertical_gap = max(y0 - gy1, gy0 - y1, 0)
        if vertical_gap <= 45:
            return True
    return False


def detect_captions(pages: list[dict]) -> list[dict]:
    captions = []
    for page in pages:
        for line in page["text_lines"]:
            if line["role"] != "body_candidate":
                continue
            match = MARKER_RE.match(line["text"])
            if not match:
                continue
            tail = line["text"][match.end():].lstrip()
            if BODY_VERB_RE.match(tail):
                continue
            # Lists of references at the beginning of prose are not captions.
            if sum(marker["start"] == match.start() for marker in parse_markers(line["text"])) > 1:
                continue
            if re.search(r"\.{3,}\s*\d+\s*$", line["text"]):
                line["role"] = "navigation_entry_candidate"
                continue
            separator = bool(re.match(r"^[.:：|｜—–]", tail))
            near_graphic = near_visual(line["bbox"], page)
            font_bold = any(span["flags"] & 16 for span in line["spans"])
            confidence = 0.50 + 0.24 * separator + 0.12 * near_graphic + 0.06 * font_bold
            if not tail:
                confidence -= 0.06
            confidence = round(min(0.94, confidence), 2)
            status = "probable_caption" if confidence >= 0.70 else "possible_caption"
            caption_lines = [line]
            # Only probable captions claim continuation lines. Low-confidence
            # candidates remain eligible as body references (dual interpretation).
            if status == "probable_caption":
                previous = line
                for other in page["text_lines"][line["extraction_index"] + 1:]:
                    if len(caption_lines) >= 12 or other["block_index"] != line["block_index"]:
                        break
                    gap = other["bbox"][1] - previous["bbox"][3]
                    height = max(1, previous["bbox"][3] - previous["bbox"][1])
                    if gap > height or gap < -height * 0.5:
                        break
                    if abs(other["bbox"][0] - line["bbox"][0]) > 24:
                        break
                    if other["role"] != "body_candidate":
                        break
                    next_marker = MARKER_RE.match(other["text"])
                    if next_marker:
                        next_tail = other["text"][next_marker.end():].lstrip()
                        # Captions can refer to another figure at the start of
                        # a wrapped line. A marker alone is not a new caption.
                        if re.match(r"^[.:：|｜—–]", next_tail):
                            break
                    if other["bbox"][3] - line["bbox"][1] > 160:
                        break
                    caption_lines.append(other)
                    previous = other
            caption_id = f"cap-{len(captions) + 1:04d}"
            for item in caption_lines:
                item.setdefault("caption_candidate_ids", []).append(caption_id)
                if status == "probable_caption":
                    item["role"] = "caption_candidate"
            captions.append({
                "id": caption_id, "kind": marker_kind(match.group("label")),
                "number": marker_number(match.group("number"), match.group("label")),
                "panel": panel_from_match(match),
                "physical_page": page["physical_page"], "page_label": page["page_label"],
                "bbox": merge_boxes([item["bbox"] for item in caption_lines]),
                "text": " ".join(item["text"] for item in caption_lines),
                "line_ids": [item["id"] for item in caption_lines],
                "confidence": confidence, "status": status,
                "evidence": {"numbered_line_start": True, "caption_separator": separator,
                             "near_graphic_primitive": near_graphic, "bold_span_present": font_bold},
                "figure_bounds": None,
                "review_required": True,
            })
    return captions


def reference_context(line: dict, page: dict) -> str:
    same_block = [other["text"] for other in page["text_lines"]
                  if other["block_index"] == line["block_index"]
                  and abs(other["line_index"] - line["line_index"]) <= 1]
    return " ".join(same_block)[:800]


def match_references(pages: list[dict], captions: list[dict]) -> list[dict]:
    lookup = collections.defaultdict(list)
    for caption in captions:
        lookup[(caption["kind"], caption["number"])].append(caption)
    references = []
    for page in pages:
        for line in page["text_lines"]:
            if line["role"] != "body_candidate":
                continue
            for marker in parse_markers(line["text"]):
                candidates = lookup[(marker["kind"], marker["number"])]
                # Do not match a possible caption's marker back to itself.
                candidates = [candidate for candidate in candidates if line["id"] not in candidate["line_ids"]]
                if marker["panel"]:
                    compatible = [candidate for candidate in candidates
                                  if not candidate["panel"] or candidate["panel"] == marker["panel"]]
                    candidates = compatible
                candidates = sorted(candidates, key=lambda candidate: (-candidate["confidence"],
                                    candidate["physical_page"], candidate["id"]))
                selected = candidates[0] if len(candidates) == 1 else None
                distances = [{
                    "caption_id": candidate["id"],
                    "caption_physical_page": candidate["physical_page"],
                    "page_gap": abs(candidate["physical_page"] - page["physical_page"]),
                    "signed_page_delta": candidate["physical_page"] - page["physical_page"],
                } for candidate in candidates]
                same_page_geometry = None
                if selected and selected["physical_page"] == page["physical_page"]:
                    lb, cb = line["bbox"], selected["bbox"]
                    same_page_geometry = {
                        "reference_line_bbox": lb, "caption_bbox": cb,
                        "caption_minus_reference_center_x_pt": round((cb[0] + cb[2] - lb[0] - lb[2]) / 2, 3),
                        "caption_minus_reference_center_y_pt": round((cb[1] + cb[3] - lb[1] - lb[3]) / 2, 3),
                        "reading_order_distance": None,
                        "limitation": "Caption geometry only; column order, viewport and full figure bounds are unverified.",
                    }
                references.append({
                    "id": f"ref-{len(references) + 1:04d}",
                    "kind": marker["kind"], "number": marker["number"], "panel": marker["panel"],
                    "syntax": marker["syntax"], "matched_text": marker["matched_text"],
                    "physical_page": page["physical_page"], "page_label": page["page_label"],
                    "line_id": line["id"], "bbox": line["bbox"],
                    "bbox_scope": "containing_text_line",
                    "line_text": line["text"], "context": reference_context(line, page),
                    "candidate_caption_ids": [candidate["id"] for candidate in candidates],
                    "selected_caption_id": selected["id"] if selected else None,
                    "match_status": "unambiguous_candidate" if selected else (
                        "ambiguous_candidates" if candidates else "unresolved_candidate"),
                    "candidate_distances": distances,
                    "page_gap": distances[0]["page_gap"] if selected else None,
                    "signed_page_delta": distances[0]["signed_page_delta"] if selected else None,
                    "same_page_geometry": same_page_geometry,
                    "source_role_ambiguity": "possible_caption_or_body_reference"
                        if line.get("caption_candidate_ids") else None,
                    "semantic_importance": "not_assessed",
                    "review_required": True,
                })
    return references


def estimate_body_font(pages: list[dict]) -> float | None:
    sizes = collections.Counter()
    for page in pages:
        for line in page["text_lines"]:
            if line["role"] != "body_candidate":
                continue
            for span in line["spans"]:
                size = span["font_size_pt"]
                weight = len(re.sub(r"\s+", "", span["text"]))
                if 4 <= size <= 40 and weight > 1:
                    sizes[round(size * 4) / 4] += weight
    return sizes.most_common(1)[0][0] if sizes else None


def summarize_groups(references: list[dict], captions: list[dict]) -> list[dict]:
    refs_by_key, caps_by_key = collections.defaultdict(list), collections.defaultdict(list)
    for reference in references:
        refs_by_key[(reference["kind"], reference["number"])].append(reference)
    for caption in captions:
        caps_by_key[(caption["kind"], caption["number"])].append(caption)
    groups = []
    for kind, number in sorted(set(refs_by_key) | set(caps_by_key)):
        refs = refs_by_key[(kind, number)]
        first = refs[0] if refs else None
        groups.append({
            "kind": kind, "number": number,
            "caption_candidate_ids": [caption["id"] for caption in caps_by_key[(kind, number)]],
            "body_reference_ids": [reference["id"] for reference in refs],
            "first_reference_id": first["id"] if first else None,
            "first_reference_page_gap": first["page_gap"] if first else None,
            "first_reference_candidate_distances": first["candidate_distances"] if first else [],
            "first_reference_basis": "Earliest physical page, then native PDF extraction order; not first substantive discussion.",
            "substantive_reference_id": None,
        })
    return groups


def build_issues(pages: list[dict], captions: list[dict], references: list[dict],
                 profile: dict, body_font: float | None) -> list[dict]:
    issues = []
    by_page = {page["physical_page"]: page for page in pages}

    def add(rule, page, bbox, evidence, confidence, severity="warning", category="heuristic",
            exemption=None):
        issues.append({
            "id": f"issue-{len(issues) + 1:04d}", "rule": rule, "severity": severity,
            "page": page, "page_label": by_page[page]["page_label"], "bbox": bbox,
            "evidence": evidence, "confidence": confidence, "category": category,
            "review_required": True, "exemption": exemption,
        })

    for reference in references:
        page = reference["physical_page"]
        if reference["match_status"] == "unresolved_candidate":
            add("unresolved_reference_candidate", page, reference["bbox"], {
                "reference_id": reference["id"], "context": reference["context"],
                "kind": reference["kind"], "number": reference["number"],
                "interpretation": "No caption candidate was extracted. This does not establish a missing figure/table.",
            }, 0.45, "info")
        elif reference["match_status"] == "ambiguous_candidates":
            add("ambiguous_reference_match", page, reference["bbox"], {
                "reference_id": reference["id"],
                "candidate_caption_ids": reference["candidate_caption_ids"],
                "candidate_distances": reference["candidate_distances"],
            }, 0.50, "info")
        if reference["page_gap"] is not None and reference["page_gap"] >= profile["far_reference_page_gap"]:
            exemption = None
            if profile["float_policy"] == "end_matter":
                exemption = "float_policy=end_matter; distance retained, proximity warning exempt"
            elif page in profile["exempt_pages"]:
                exemption = "reference page listed in exempt_pages; distance retained"
            reference["distance_exemption"] = exemption
            reference["distance_threshold_triggered"] = True
            if not exemption:
                add("reference_caption_page_gap", page, reference["bbox"], {
                    "reference_id": reference["id"], "caption_id": reference["selected_caption_id"],
                    "page_gap": reference["page_gap"], "signed_page_delta": reference["signed_page_delta"],
                    "threshold": profile["far_reference_page_gap"], "context": reference["context"],
                    "interpretation": "Page gap to a caption candidate; reading effort and substantive relevance require visual review.",
                }, 0.65)
        else:
            reference["distance_exemption"] = None
            reference["distance_threshold_triggered"] = False
    for page in pages:
        number = page["physical_page"]
        exempt = number in profile["exempt_pages"]
        page["heuristic_exemption"] = "listed in profile.exempt_pages" if exempt else None
        width, height = page["width_pt"], page["height_pt"]
        tolerance = profile["page_edge_tolerance_pt"]
        for line in page["text_lines"]:
            outside = [span for span in line["spans"]
                       if span["text"].strip() and (
                           span["bbox"][0] < -tolerance or span["bbox"][1] < -tolerance
                           or span["bbox"][2] > width + tolerance
                           or span["bbox"][3] > height + tolerance)]
            if outside:
                add("text_bbox_outside_page", number, merge_boxes([span["bbox"] for span in outside]), {
                    "text": line["text"], "span_boxes": [span["bbox"] for span in outside],
                    "page_bbox": page["page_bbox"], "tolerance_pt": tolerance,
                    "interpretation": "Extracted text geometry crosses the page boundary; visible clipping must be verified.",
                }, 0.95, category="geometric_evidence")
            if exempt or line["role"] in ("repeated_header_or_footer_candidate", "navigation_candidate"):
                continue
            small = []
            for span in line["spans"]:
                if len(span["text"].strip()) < 2 or span["font_size_pt"] <= 0:
                    continue
                absolute = span["font_size_pt"] < profile["minimum_font_pt"]
                relative = body_font is not None and span["font_size_pt"] < (
                    body_font * profile["minimum_body_font_ratio"])
                if absolute or relative:
                    small.append({**span, "below_absolute_threshold": absolute,
                                  "below_body_relative_threshold": relative})
            if small:
                add("small_text_candidate", number, merge_boxes([span["bbox"] for span in small]), {
                    "line_text": line["text"], "spans": small, "body_font_estimate_pt": body_font,
                    "absolute_threshold_pt": profile["minimum_font_pt"],
                    "body_relative_ratio": profile["minimum_body_font_ratio"],
                    "interpretation": "PDF point sizes are evidence; superscripts, footnotes and venue rules may justify them.",
                }, 0.65)
        # Do not imply that absence of searchable text is a blank page.
        internal = 1 < number < len(pages)
        if (not exempt and internal and page["text_available"]
                and page["page_role"] == "content_candidate"
                and not page["extraction_notes"]
                and page["occupied_bbox_fraction"] < profile["sparse_page_max_occupied_fraction"]):
            add("sparse_page_candidate", number, None, {
                "occupied_bbox_fraction": page["occupied_bbox_fraction"],
                "threshold": profile["sparse_page_max_occupied_fraction"],
                "method": page["occupancy_method"],
                "interpretation": "Sparse extracted bounding boxes on an internal page; chapter breaks or design choices may justify this.",
            }, 0.40, "info")
    return issues


def build_coverage(pages: list[dict]) -> list[dict]:
    text_pages = [page["physical_page"] for page in pages if page["text_available"]]
    unavailable = [page["physical_page"] for page in pages if not page["text_available"]]
    has_text = bool(text_pages)
    return [
        {"check": "text_spans_and_page_geometry", "status": "automatic_evidence" if has_text else "unavailable",
         "pages_with_searchable_text": text_pages, "pages_without_searchable_text": unavailable,
         "limitations": "No OCR. Hidden OCR text, crop boxes, rotation and extraction quirks require visual confirmation."},
        {"check": "caption_reference_candidates_and_page_gap", "status": "heuristic" if has_text else "unavailable",
         "limitations": "English/Chinese Figure/Fig./Table/图/表, Arabic and S numbers; simple lists and bounded integer ranges. Roman numerals, cross-line labels and long/complex ranges are not fully parsed. Navigation and repeated-edge exclusions are heuristic. All matches require review."},
        {"check": "font_size_candidates", "status": "heuristic" if has_text else "unavailable",
         "limitations": "Extracted font sizes and a character-weighted modal body-font estimate; not visual legibility. Text baked into images is unavailable."},
        {"check": "text_boundary_geometry", "status": "automatic_evidence" if has_text else "unavailable",
         "limitations": "Evidence of extracted span geometry outside the page only; internal margins, clipping paths and hidden text are not judged."},
        {"check": "sparse_page_candidate", "status": "heuristic" if has_text else "unavailable",
         "limitations": "Approximate bbox occupancy, including vector primitives and raster images. Not actual white-space/ink measurement. Cover/final pages are not flagged."},
        {"check": "first_substantive_reference", "status": "not_checked",
         "limitations": "Earliest extracted mention is provided; substantive discussion must be identified by an agent or reviewer."},
        {"check": "same_page_reading_distance_and_columns", "status": "not_checked",
         "limitations": "Only reference-line/caption coordinates are recorded. No validated reading-order, spread, screen or column-distance score."},
        {"check": "figure_bounds_and_graphic_content", "status": "not_checked",
         "limitations": "Primitive boxes do not reconstruct figures. Plot labels, legends, units, panels, colour/contrast, missing data and caption consistency need rendered visual/source review."},
        {"check": "tables_equations_and_typographic_details", "status": "not_checked",
         "limitations": "Table splits, equation wrapping/number collisions, widow/orphan lines, hyphenation, spacing and heading hierarchy need visual/source review."},
        {"check": "links_accessibility_and_scientific_correctness", "status": "not_checked",
         "limitations": "No link-target audit, PDF tagging, alt-text validation, reading-order accessibility test or scientific-claim verification."},
    ]


def write_html(report: dict, out: Path) -> None:
    esc = lambda value: html.escape(str(value), quote=True)
    page_count = report["document"]["page_count"]
    chunks = ["""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PDF layout evidence</title><style>
body{font:15px/1.55 system-ui,sans-serif;max-width:1120px;margin:32px auto;padding:0 20px;color:#18222c}
h1,h2,h3{line-height:1.25}a{color:#155da8}table{border-collapse:collapse;width:100%;margin:16px 0}
th,td{border:1px solid #d8e0e7;padding:8px;text-align:left;vertical-align:top;overflow-wrap:anywhere}
th{background:#edf2f6}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f7;padding:12px}
.notice{padding:14px;background:#fff6d9;border-left:4px solid #be9000}.muted{color:#52616d}
.issue{border:1px solid #d9e0e6;border-radius:7px;padding:14px;margin:12px 0}
.page-image{display:block;max-width:100%;max-height:1000px;border:1px solid #d9e0e6}
.badge{background:#edf2f6;padding:2px 7px;border-radius:4px;font-size:12px}summary{cursor:pointer}
</style><h1>PDF layout evidence</h1>"""]
    chunks.append(f"<p><strong>{esc(report['document']['filename'])}</strong> · {page_count} physical pages · "
                  f"{len(report['issues'])} review candidates</p>")
    chunks.append('<p class="notice">This report does not certify readability or publication readiness. '
                  'Caption matches, page-gap warnings and font/sparsity thresholds are candidates. '
                  'Unchecked features and pages without searchable text must be reviewed visually.</p>')
    chunks.append(f"<p><a href=\"{esc(report['document']['source_uri'])}\">Open source PDF</a> · "
                  '<a href="report.json">Download JSON evidence</a></p>')
    chunks.append(f"<p>Estimated body font: {esc(report['document']['body_font_estimate_pt'])} pt. "
                  f"Float policy: {esc(report['profile']['float_policy'])}. "
                  f"Exempt physical pages: {esc(report['profile']['exempt_pages'])}.</p>")
    chunks.append("<h2>Coverage</h2><table><tr><th>Check</th><th>Status</th><th>Limits</th></tr>")
    for item in report["coverage"]:
        chunks.append(f"<tr><td>{esc(item['check'])}</td><td>{esc(item['status'])}</td>"
                      f"<td>{esc(item['limitations'])}</td></tr>")
    chunks.append("</table><h2>Review candidates</h2>")
    if not report["issues"]:
        chunks.append('<p>No candidates from the enabled automated checks. This is not a layout pass.</p>')
    else:
        counts = collections.Counter(issue["rule"] for issue in report["issues"])
        chunks.append("<table><tr><th>Candidate rule</th><th>Count</th></tr>")
        for rule, count in sorted(counts.items()):
            chunks.append(f"<tr><td>{esc(rule)}</td><td>{count}</td></tr>")
        chunks.append("</table><p class=\"muted\">Counts describe review candidates, not confirmed defects. "
                      "Small-text candidates are grouped below by physical page.</p>")

    def append_issue(issue: dict) -> None:
        chunks.append(f'<article class="issue" id="{esc(issue["id"])}"><strong>{esc(issue["rule"])}</strong> '
                      f'<span class="badge">{esc(issue["severity"])}</span> · '
                      f'<a href="#page-{issue["page"]}">physical page {issue["page"]}</a> '
                      f'(label {esc(issue["page_label"])})'
                      f'<pre>{esc(json.dumps(issue["evidence"], ensure_ascii=False, indent=2))}</pre>'
                      f'<p class="muted">Candidate confidence: {issue["confidence"]}; review required.</p></article>')

    small_by_page = collections.defaultdict(list)
    for issue in report["issues"]:
        if issue["rule"] == "small_text_candidate":
            small_by_page[issue["page"]].append(issue)
        else:
            append_issue(issue)
    for page_number, page_issues in sorted(small_by_page.items()):
        chunks.append(f"<details><summary>Physical page {page_number}: "
                      f"{len(page_issues)} small-text candidates</summary>")
        for issue in page_issues:
            append_issue(issue)
        chunks.append("</details>")
    chunks.append("<h2>All extracted body-reference candidates</h2><table><tr><th>Reference</th>"
                  "<th>Page</th><th>Context</th><th>Match / distance</th></tr>")
    for reference in report["references"]:
        distance = f"{reference['page_gap']} page(s)" if reference["page_gap"] is not None else "unresolved/ambiguous"
        detail = {"status": reference["match_status"], "selected_caption_id": reference["selected_caption_id"],
                  "candidate_distances": reference["candidate_distances"],
                  "same_page_geometry": reference["same_page_geometry"],
                  "source_role_ambiguity": reference["source_role_ambiguity"],
                  "distance_exemption": reference["distance_exemption"]}
        chunks.append(f"<tr><td>{esc(reference['kind'])} {esc(reference['number'])}"
                      f"{esc(' (' + reference['panel'] + ')' if reference['panel'] else '')}"
                      f"<br>{esc(reference['id'])}</td><td><a href=\"#page-{reference['physical_page']}\">"
                      f"{reference['physical_page']}</a></td><td>{esc(reference['context'])}</td>"
                      f"<td>{esc(distance)}<details><summary>Evidence</summary>"
                      f"<pre>{esc(json.dumps(detail, ensure_ascii=False, indent=2))}</pre></details></td></tr>")
    chunks.append("</table><h2>Physical pages</h2>")
    for page in report["pages"]:
        number = page["physical_page"]
        chunks.append(f'<section id="page-{number}"><h3>Physical page {number} · label {esc(page["page_label"])}</h3>')
        chunks.append(f"<p>{esc(page['text_status'])}; role: {esc(page['page_role'])}; "
                      f"bbox occupancy: {page['occupied_bbox_fraction']:.1%}; "
                      f"heuristic exemption: {esc(page['heuristic_exemption'])}.</p>")
        if page.get("render_path"):
            chunks.append(f'<a href="{esc(page["render_path"])}"><img class="page-image" '
                          f'src="{esc(page["render_path"])}" alt="Rendered physical page {number}" loading="lazy"></a>')
        else:
            chunks.append(f'<p><a href="{esc(report["document"]["source_uri"])}#page={number}">Open PDF page</a>'
                          ' (viewer support varies). Use --render for local page images.</p>')
        page_captions = [caption for caption in report["captions"] if caption["physical_page"] == number]
        chunks.append("<details><summary>Caption candidates and text roles</summary>")
        for caption in page_captions:
            chunks.append(f"<p><strong>{esc(caption['id'])}</strong> ({esc(caption['status'])}, "
                          f"{caption['confidence']}): {esc(caption['text'])}</p>")
        chunks.append("<ul>")
        for line in page["text_lines"]:
            chunks.append(f"<li><span class=\"badge\">{esc(line['role'])}</span> {esc(line['text'])}</li>")
        chunks.append("</ul></details></section>")
    chunks.append("<p class=\"muted\">Produced locally by paperflow " + esc(VERSION)
                  + ". Source PDF unchanged. Numeric confidence values are heuristic scores, not calibrated probabilities.</p></html>")
    (out / "report.html").write_text("\n".join(chunks), encoding="utf-8")


def audit(source: Path, out: Path, profile: dict, render: bool) -> dict:
    try:
        import fitz
    except ImportError as error:
        raise ValueError("PyMuPDF is required: python -m pip install PyMuPDF") from error
    if not source.is_file():
        raise ValueError(f"input PDF does not exist: {source}")
    out.mkdir(parents=True, exist_ok=True)
    with fitz.open(source) as document:
        if not document.is_pdf:
            raise ValueError("input must be a PDF")
        if document.needs_pass:
            raise ValueError("PDF is encrypted; provide a locally decrypted copy")
        if not len(document):
            raise ValueError("PDF contains no pages")
        targets = [out / "report.json", out / "report.html"]
        if render:
            targets += [out / "pages" / f"page-{page_index + 1:04d}.png"
                        for page_index in range(len(document))]
        reject_source_output_collision(source, targets)
        if any(page > len(document) for page in profile["exempt_pages"]):
            raise ValueError("exempt_pages contains a physical page beyond this PDF")
        pages = extract_pages(document)
        assign_page_roles(pages)
        captions = detect_captions(pages)
        references = match_references(pages, captions)
        body_font = estimate_body_font(pages)
        issues = build_issues(pages, captions, references, profile, body_font)
        if render:
            render_dir = out / "pages"
            render_dir.mkdir(exist_ok=True)
            for page_index, page in enumerate(document):
                relative = f"pages/page-{page_index + 1:04d}.png"
                page.get_pixmap(dpi=profile["render_dpi"], alpha=False).save(out / relative)
                pages[page_index]["render_path"] = relative
        report = {
            "schema_version": SCHEMA_VERSION, "tool_version": VERSION,
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "document": {
                "filename": source.name, "source_path": str(source.resolve()),
                "source_uri": source.resolve().as_uri(), "page_count": len(document),
                "sha256": file_sha256(source),
                "body_font_estimate_pt": body_font,
                "body_font_estimate_method": "Character-weighted modal span size, rounded to quarter points, in body-candidate lines.",
                "coordinate_system": "PDF points in unrotated page coordinates; 1 point = 1/72 inch. Reference bboxes cover the containing line.",
                "source_modified": False,
            },
            "profile": profile, "pages": pages, "captions": captions,
            "references": references, "reference_groups": summarize_groups(references, captions),
            "issues": issues, "coverage": build_coverage(pages),
            "assessment": {
                "status": "review_required",
                "no_issues_means_pass": False,
                "confidence_note": "Heuristic evidence scores, not calibrated probabilities.",
                "automatic_repairs": [],
            },
        }
        (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False),
                                       encoding="utf-8")
        write_html(report, out)
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, help="local PDF (read only)")
    parser.add_argument("--out", type=Path, required=True, help="output directory for report.json and report.html")
    parser.add_argument("--profile", type=Path, help="JSON configuration; unknown keys are rejected")
    parser.add_argument("--render", action="store_true", help="also render every PDF page to local PNG files")
    parser.add_argument("--version", action="version", version=f"paperflow {VERSION} (schema {SCHEMA_VERSION})")
    args = parser.parse_args()
    try:
        profile = load_profile(args.profile)
        report = audit(args.input, args.out, profile, args.render)
    except (ValueError, OSError, RuntimeError, TypeError) as error:
        print(f"audit_pdf: {error}", file=sys.stderr)
        return 2
    print(json.dumps({
        "report": str((args.out / "report.html").resolve()),
        "json": str((args.out / "report.json").resolve()),
        "physical_pages": report["document"]["page_count"],
        "caption_candidates": len(report["captions"]),
        "body_reference_candidates": len(report["references"]),
        "review_candidates": len(report["issues"]),
        "status": "review_required",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
