#!/usr/bin/env python3
"""Make independent adversarial layout fixtures, not production documents.

Source drawings and text are original. The bad pages deliberately contain faults.
The generated faults are intentional; do not use these as manuscript templates.
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
from textwrap import wrap

import fitz
from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

W, H = 612, 792
NAVY = HexColor("#123b55")
TEAL = HexColor("#147d83")
GRAY = HexColor("#52606c")
LIGHT = HexColor("#e4edf1")


def canvas(path: Path, title: str) -> Canvas:
    c = Canvas(str(path), pagesize=(W, H), pageCompression=1)
    c.setTitle(title)
    c.setAuthor("Independent layout behavior fixtures")
    return c


def header(c: Canvas, title: str, page: int, subtitle: str = "") -> None:
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(54, H - 55, title)
    c.setFont("Helvetica", 9)
    c.setFillColor(GRAY)
    if subtitle:
        c.drawString(54, H - 74, subtitle)
    c.setStrokeColor(LIGHT)
    c.line(54, 44, W - 54, 44)
    c.setFont("Helvetica", 9)
    c.drawString(54, 30, "Independent layout fixture - fictional results")
    c.drawRightString(W - 54, 30, str(page))
    c.setFillColor(black)


def para(c: Canvas, text: str, x: float = 54, y: float = 685,
         width: float = 500, size: float = 11, leading: float = 15) -> float:
    c.setFillColor(black)
    c.setFont("Helvetica", size)
    # Word wrapping uses actual string width rather than character count.
    words = text.split()
    line = ""
    for word in words:
        candidate = (line + " " + word).strip()
        if c.stringWidth(candidate, "Helvetica", size) > width and line:
            c.drawString(x, y, line)
            y -= leading
            line = word
        else:
            line = candidate
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y - 8


def filler(c: Canvas, x: float = 54, y: float = 650, width: float = 500,
           paragraphs: int = 4) -> None:
    text = (
        "The observations were collected under the same acquisition protocol. "
        "Each sample contributes one independent measurement. "
        "The reported comparison is restricted to this controlled setting. "
        "Additional details document how the experimental record was assembled."
    )
    for _ in range(paragraphs):
        y = para(c, text, x, y, width)


def figure(c: Canvas, label: str = "1", x: float = 74, y: float = 345,
           width: float = 450, height: float = 220, caption: str | None = None,
           panel: str = "") -> None:
    """A vector-only chart. No bitmap image object exists."""
    c.setFillColor(HexColor("#f8fafb"))
    c.rect(x, y, width, height, fill=1, stroke=0)
    left, bottom = x + 42, y + 32
    right, top = x + width - 20, y + height - 24
    c.setStrokeColor(GRAY)
    c.setLineWidth(0.8)
    c.line(left, bottom, right, bottom)
    c.line(left, bottom, left, top)
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 9)
    for i in range(5):
        tick = left + i * (right - left) / 4
        c.line(tick, bottom, tick, bottom - 3)
        c.drawCentredString(tick, bottom - 13, str(i))
    c.drawCentredString((left + right) / 2, y + 4, "Measurement index")
    c.saveState()
    c.translate(x + 13, (top + bottom) / 2)
    c.rotate(90)
    c.drawCentredString(0, 0, "Response (a.u.)")
    c.restoreState()
    c.setStrokeColor(TEAL)
    c.setLineWidth(2)
    p = c.beginPath()
    for i, value in enumerate([0.22, 0.4, 0.38, 0.68, 0.84]):
        px = left + i * (right - left) / 4
        py = bottom + value * (top - bottom)
        p.moveTo(px, py) if i == 0 else p.lineTo(px, py)
        c.setFillColor(TEAL)
        c.circle(px, py, 2.5, fill=1, stroke=0)
    c.drawPath(p)
    if panel:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x + 8, y + height - 15, panel)
    para(c, caption or f"Figure {label}. Response across repeated measurement settings.",
         x, y - 18, width, 9.5, 12)


def near(path: Path) -> None:
    c = canvas(path, "Near reference - positive control")
    header(c, "1. Local figure explanation", 1)
    para(c, "The rise is concentrated in the last two measurements (Figure 1). "
         "The chart immediately below lets the reader verify this pattern.", y=682)
    figure(c, y=340)
    filler(c, y=270, paragraphs=2)
    c.save()


def far(path: Path, end_matter: bool = False) -> None:
    c = canvas(path, "End-matter policy" if end_matter else "Distant essential figure")
    header(c, "1. Main result", 1)
    para(c, "The rise is concentrated in the last two measurements (Figure 1). "
         "The relative changes and the turning point are needed to interpret this claim.", y=682)
    if end_matter:
        para(c, "Submission policy for this fixture: all figures must appear after the text. "
             "A final typeset reading copy will place them near their citations.", y=615)
    filler(c, y=550, paragraphs=5)
    c.showPage()
    for p, title in [(2, "2. Acquisition protocol"), (3, "3. Additional controls")]:
        header(c, title, p)
        filler(c, y=680, paragraphs=7)
        c.showPage()
    header(c, "Figures" if end_matter else "4. Deferred visual evidence", 4)
    figure(c, y=390)
    para(c, "This is the sole Figure 1 in the document.", y=320)
    c.save()


def directory(path: Path) -> None:
    c = canvas(path, "Figure directory is not body prose")
    header(c, "List of Figures", 1)
    c.setFont("Helvetica", 11)
    c.drawString(54, 680, "Figure 1. Response across settings ................................... 3")
    para(c, "This page is a navigational directory.", y=625)
    c.showPage()
    header(c, "1. Acquisition protocol", 2)
    filler(c, y=680, paragraphs=6)
    c.showPage()
    header(c, "2. Observed response", 3)
    para(c, "The response increases most strongly at the end of the range (Figure 1).", y=682)
    figure(c, y=355)
    filler(c, y=280, paragraphs=2)
    c.save()


def multiple(path: Path) -> None:
    c = canvas(path, "Different reference roles")
    header(c, "1. Roadmap", 1)
    para(c, "The paper introduces the acquisition protocol, then summarizes the response "
         "in Figure 1, and finally describes the controls.", y=682)
    filler(c, y=615, paragraphs=6)
    c.showPage()
    header(c, "2. Acquisition protocol", 2)
    filler(c, y=680, paragraphs=7)
    c.showPage()
    header(c, "3. Observed response", 3)
    para(c, "The first three measurements are almost flat, whereas the last two increase "
         "markedly (Figure 1). Inspecting the bend is essential to this comparison.", y=682)
    figure(c, y=350)
    filler(c, y=275, paragraphs=2)
    c.save()


def columns(path: Path) -> None:
    c = canvas(path, "Two-column reading order")
    header(c, "Two-column reading path", 1)
    para(c, "The chart is encountered in the right column after the left column finishes. "
         "Its reference appears near the bottom of the left column.", 54, 680, 235)
    filler(c, x=54, y=595, width=235, paragraphs=3)
    para(c, "The last two measurements dominate the increase (Figure 1).",
         54, 180, 235)
    figure(c, x=323, y=470, width=235, height=205)
    filler(c, x=323, y=400, width=235, paragraphs=3)
    c.save()


def ambiguity(path: Path) -> None:
    c = canvas(path, "Caption versus sentence")
    header(c, "Caption and prose distinction", 1)
    # A paragraph begins with Figure, but is not a caption and has no nearby visual.
    para(c, "Figure 1 shows the response rising in the final two settings. This sentence "
         "belongs to the main discussion; its initial words do not make it a caption.",
         y=680)
    figure(c, y=365, caption="Figure 1. Response under the controlled acquisition protocol.")
    para(c, "The measurement totals are given in Table 1.", y=295)
    c.setFillColor(LIGHT)
    c.rect(74, 190, 450, 45, fill=1, stroke=0)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(90, 219, "Setting")
    c.drawString(300, 219, "Independent samples")
    c.setFont("Helvetica", 10)
    c.drawString(90, 200, "A / B")
    c.drawString(300, 200, "12 / 12")
    para(c, "Table 1. Number of samples in each acquisition setting.", 74, 174, 450, 9.5, 12)
    c.save()


def supplementary(path: Path) -> None:
    c = canvas(path, "Supplementary figure and panel references")
    header(c, "Supplementary response", 1)
    para(c, "The stable early values are visible in Figure S1a; the later rise is "
         "shown in Fig. S1(b). Both panels support the same controlled comparison.", y=682)
    # Use a shared caption for panels; panel b is not another numbered figure.
    figure(c, label="S1", x=54, y=390, width=235, height=215, caption="(a) Early range.", panel="a")
    figure(c, label="S1", x=323, y=390, width=235, height=215, caption="(b) Later range.", panel="b")
    para(c, "Figure S1. Response by measurement range. (a) Early range. (b) Later range.",
         54, 330, 504, 9.5, 13)
    para(c, "For the panel comparison, use the shared supplementary figure identifier.", y=278)
    c.save()


def typography(path: Path) -> None:
    c = canvas(path, "Typography and page exceptions")
    header(c, "Readable control", 1)
    para(c, "This page uses 11-point body text, conventional margins, and 9.5-point "
         "captions. The footnote below uses 8 points intentionally.", y=682)
    figure(c, y=350)
    c.setFont("Helvetica", 8)
    c.drawString(54, 85, "1. A brief footnote is smaller than the surrounding body text.")
    c.showPage()
    header(c, "Deliberately defective page", 2)
    para(c, "The following block is body text rendered at 5 points; it is not a footnote.",
         y=682)
    para(c, "Tiny body text repeats a substantive explanation that readers must understand. " * 12,
         y=620, size=5, leading=6.5)
    c.setFont("Helvetica", 12)
    c.drawString(54, 410, "The next two body lines overlap and require source-level repair.")
    c.drawString(54, 404, "Their baselines are separated by only six points.")
    c.setFont("Helvetica", 12)
    c.drawString(545, 310, "Visible text continues beyond the crop edge and is clipped.")
    c.setFont("Helvetica", 11)
    c.drawString(-40, 275, "LEFT-CROPPED body text starts outside the page.")
    c.showPage()
    # Truly blank page is intentional in paired policy, not automatically an error.
    c.showPage()
    header(c, "Blank-page policy", 4)
    para(c, "Page 3 is intentionally blank so this section opens on a new spread. "
         "Treat blank-page detection as evidence, then apply the declared document policy.", y=682)
    filler(c, y=605, paragraphs=5)
    c.save()


def scanned(path: Path) -> None:
    memory = io.BytesIO()
    c = Canvas(memory, pagesize=(W, H))
    header(c, "Image-only page", 1)
    para(c, "The measurements rise toward the end of the range (Figure 1).", y=682)
    figure(c, y=350)
    para(c, "This entire page will be embedded as one image. Text extraction is unavailable.", y=270)
    c.save()
    source = fitz.open(stream=memory.getvalue(), filetype="pdf")
    pix = source[0].get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
    c2 = canvas(path, "Scanned image-only fixture")
    c2.drawImage(ImageReader(io.BytesIO(pix.tobytes("png"))), 0, 0, W, H)
    c2.save()
    source.close()


GOLD = [
    {
        "id": "01_near_vector",
        "file": "01_near_vector.pdf",
        "observable_facts": {"pages": 1, "figure_1_caption_page": 1, "substantive_ref_pages": [1],
                             "raster_images": 0, "vector_chart": True},
        "expected_review_behavior": [
            "Recognize a real Figure 1 although no embedded raster image exists.",
            "Do not flag its citation as remotely placed; inspect the nearby vector plot and caption."
        ],
        "must_not_claim": ["Raster-image count of zero means the document has no figure.",
                           "The chart is scientifically correct because its layout is readable."]
    },
    {
        "id": "02_far_essential",
        "file": "02_far_essential.pdf",
        "observable_facts": {"pages": 4, "figure_1_caption_page": 4, "substantive_ref_pages": [1],
                             "physical_page_gap": 3, "end_matter_policy": False},
        "expected_review_behavior": [
            "Report Figure 1 at physical page 4 and its essential interpreting paragraph at physical page 1.",
            "Treat three pages of navigation as a concrete locality review candidate; propose a nearby float only after checking constraints."
        ],
        "must_not_claim": ["An arbitrary three-page threshold establishes measured reader confusion.",
                           "A source edit was performed when only the PDF was supplied."]
    },
    {
        "id": "03_end_matter_exception",
        "file": "03_end_matter_exception.pdf",
        "observable_facts": {"pages": 4, "figure_1_caption_page": 4, "substantive_ref_pages": [1],
                             "physical_page_gap": 3, "declared_policy_page": 1},
        "expected_review_behavior": [
            "Expose the same measured gap as 02_far_essential.",
            "Honor the explicit submission policy requiring end-matter figures; do not call this a mandatory placement violation.",
            "A suggestion for an additional reading copy is permissible, but no forced relocation."
        ],
        "must_not_claim": ["All figures farther than one page must be moved.", "A manuscript-layout rule overrides a declared submission format."]
    },
    {
        "id": "04_figure_directory",
        "file": "04_figure_directory.pdf",
        "observable_facts": {"pages": 3, "directory_page": 1, "figure_1_caption_page": 3,
                             "first_body_ref_page": 3, "directory_entry_mentions_figure_1": True},
        "expected_review_behavior": [
            "Treat page 1 as a navigational list, not the first substantive reference.",
            "Pair the actual chart caption on page 3 with nearby body prose on page 3.",
            "If the extractor cannot disambiguate the list entry, mark it ambiguous rather than assert a two-page locality fault."
        ],
        "must_not_claim": ["The list entry is definitely a second Figure 1 caption.", "The first text match always defines the reference location."]
    },
    {
        "id": "05_reference_roles",
        "file": "05_reference_roles.pdf",
        "observable_facts": {"pages": 3, "roadmap_ref_page": 1, "essential_ref_page": 3,
                             "figure_1_caption_page": 3, "lexical_first_page_gap": 2,
                             "substantive_page_gap": 0},
        "expected_review_behavior": [
            "Retain evidence for both mentions rather than silently discarding one.",
            "Distinguish the introductory roadmap on page 1 from the essential comparison on page 3.",
            "Do not force Figure 1 onto page 1 simply because its name appears there first."
        ],
        "must_not_claim": ["A lexical first-mention metric is equivalent to semantic reading difficulty."]
    },
    {
        "id": "06_two_columns",
        "file": "06_two_columns.pdf",
        "observable_facts": {"pages": 1, "columns": 2, "reference_position": "left column near bottom",
                             "figure_position": "right column near top", "physical_page_gap": 0},
        "expected_review_behavior": [
            "Inspect column reading order; left-bottom to right-top may be an adjacent reading transition.",
            "Keep same-page geometry separate from a claim of true reading-path distance.",
            "Do not sort lines globally by y position and claim this reflects column order."
        ],
        "must_not_claim": ["Same page always means easy to find.", "The vertical distance across columns is a validated reading-cost measure."]
    },
    {
        "id": "07_caption_prose_ambiguity",
        "file": "07_caption_prose_ambiguity.pdf",
        "observable_facts": {"pages": 1, "true_figure_captions": ["Figure 1."],
                             "true_table_captions": ["Table 1."],
                             "body_sentence_start": "Figure 1 shows the response",
                             "actual_figures": 1, "actual_tables": 1},
        "expected_review_behavior": [
            "Do not classify the full body paragraph beginning 'Figure 1 shows' as a second figure caption.",
            "Preserve separate figure and table identities.",
            "If caption ambiguity remains, report that uncertainty for visual confirmation."
        ],
        "must_not_claim": ["Duplicate captions proven by a mere Figure-number prefix.", "Table 1 and Figure 1 identify the same object."]
    },
    {
        "id": "08_supplementary_panels",
        "file": "08_supplementary_panels.pdf",
        "observable_facts": {"pages": 1, "true_figure_captions": ["Figure S1."],
                             "panel_refs": ["Figure S1a", "Fig. S1(b)"],
                             "unrelated_figure_1": False, "vector_chart_panels": 2},
        "expected_review_behavior": [
            "Keep supplementary Figure S1 distinct from main-text Figure 1.",
            "Associate panel a and panel b references with the same numbered figure, preserving panel specificity.",
            "Fallback to manual verification when parsing panel syntax is unsupported."
        ],
        "must_not_claim": ["Both panel references are broken simply because their spelling differs from the caption.",
                           "Panel a and panel b are duplicate numbered captions."]
    },
    {
        "id": "09_typography_and_blank",
        "file": "09_typography_and_blank.pdf",
        "observable_facts": {"pages": 4, "normal_body_pt": 11, "normal_footnote_pt": 8,
                             "bad_body_page": 2, "bad_body_pt": 5, "overlapping_lines_page": 2,
                             "off_crop_text_page": 2, "blank_page": 3, "blank_page_policy_page": 4},
        "expected_review_behavior": [
            "Distinguish the brief 8-point footnote from substantive 5-point body text.",
            "Visually identify overlapping body lines and clipped text on page 2.",
            "Record page 3 as blank, then apply the explicit spread-opening exception rather than deleting it.",
            "Do not promise complete clipping detection from extracted text: off-crop glyphs can be absent from extraction."
        ],
        "must_not_claim": ["Any font smaller than the median is an error.", "Every blank page must be deleted.",
                           "No clipping exists because extracted bounding boxes are within the crop box."]
    },
    {
        "id": "10_image_only",
        "file": "10_image_only.pdf",
        "observable_facts": {"pages": 1, "extractable_text_characters": 0, "raster_page_images": 1,
                             "visible_figure_1": True, "visible_ref_page": 1},
        "expected_review_behavior": [
            "Mark text-based figure matching and font checks unavailable until OCR or visual review.",
            "Render the page and inspect visible content; do not issue a fully verified pass."
        ],
        "must_not_claim": ["The page has no captions or references.", "All checks passed because no text-level violations were detected."]
    },
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "generated")
    parser.add_argument("--render", action="store_true", help="Render selected pages for independent visual inspection.")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    builders = [
        near, far, lambda p: far(p, True), directory, multiple,
        columns, ambiguity, supplementary, typography, scanned,
    ]
    for item, builder in zip(GOLD, builders, strict=True):
        builder(args.out / item["file"])
    (args.out / "gold.json").write_text(json.dumps({
        "schema_version": 1,
        "purpose": "Independent behavioral fixtures; no production auditor implementation was read.",
        "scoring": {
            "unit": "case plus expected behavior",
            "automatic_metrics": "Only facts the selected extraction/render method can actually observe.",
            "human_review": "Semantic roles, venue exceptions, and final visual quality require independent assessment.",
            "no_claim": "This is a small synthetic suite, not a validated measure of reader performance or production recall."
        },
        "cases": GOLD,
        "real_document_candidate": {
            "title": "Connecting the Dots: Surfacing Structure in Documents through AI-Generated Cross-Modal Links",
            "submitted": "2026-02-18",
            "primary_url": "https://arxiv.org/abs/2602.16895",
            "pdf_url": "https://arxiv.org/pdf/2602.16895",
            "version": "v1",
            "rationale": "40 pages, 16 figures; a real mixed-layout stress test and primary study of cross-modal navigation.",
            "caution": "Suitability as a test document does not certify this paper's own layout as an optimum."
        }
    }, indent=2, ensure_ascii=False) + "\n")
    checks = {}
    for item in GOLD:
        doc = fitz.open(args.out / item["file"])
        checks[item["id"]] = {
            "actual_pages": len(doc),
            "extractable_characters_per_page": [len(p.get_text().strip()) for p in doc],
            "image_objects_per_page": [len(p.get_images()) for p in doc],
            "drawing_objects_per_page": [len(p.get_drawings()) for p in doc],
        }
        assert len(doc) == item["observable_facts"]["pages"], (item["id"], len(doc))
        if item["id"] == "10_image_only":
            assert not doc[0].get_text().strip()
        if item["id"] == "01_near_vector":
            assert not doc[0].get_images()
            assert doc[0].get_drawings()
        if args.render:
            pages = [0]
            if item["id"] == "09_typography_and_blank":
                pages = [0, 1, 2, 3]
            elif item["id"] == "04_figure_directory":
                pages = [0, 2]
            elif item["id"] in {"02_far_essential", "03_end_matter_exception", "05_reference_roles"}:
                pages = [0, len(doc) - 1]
            for page_no in pages:
                pix = doc[page_no].get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False)
                pix.save(args.out / f"{item['id']}-p{page_no + 1}.png")
        doc.close()
    (args.out / "fixture-manifest.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(f"Generated {len(GOLD)} independent PDF fixtures and gold.json in {args.out}")


if __name__ == "__main__":
    main()
