# Design: Save Firecrawl Results as Markdown Files

**Date:** 2026-05-06  
**Scope:** Extend `scrape_pipeline.py` to persist each Firecrawl search result as a markdown file under `knowledge/raw/`.

---

## Approach

Inline Option A: add a `save_result()` helper function in `scrape_pipeline.py` and call it inside the existing `for r in results` loop. No new files or modules.

---

## File Naming

- Pattern: `{idx:02d}-{slug}.md`
- Slug derived from the result title: lowercase, non-alphanumeric chars removed, whitespace/hyphens collapsed to single `-`, truncated to 60 characters before slugifying.
- Examples:
  - `01-chipotle-mexican-grill-investor-relations.md`
  - `02-q1-2025-earnings-press-release.md`
- Output directory: `knowledge/raw/`, created with `mkdir -p` if absent.

---

## File Contents

Each file contains a YAML front-matter block followed by the raw Firecrawl markdown:

```
---
title: "<result title>"
url: "<result url>"
scraped_at: "YYYY-MM-DD"
---

<markdown body>
```

`scraped_at` is `datetime.date.today()` in ISO format. No additional dependencies.

---

## Control Flow

Changes are confined to the existing `for r in results` loop:

1. **Guard clause:** if `r.get('markdown')` is falsy, print a warning (`WARNING: no markdown for "{title}" ({url}) — skipping`) and `continue`.
2. **Save call:** call `save_result(idx, r)`, which builds the filename, writes the file, and prints `Saved: knowledge/raw/<filename>`.

`save_result(idx, result)` is defined just above the loop. It handles slug generation, front-matter assembly, directory creation, and file writing. Returns nothing.

No changes to the API call, headers, or payload.

---

## Out of Scope

- Deduplication across runs
- Subdirectory organisation by date or query
- Post-processing or transformation of markdown content
