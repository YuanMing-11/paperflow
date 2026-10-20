# Reporting contract

The helper's HTML/JSON is an **evidence inventory**. The final agent review adds visual verification, semantic matching, decisions and repair status. Do not present the inventory as the completed audit.

## Minimum useful report

1. **Scope:** input file/hash, build/source version if available, target format and reading setting, profile/overrides, physical pages inspected and source/tool availability.
2. **Findings:** prioritize reader impact; separate confirmed findings from candidates.
3. **Changes:** source edits, resulting artifact, before/after evidence, completed regression checks.
4. **Coverage:** which catalog families were checked, partially checked, exempted or unavailable. Name specific unverified areas rather than a broad disclaimer.

Each actionable finding should include:

```json
{
  "id": "NAV-01-figure4",
  "status": "confirmed",
  "severity": "major",
  "object": "Figure 4b",
  "physical_pages": [6, 8],
  "printed_labels": ["5", "7"],
  "evidence": {
    "quote": "The second peak in Figure 4b ...",
    "caption_page": 8,
    "reference_page": 6,
    "page_gap": 2,
    "visual_checked": true,
    "source_checked": true
  },
  "impact": "The paragraph repeatedly compares two curves that are not visible.",
  "repair": "Move the full-width figure before the results subsection.",
  "confidence": "high",
  "verification": "Rebuilt; inspected p.5–9; other mentions and Table 2 remain usable."
}
```

Quotes must come from the actual input; this illustrative schema is not evidence. Use `candidate` until ambiguity is resolved. Use `fixed` only after inspecting the new artifact. If a recommendation was not applied, say so.

## Coverage ledger example

| Family | Status | Evidence |
|---|---|---|
| Figure proximity | checked | All 6 figures matched; 14 mentions inspected |
| Equation fit | checked | Pages 2–8 inspected; build log checked |
| Data-series completeness | not_checked | Plot data unavailable |
| Tagged reading order | not_checked | No tag inspection performed |
| End-matter proximity | exempted | Submission template requires figures at end |

For a focused task, report only relevant checks and their limits. For a full audit, a concise ledger may group catalog families, but cannot imply checks that were never performed.

Prefer a short summary plus linked evidence over dumping every measurement. Suggested summary: “Fixed two clipped labels and moved Figure 3 beside its explanation. A table split remains a candidate. Checked all 12 pages; source plot-data completeness was not evaluated.”
