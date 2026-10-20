# Check catalog

Use relevant families for focused requests; cover all applicable families for a full audit. Mark each `checked`, `candidate`, `not_checked`, or `not_applicable`, with a reason. `checked` requires stating what evidence was examined, not merely running a script.

Evidence modes: **P** = PDF helper provides partial candidates/measurements; **L** = build-log helper; **V** = rendered-page visual review; **S** = source/structure inspection; **D** = original data needed. A mode listed here is not a claim that the helper automatically checks the whole row.

| ID | Family / checks | Evidence and decision |
|---|---|---|
| NAV-01 | First mention and explanatory passage proximity; back-and-forth reading | P + V + semantic reading; use proximity guide, inspect every material mention |
| NAV-02 | Figure/table number, panel letter, reference target consistency | P + S + V; verify candidates, numbering scopes and ranges |
| NAV-03 | Reading order: columns, spanning elements, continuations | V + S; text extraction order alone is insufficient |
| NAV-04 | Caption stays with object; caption or table split over pages | V; legitimate continued captions/tables can be correct |
| NAV-05 | Figure order and unreferenced items | P + S + V; an unrecognized reference or deliberate teaser is not automatically a defect |
| NAV-06 | Working internal links, bookmarks and headings | S + actual destination checks; match exported artifact, not just source |
| PAG-01 | Text/figure/table/equation cropping and margin overflow | P + L + V; page-edge candidates do not prove text-block margin violations |
| PAG-02 | Object collisions, text through figures, caption/footnote overlap | V at readable resolution; geometric bounding-box intersections alone overcount |
| PAG-03 | Unexplained holes, float queues, isolated headings/floats | P + L + V; measure context, distinguish intentional structure |
| PAG-04 | Widows/orphans, heading stranded at foot, broken lists | V + S; preserve template-specific rules |
| PAG-05 | Page rhythm, column balance and content density | V; do not fill every blank area or require identical column bottoms |
| PAG-06 | Page size, orientation, margins, page numbering and blank versos | P + S + V; target spec and intentional section breaks govern |
| TYP-01 | Body, caption, footnote, figure and table type at final size | P + V; physical type size and visual legibility both matter |
| TYP-02 | Font hierarchy, style consistency, leading and paragraph spacing | P + S + V; avoid flattening intentional hierarchy |
| TYP-03 | Line length, rivers, stretched justification and repeated hyphenation | L + V; isolated underfull warnings are not sufficient |
| TYP-04 | Embedded/fallback fonts, missing glyphs, math symbols, Unicode/CJK | L + S + V; a searchable PDF can still render incorrectly |
| TYP-05 | Lists, indentation, punctuation, superscripts/subscripts and inline math | V; preserve semantic distinctions and accessibility |
| FIG-01 | Axes, labels, legends, line weights, markers legible at placement size | V; zoomed-in screenshots alone do not establish print legibility |
| FIG-02 | Panels align; consistent scales, aspect ratios, panel order and gutters | V + S; different data scales may be intentional and must stay explicit |
| FIG-03 | Cropped ticks, labels, colorbars, legends, annotations or error bars | V + D when completeness is in doubt |
| FIG-04 | Unused canvas versus actual plot area; sensible figure width/height | V + S; trim canvas before shrinking informative content |
| FIG-05 | Raster sharpness at placed size; vector text survives export | S + V; do not impose one DPI on line art, photographs and screenshots |
| FIG-06 | Visual/text agreement: units, colors, symbols, panels and names | V + semantic reading; verify the source when inconsistent |
| FIG-07 | Series completeness, axis range and data marks survive export | D + V; without original data, state completeness was not established |
| FIG-08 | Consistent figure set without erasing meaningful differences | V; harmonize typography and conventions, not scientific scales blindly |
| TAB-01 | Column width, decimal alignment, units, precision and symbol key | V + semantic reading; do not round/change data for appearance |
| TAB-02 | Table fit and legibility without wholesale scaling | V + S; prioritize structure, wrapping and orientation |
| TAB-03 | Headers repeat on continuation; row/cell integrity; notes attached | V + S; inspect both page boundaries and exported cells |
| TAB-04 | Emphasis/hierarchy supports comparisons; clutter and color dependence | V; honor required conventions and accessible alternatives |
| TAB-05 | Caption and body accurately identify rows/columns and highlights | V + semantic reading; meaning changes require author decision |
| EQN-01 | Equations within text block; aligned continuation and number clearance | L + V + S; break mathematically, not at arbitrary width |
| EQN-02 | Equation references, numbering and punctuation consistent | S + V; shared subequation labels can be intentional |
| EQN-03 | Inline equations do not cause collisions or erratic leading | V; preserve symbols, limits and meaning |
| EQN-04 | Fonts, subscripts, matrices and delimiters remain legible | V at placement size; do not shrink away a problem |
| CAP-01 | Caption self-containment: panel map, abbreviations, units and keys | V + semantic reading; substantive additions need evidence |
| CAP-02 | Caption placement, width, wrapping and hierarchy consistent | V + S; tables-above/figures-below is template-dependent |
| CAP-03 | Figure descriptions and captions serve distinct roles | S + semantic reading; avoid duplicating the caption as uninformative alt text |
| REF-01 | Undefined references/citations, duplicate labels, unresolved fields | L + S + V; a “rerun” message may require rebuild rather than editing |
| REF-02 | Bibliography wrapping, long URLs, DOI links and entry splits | L + V; formatting review does not verify source truth |
| REF-03 | Footnote marker/text mapping, placement and continuation | V + S; look for collisions with floats and rules |
| ACC-01 | Color plus redundant marker/shape/label encoding; grayscale use | V; colorblind-safe flags are assertions, not validation |
| ACC-02 | Meaningful descriptions, searchable text and language metadata | S; missing extraction may need OCR, not a pass |
| ACC-03 | Tagged reading order, headings, table headers and link names | S + suitable accessibility tooling; unavailable checks stay unverified |
| ACC-04 | Contrast and small symbols in actual export, not just design source | V + measured colors where reliable; do not infer conformance |
| DOC-01 | Venue/template version, permitted styles and page-count rules | S + verified current official instructions when compliance is requested |
| DOC-02 | Main matter, references and supplement boundaries | S + V; different page limits/numbering may apply |
| DOC-03 | Anonymization, line numbers, required sections, metadata if requested | S + V; apply the user's submission stage, not a universal default |
| DOC-04 | File integrity, correct build, no stale figure or missing asset | S + L + V; verify the final artifact hash and toolchain |
| REG-01 | Claims, numbers, units, qualifiers, panels and series preserved | Source diff + text comparison + V; automated differences are triage |
| REG-02 | No new overflow, float displacement, broken links or pagination defects | Rebuild + P + L + V; inspect neighbors and final whole-document structure |

## Priority and exceptions

- **Blocker:** confirmed missing/illegible essential material, significant cropping, collision obscuring meaning, broken output, or confirmed required-format violation.
- **Major:** repeated reading disruption, difficult labels, bad splits, or inconsistent mappings.
- **Minor:** spacing/hierarchy inconsistency with limited impact.
- **Candidate:** not a severity. This is an evidence status; pair it with potential severity and explain the uncertainty.

Keep evidence and severity independent. An exact measurement may have low impact. A visual defect may be important even if no parser can measure it.

Generic numeric defaults are triage thresholds. Venue requirements must include the actual official source, date/version, and relevant condition. Do not claim that one font size, whitespace ratio or figure distance suits every document.
