# Figure–text proximity and reading paths

## Establish the association before measuring

Build a small ledger per figure/table: number, visible caption, panel letters, physical page and printed label, source label if available, all mentions, and the passages that interpret its evidence.

Classify mentions by reading them:

- **Orientation:** “An overview is given in Figure 1.”
- **Interpretation:** explains a particular curve, region, panel, comparison or table cell.
- **Backward reminder:** briefly recalls a result already explained.
- **Navigation:** directory, caption-to-caption reference, index, bibliography or supplementary pointer.

The collector finds textual candidates; it does **not** perform these semantic classifications. Exclude navigation from the body-first-reference calculation. A teaser may precede its first mention deliberately. Distinguish “Fig. 2b” from the whole figure; separate numbering scopes in main text and supplements.

Match explicit IDs first, then verify caption and panel content. Check the numbering scope: a quoted prompt, questionnaire or embedded excerpt may refer to a different paper's Figure 1. Unique lexical matches can still be wrong. If duplicates, unconventional identifiers, ranges, OCR errors, or missing labels make the match uncertain, show alternatives. A failed match does not prove a missing figure. The visible visual may have a caption on another page.

## Measure what is observable

Record page gap for the first body mention **and each important explanatory passage**. For same-page items, show positions and columns; for adjacent pages, show where each lies. Physical page gap is not the number of page turns a reader necessarily makes.

Reading settings matter:

| Setting | Useful observation |
|---|---|
| Single-column paper | Intervening blocks, whether figure and explanation can be seen together |
| Two-column paper | Column order, spanning floats, whether the reader must jump backward across columns |
| Facing-page print | Whether the two pages really face each other; do not infer this from even/odd PDF index alone |
| Scrolling screen | Viewport dimensions and scale, whether repeated scrolling is needed |
| End-matter submission | Compliance with required policy; useful navigation, complete captions and numbering |

Do not report an invented composite “reading distance.” Without reliable block order or known viewport, provide page/coordinate evidence and a qualitative judgment.

Default `far_reference_page_gap=2` is a **triage heuristic**, not a literature-derived maximum or a venue rule. Review one-page gaps when a long explanation repeatedly needs the figure; exempt distant passing reminders when appropriate. Log the context and rationale.

## Choose the useful repair

Prefer moving the float/source anchor near the central explanation, rearranging allowed floats, grouping related panels, or supplying accurate cross-links. Consider moving explanatory text only when it preserves the argument and is within the user's requested scope.

Do not optimize only the first mention. If the first mention is on page 1, detailed analysis on page 5, and the figure on page 5, moving it to page 1 may worsen the document. Report both relationships and prefer the high-value passage unless the venue dictates otherwise.

A large comparison table may deserve a dedicated page. A figure referred to in several sections may be best left central with useful links. Do not duplicate visual evidence or move it to an appendix just to improve a distance number.

After repair, check **all mentions of the moved item**, its caption/panels, and nearby floats. Record:

```
Figure 4, panel b
First mention: PDF p.2; analysis: PDF p.6, right column
Before: figure p.8; analysis-to-figure gap +2 pages
After: figure p.6 above analysis; first mention remains distant
Decision: retain the early overview; prioritize the detailed comparison
Verification: caption and panel labels intact, p.5–7 checked, no displaced table
```

This example is a reporting pattern, not a universal preferred placement.
