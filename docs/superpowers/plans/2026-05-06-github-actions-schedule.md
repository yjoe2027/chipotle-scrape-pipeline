# GitHub Actions Scheduled Scrape Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a weekly GitHub Actions workflow that runs `scrape_pipeline.py`, saves results to a date-stamped subdirectory, and commits them back to `main`.

**Architecture:** Two changes — (1) a one-line edit to `scrape_pipeline.py` so output goes to `knowledge/raw/YYYY-MM-DD/`, and (2) a new `.github/workflows/scrape.yml` with a `test` job (gates the API call) and a `scrape` job (runs the pipeline, commits, and pushes with `GITHUB_TOKEN`).

**Tech Stack:** GitHub Actions, Python 3.14, pytest, `requests`, `python-dotenv`

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `scrape_pipeline.py` | Modify line 11 | Change `OUT_DIR` to include today's ISO date |
| `tests/test_save_result.py` | Modify | Add one test asserting `OUT_DIR` ends with today's date |
| `.github/workflows/scrape.yml` | Create | Weekly schedule workflow with `test` + `scrape` jobs |

---

### Task 1: Date-stamp the output directory

**Files:**
- Modify: `scrape_pipeline.py:11`
- Modify: `tests/test_save_result.py` (append one test at the end)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_save_result.py`:

```python
import datetime

def test_out_dir_includes_today():
    import scrape_pipeline
    today = datetime.date.today().isoformat()
    assert scrape_pipeline.OUT_DIR.parts[-1] == today
```

- [ ] **Step 2: Run it to confirm it fails**

```bash
pytest tests/test_save_result.py::test_out_dir_includes_today -v
```

Expected output: `FAILED` — `AssertionError` because `OUT_DIR.parts[-1]` is currently `"raw"`, not today's date.

- [ ] **Step 3: Update `OUT_DIR` in `scrape_pipeline.py`**

Change line 11 from:

```python
OUT_DIR = Path("knowledge/raw")
```

to:

```python
OUT_DIR = Path("knowledge/raw") / datetime.date.today().isoformat()
```

`datetime` is already imported on line 4 — no new import needed.

- [ ] **Step 4: Run the full test suite to confirm everything passes**

```bash
pytest -v
```

Expected output: all tests pass. The existing `save_result` tests use `monkeypatch.setattr("scrape_pipeline.OUT_DIR", tmp_path)` so they are unaffected by the `OUT_DIR` change.

- [ ] **Step 5: Commit**

```bash
git add scrape_pipeline.py tests/test_save_result.py
git commit -m "feat: write scrape output to date-stamped subdirectory"
```

---

### Task 2: Create the GitHub Actions workflow

**Files:**
- Create: `.github/workflows/scrape.yml`

- [ ] **Step 1: Create the workflow directory and file**

```bash
mkdir -p .github/workflows
```

Create `.github/workflows/scrape.yml` with this exact content:

```yaml
name: Weekly Scrape

on:
  schedule:
    - cron: '0 6 * * 1'
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest

      - name: Run tests
        run: pytest

  scrape:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run scrape pipeline
        run: python scrape_pipeline.py
        env:
          FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}

      - name: Commit and push results
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add knowledge/raw/
          git diff --staged --quiet || git commit -m "chore: weekly scrape $(date -u +%Y-%m-%d)"
          git push origin main
```

- [ ] **Step 2: Validate the YAML is well-formed**

```bash
python -c "
import yaml, sys
with open('.github/workflows/scrape.yml') as f:
    doc = yaml.safe_load(f)
print('jobs:', list(doc['jobs'].keys()))
print('cron:', doc['on']['schedule'][0]['cron'])
"
```

Expected output:
```
jobs: ['test', 'scrape']
cron: 0 6 * * 1
```

Note: if `pyyaml` is not installed locally run `pip install pyyaml` first (it is not a runtime dep — this is a local sanity check only).

- [ ] **Step 3: Add the `FIRECRAWL_API_KEY` secret to GitHub**

Go to: **GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

- Name: `FIRECRAWL_API_KEY`
- Value: the key from your local `.env` file

This step is manual and has no automated verification — confirm the secret appears in the list before proceeding.

- [ ] **Step 4: Commit the workflow file**

```bash
git add .github/workflows/scrape.yml
git commit -m "feat: add weekly GitHub Actions scrape workflow"
```

- [ ] **Step 5: Push and trigger a manual test run**

```bash
git push origin main
```

Then go to: **GitHub repo → Actions → Weekly Scrape → Run workflow** and trigger it manually via `workflow_dispatch`. Confirm both the `test` and `scrape` jobs go green, and that a new commit appears on `main` with files under `knowledge/raw/YYYY-MM-DD/`.
