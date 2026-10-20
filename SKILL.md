---
name: paperflow
description: Audit and improve academic paper and long-document layout using rendered pages and source files. Checks figure/table proximity to explanatory text, reading order, typography, whitespace, equations, captions, cross-references, and accessibility. Use for PDF/LaTeX/Word/Typst layout review or repair, not scientific peer review, prose polishing, or website design.
---

# PaperFlow

Make the document easier to read while preserving its content and submission constraints. The rendered artifact is the object of review; source inspection and measurements help locate causes.

## Choose the work

- **Audit:** inspect and report, without modifying the manuscript.
- **Repair:** when the user asks to improve/fix layout, make reversible source edits, rebuild, and verify. Existing authorization applies; do not repeatedly request approval.
- **Focused review:** honor the requested pages or issue. Do not expand a proximity check into a mandatory full production audit.

Infer the intended format and venue from the files. Use an existing template/profile before generic preferences. Ask only for missing information that changes a consequential choice; otherwise state the working assumption and continue. Do not invent a venue rule.

Use these references as needed:

| Work | Read |
|---|---|
| Any full audit; choose relevant checks for a focused audit | [Check catalog](references/checks.md) |
| Figures/tables distant from text; multi-column or multi-panel reading | [Reading proximity](references/proximity.md) |
| Run the PDF collector, interpret evidence, compare versions | [Tools and profiles](references/tools.md) |
| Edit LaTeX, Word, Typst or rendered HTML sources | [Format-specific repairs](references/repairs.md) |
| Deliver findings and verification | [Report contract](references/reporting.md) |

## Collect evidence

1. Identify the actual final PDF and source/build entrypoint. Record filename/hash, page count, venue/template, and whether readers use print, spreads, or a scrolling display. Preserve an untouched baseline.
2. Render the PDF with an available renderer. The bundled helper uses Python and PyMuPDF:

   ```bash
   python "<skill-dir>/scripts/audit_pdf.py" manuscript.pdf --out audit/before --render
   ```

   Replace `<skill-dir>` with this installed folder. Follow [tools](references/tools.md) for dependencies, profiles and fallbacks. Neither the helper nor a successful compilation certifies readability.
3. Inspect rendered pages. For a full audit, scan every page for structure; inspect flagged pages, all figure/table pages, and unusually dense pages at readable resolution. For large documents, work in batches and report completed coverage accurately. Whole-page views reveal rhythm; detail views reveal clipped labels and tiny symbols.
4. Reconcile extracted references/captions against the visible page and source. Keep physical PDF page numbers distinct from printed labels. Check both the **first mention** and the **passage that needs the visual**. A nearer incidental mention does not cancel a distant explanation.
5. Apply the relevant catalog checks. Record unavailable checks explicitly: no text layer, unavailable source, no figure data, no accessibility validator, or pages not visually inspected. Do not convert “no candidates” into “passed.”

## Decide what deserves a change

- Separate measured facts, heuristics, and visual/semantic judgments. A three-page separation is measurable; whether it harms reading needs context.
- Give each actionable finding a page/label, quoted context or bounding box, reader impact, confidence, and a concrete repair. Treat uncertain caption matches and possible omissions as candidates.
- Priority follows impact: missing/cropped content and broken reading paths first; legibility next; spacing and consistency last. Avoid aggregate “quality scores” without a validated rubric.
- Dedicated figure pages, end-matter floats, intentional blank versos, modest whitespace, and venue-specific conventions may be correct. Document applicable exemptions.
- Accessibility includes more than colors: inspect descriptions, text order, table structure, links and final export where available. Never assert PDF/UA or WCAG conformance from a visual scan or a metadata flag.

## Repair and verify

Choose a small set of changes that addresses the cause. Prefer correct float placement, figure canvas/crop, line breaking, table structure, and style settings over global shrinking or spacing hacks.

Preserve claims, numbers, units, uncertainty, qualifiers, legends, error bars, data series, citations and meaningful labels. If a layout change would require substantive rewriting, identify that decision separately. Do not delete scientific content to hit a page limit.

Rebuild using the project's intended toolchain. Inspect changed pages **and their new neighbors**, then scan for pagination/float regressions across the document. Recompute candidate measurements and check content preservation. A moved figure can fix one reference while worsening another.

Use [repairs](references/repairs.md) for tool-specific choices. Do not apply `[H]`, barriers, negative spacing, margin changes, or `resizebox` everywhere. Do not patch an exported PDF when an editable source is available.

Stop when the requested defects are resolved and verification succeeds. After two unsuccessful changes to the same issue, reassess the cause; after three repair/rebuild rounds without net improvement, preserve the best version and explain the unresolved tradeoff. These are workflow defaults, not limits on explicitly requested further work.

## Deliver

Give the improved artifact/source when requested and a concise findings report using [reporting](references/reporting.md). Distinguish confirmed issues, candidates, fixed issues, exemptions, and unchecked areas. Name the pages actually inspected and the checks actually run. Provide before/after evidence for repairs; do not claim a clean bill of health from an empty script report.
