# Bundled tools and profiles

Python 3.10+ is required. The PDF helper needs PyMuPDF; other helpers use only the standard library. No helper calls an LLM service or uploads a document.

If dependencies are missing, use an available isolated environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r "<skill-dir>/requirements.txt"
.venv/bin/python "<skill-dir>/scripts/audit_pdf.py" paper.pdf --out audit/before --render
```

Use the matching Windows virtual-environment executable on Windows. Do not hardcode the author's machine paths. If dependency installation is unavailable, use an available PDF renderer/extractor and follow the visual workflow; mark automated evidence unavailable.

## PDF evidence

```bash
python "<skill-dir>/scripts/audit_pdf.py" paper.pdf \
  --profile "<skill-dir>/profiles/embedded.json" --out audit/before --render
```

`report.json` contains:

- `schema_version`, `tool_version`, UTC generation time, document SHA-256 and input identity;
- `pages`: 1-based `physical_page`, PDF `page_label`, unrotated point coordinates, text lines/spans, font size, primitive geometry and approximate bbox occupancy;
- `captions`: probable/possible caption candidates, their geometry and heuristic confidence;
- `references`: all extracted body-reference candidates, contexts, panel suffixes, matching alternatives, absolute `page_gap`, `signed_page_delta`, and same-page geometry;
- `reference_groups`: earliest extracted reference per figure/table identity;
- `issues`: page, box, candidate rule, evidence, severity, confidence, exemption and `review_required`;
- `coverage` and `assessment`: explicit unimplemented checks; no automatic repairs.

`report.html` provides a readable local evidence inventory with page anchors. `--render` adds `pages/page-NNNN.png`; without it, local PDF page links depend on the viewer. Rendering all pages can use substantial disk space on long documents; choose DPI accordingly.

### Interpretation

`signed_page_delta = caption physical page - reference physical page`; negative means the figure precedes the mention. `page_gap` is its absolute value. The caption position is a proxy, **not a recovered figure boundary**. Numeric confidence is a heuristic score, not a calibrated probability.

The matcher recognizes English/Chinese Figure/Fig./Table/图/表, Arabic and supplementary S numbering, common panel suffixes, simple lists and bounded integer ranges. Explicit `Supplementary Table 1` / `Supplementary Figure 1` normalize to `S1` in their respective table/figure scopes; original text is retained. Roman numerals, cross-line markers, unconventional identifiers and complex ranges can be missed. Repeated page furniture and figure directories are filtered heuristically. A `possible_caption` remains an ambiguity, not a confirmed duplicate. Footnote superscripts can merge into a number (for example, `Figure 15.` plus superscript `3`). References inside quoted examples, questionnaires, screenshots or excerpts from another paper need semantic scope verification even if their ID matches uniquely.

There is no OCR. A scanned page has unavailable text checks even if it visibly contains text. Hidden OCR text, text turned into vector outlines, rotated text and unusual crop boxes need visual confirmation. The helper does not reconstruct chart elements or prove table/figure completeness.

Page occupancy is a 100×100 grid approximation of **bounding-box coverage** including vector primitives, raster images and text; it is not the fraction of actual ink. Large background rectangles can hide empty areas. Sparse-page candidates exclude cover/final pages and are not instructions to fill space.

### Profile values

Both supplied profiles are generic triage defaults, not publication standards. Use `end-matter.json` when the actual submission policy requires figures/tables at the end. It retains measured gaps but exempts the distance warning.

| Key | Default | Meaning |
|---|---:|---|
| `far_reference_page_gap` | 2 | Flag absolute page gaps at or above this integer |
| `float_policy` | `inline` | `inline` or `end_matter`; changes proximity warnings |
| `minimum_font_pt` | 7 | Small-text candidate if size is below this value |
| `minimum_body_font_ratio` | 0.65 | Also flag size below this fraction of estimated body type |
| `sparse_page_max_occupied_fraction` | 0.12 | Sparse internal-page candidate; bbox-based, not actual whitespace |
| `page_edge_tolerance_pt` | 0.5 | Tolerance for extracted text outside page boundary |
| `render_dpi` | 110 | PNG rendering, integer 72–300 |
| `exempt_pages` | `[]` | Physical pages exempt from proximity/font/sparse heuristics; keep geometry and boundary findings |

Unknown keys and invalid values are errors. Record the actual reason for exemptions in the final review. A profile cannot declare the content correct or suppress a confirmed clipping problem.

## Build diagnostics

```bash
python "<skill-dir>/scripts/audit_build_log.py" main.log --out audit/build-log.json
```

Collects recognized TeX messages: undefined references/citations, duplicate labels, over/underfull boxes, float size/queue warnings, missing glyphs/files, font substitution, rerun requests and TeX errors. It does not parse every compiler format or know the compiler exit status. Underfull warnings often need no action; inspect the output.

## Compare artifacts

```bash
python "<skill-dir>/scripts/compare_reports.py" \
  audit/before/report.json audit/after/report.json --out audit/comparison.json
```

Compares profile, page count, candidate counts by rule, all reference distances and extracted text-token counts. It suppresses known running furniture and normalizes common ligatures/line-break hyphenation. Page-number changes and extraction artifacts can still produce false differences.

Token multisets do not preserve word order and cannot establish semantic equality. Missing text/data in images will not appear in this diff. Inspect source edits and the rendered output. A lower candidate count, unchanged hash of a figure, or equal text tokens alone is not proof of a successful repair.

All helpers return `0` when collection/comparison completes and `2` on input/configuration errors. **Exit 0 is not a layout pass.** There is deliberately no CI gate on the number of heuristic warnings.
