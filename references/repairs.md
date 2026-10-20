# Repairs by source format

## Shared decisions

Preserve a baseline, use the existing build/export route, and keep edits local. The target is a readable final artifact with preserved meaning. Keep source changes reviewable. If only a PDF is supplied, provide audit and source-level recommendations; direct PDF edits are appropriate only when requested and suitable.

Resolve competing objectives in this order: explicit user/venue constraints; completeness and correctness; legibility and navigation; consistency and compactness. Where no option dominates, explain the concrete tradeoff. Do not hide a regression by suppressing a check.

## LaTeX

Inspect document class, active template and packages, float definitions/labels, source order, build log and final PDF. Compile with the existing build command; a common fallback is `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`, but use XeLaTeX/LuaLaTeX if the project requires it.

- **Float too late:** inspect earlier oversized/stuck floats first. Check width and height, placement permissions, source anchor order, and single/double-column environment. Make the earliest cause fit.
- **Too much whitespace:** distinguish a float queue from a deliberate page/section boundary. Remove unnecessary forced breaks/barriers locally. Tune class-supported float settings only after understanding the cause.
- **Wide figure:** fix exported canvas and layout, then use the correct `\linewidth`/`\columnwidth`/`\textwidth`. Re-evaluate physical label size after changing scale.
- **Wide table:** wrap descriptive columns, adjust column structure/spacing within template rules, use an appropriate multi-page/landscape/full-width environment. Keep numbers and precision. A split table needs explicit continuation labels and headers.
- **Long equation:** use meaningful aligned/split forms; keep number clearance. Verify math semantics.
- **Caption or heading split:** use class-compatible settings; avoid blanket package additions that override a venue's style.
- **Undefined refs/cites:** verify target/label/bibliography and rerun the prescribed compilation sequence. Do not delete the reference to silence warnings.

Do not globally force `[H]`, add `\FloatBarrier` at every section, shrink fonts/margins, scatter negative `\vspace`, or scale every table with `\resizebox`. These may trade the visible symptom for new defects. Elsevier `cas-dc`/`cas-sc` and double-column classes deserve explicit queue inspection.

A clean build log does not prove a clean page; an underfull box does not prove a visible defect.

## Word / DOCX

Edit styles and layout settings in the source using available document tooling. Preserve tracked changes and comments unless the user requests accepting/removing them.

- Use paragraph keep-with-next/keep-lines-together for headings and captions where appropriate; avoid making entire sections unsplittable.
- Inspect inline versus anchored figures, wrapping, anchor paragraph, “move with text,” and positioning relative to page/column. Choose inline placement when it best supports the reading order.
- Use true captions and cross-reference fields; update fields and verify the exported destinations and numbers. Do not silently turn fields into static text.
- Inspect table width, repeat-header settings, row-breaking rules, cell margins, paragraph spacing and section orientation.
- Prefer section/page breaks and styles to repeated empty paragraphs or manual spaces.
- Check font substitution, equations, hidden text and printed comments/markup in the intended export.

Export through the available Word/LibreOffice/document runtime and render the result. Different exporters can paginate differently; identify the one tested. If no exporter is available, state that final pagination is unverified.

## Typst

Use the project's installed Typst version and template. Inspect figure placement/scope, column layout, block breakability, show/set rules, caption settings and reference labels. Prefer measured content/block widths and heights to guessed shrink factors.

For balanced posters or columns, compare natural content height with rendered height and available space. Preserve declared exceptions for title bands, asymmetrical panels and intentional spacing. Do not treat balance as an objective to maximize at any cost.

Use `typst compile input.typ output.pdf` only when it is the project's build path. Re-render after changing placement or show rules. No Typst compiler means source review only, not verified layout.

## Markdown / HTML to PDF

Inspect the actual print stylesheet and export engine. Check `break-before/after/inside`, figures/captions, running heads, table header repetition, code blocks, links and print colors. Screen layout alone does not establish PDF layout. Avoid fixed heights that clip translated or longer content.

## Regression check

Run the collector on before/after PDFs with the same profile. Use `scripts/compare_reports.py` to triage new candidate classes and text-token changes. Then inspect affected pages and the figure's other references. Reflow changes coordinates and page numbers; raw pixel or coordinate differences are not automatically regressions.

If content changes appear, inspect the source diff: distinguish line-break hyphenation, field/page-number changes and ligatures from removed claims, numbers, labels or data. Mark unresolved preservation checks explicitly.
