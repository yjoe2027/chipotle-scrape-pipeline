# Design: GitHub Actions Scheduled Scrape Workflow

**Date:** 2026-05-06
**Status:** Approved

## Overview

Add a GitHub Actions workflow that runs the Firecrawl scrape pipeline on a weekly schedule, commits the output files back to `main`, and gates the scrape behind the existing test suite.

## Trigger

File: `.github/workflows/scrape.yml`

Two triggers:
- `schedule`: `cron: '0 6 * * 1'` — every Monday at 06:00 UTC
- `workflow_dispatch` — manual trigger from the Actions UI

## Jobs

Both jobs run on `ubuntu-latest`.

### `test`

1. Checkout repo
2. Set up Python 3.14
3. `pip install -r requirements.txt`
4. `pytest`

### `scrape`

Runs only if `test` passes (`needs: test`).

1. Checkout repo
2. Set up Python 3.14
3. `pip install -r requirements.txt`
4. `python scrape_pipeline.py` — with `FIRECRAWL_API_KEY` injected from a repository secret
5. Configure git bot identity
6. `git add knowledge/raw/`
7. Commit (skipped if nothing staged): `git commit -m "chore: weekly scrape $(date -u +%Y-%m-%d)"`
8. `git push origin main` using the built-in `GITHUB_TOKEN`

## Secret

`FIRECRAWL_API_KEY` must be added once under **Settings → Secrets and variables → Actions** in the GitHub repo. It is injected into the scrape step via `env:`.

No extra secret is needed for the push — `GITHUB_TOKEN` is provided automatically by Actions. The `scrape` job must declare `permissions: contents: write`; without it the default token is read-only and the push will fail.

## Script change

`scrape_pipeline.py` line 11 changes from:

```python
OUT_DIR = Path("knowledge/raw")
```

to:

```python
OUT_DIR = Path("knowledge/raw") / datetime.date.today().isoformat()
```

`datetime` is already imported. Each run writes to a date-stamped subdirectory, e.g. `knowledge/raw/2026-05-11/`, so results accumulate week over week rather than overwriting.

## Error handling

- If `pytest` fails, the scrape job is skipped entirely — no Firecrawl credits consumed.
- If the scrape produces no new files (Firecrawl returns identical results), the `git diff --staged --quiet` guard skips the commit and push cleanly.
- If `scrape_pipeline.py` exits non-zero, the subsequent git steps are skipped and the workflow reports failure.

## Files changed

| File | Change |
|---|---|
| `.github/workflows/scrape.yml` | New file |
| `scrape_pipeline.py` | One-line change to `OUT_DIR` |
