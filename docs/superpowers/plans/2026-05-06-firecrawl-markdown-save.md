# Firecrawl Markdown Save Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `scrape_pipeline.py` to save each Firecrawl search result as a numbered, slugified markdown file with YAML front-matter under `knowledge/raw/`.

**Architecture:** Add two helper functions (`slugify`, `save_result`) to `scrape_pipeline.py` above the main loop, wrap the script body in `if __name__ == "__main__":` so the helpers are importable for testing, and add a guard clause in the loop that warns and skips results with no markdown.

**Tech Stack:** Python 3, stdlib only (`re`, `datetime`, `pathlib`). Tests use `pytest` with `tmp_path` and `monkeypatch` fixtures.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `scrape_pipeline.py` | Add `OUT_DIR`, `slugify()`, `save_result()`, `if __name__` guard, loop changes |
| Create | `tests/test_save_result.py` | Unit tests for `slugify` and `save_result` |

---

### Task 1: Make `scrape_pipeline.py` importable without executing

Wrap everything from `api_key = ...` to the end of the file in `if __name__ == "__main__":`. This lets tests import `slugify` and `save_result` without triggering a live API call. `load_dotenv()` stays at module level (safe — just reads a file).

**Files:**
- Modify: `scrape_pipeline.py`

- [ ] **Step 1: Apply the refactor**

Replace the contents of `scrape_pipeline.py` with:

```python
import os
import re
import time
import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()

OUT_DIR = Path("knowledge/raw")


def slugify(text: str, max_len: int = 60) -> str:
    text = text[:max_len].lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text).strip('-')
    return text


def save_result(idx: int, result: dict) -> None:
    slug = slugify(result['title'])
    filename = f"{idx:02d}-{slug}.md"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / filename
    scraped_at = datetime.date.today().isoformat()
    front_matter = (
        f'---\n'
        f'title: "{result["title"]}"\n'
        f'url: "{result["url"]}"\n'
        f'scraped_at: "{scraped_at}"\n'
        f'---\n\n'
    )
    path.write_text(front_matter + result['markdown'])
    print(f"Saved: {path}")


if __name__ == "__main__":
    api_key = os.getenv("FIRECRAWL_API_KEY")

    api_url = "https://api.firecrawl.dev/v2/search"

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "query": "Chipotle investor relations press releases",
        "limit": 5,
        "scrapeOptions": {"formats": ["markdown"]}
    }

    response = requests.post(api_url, headers=headers, json=payload)

    data = response.json()
    results = data["data"]["web"]
    print(f"Firecrawl returned {len(results)} results")

    for idx, r in enumerate(results, start=1):
        title = r.get('title', '')
        url = r.get('url', '')
        if not r.get('markdown'):
            print(f'WARNING: no markdown for "{title}" ({url}) — skipping')
            continue
        save_result(idx, r)
```

- [ ] **Step 2: Verify the script still runs without error (dry import)**

```bash
.venv/bin/python -c "import scrape_pipeline; print('import OK')"
```

Expected output:
```
import OK
```

- [ ] **Step 3: Commit**

```bash
git add scrape_pipeline.py
git commit -m "refactor: wrap script body in __main__ guard, add slugify and save_result"
```

---

### Task 2: Write and pass tests for `slugify`

**Files:**
- Create: `tests/test_save_result.py`

- [ ] **Step 1: Create the tests directory and test file**

```bash
mkdir -p tests
```

Create `tests/test_save_result.py` with:

```python
import pytest
from pathlib import Path
from scrape_pipeline import slugify, save_result


# --- slugify ---

def test_slugify_lowercases():
    assert slugify("Chipotle Investor Relations") == "chipotle-investor-relations"


def test_slugify_removes_special_chars():
    assert slugify("Q1 2025: Earnings & Press Release!") == "q1-2025-earnings-press-release"


def test_slugify_truncates_before_slugifying():
    # 70-char input truncated to 60 before processing
    long_title = "a" * 70
    result = slugify(long_title)
    assert result == "a" * 60


def test_slugify_collapses_whitespace_and_hyphens():
    assert slugify("foo  --  bar") == "foo-bar"


def test_slugify_strips_leading_trailing_hyphens():
    assert slugify("!hello world!") == "hello-world"
```

- [ ] **Step 2: Run tests — expect them to pass**

```bash
.venv/bin/pytest tests/test_save_result.py -k "slugify" -v
```

Expected output (all PASSED):
```
tests/test_save_result.py::test_slugify_lowercases PASSED
tests/test_save_result.py::test_slugify_removes_special_chars PASSED
tests/test_save_result.py::test_slugify_truncates_before_slugifying PASSED
tests/test_save_result.py::test_slugify_collapses_whitespace_and_hyphens PASSED
tests/test_save_result.py::test_slugify_strips_leading_trailing_hyphens PASSED
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_save_result.py
git commit -m "test: add slugify unit tests"
```

---

### Task 3: Write and pass tests for `save_result`

**Files:**
- Modify: `tests/test_save_result.py`

- [ ] **Step 1: Append `save_result` tests to `tests/test_save_result.py`**

Add these test functions at the bottom of the file:

```python
# --- save_result ---

def test_save_result_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr("scrape_pipeline.OUT_DIR", tmp_path)
    result = {
        "title": "Chipotle Investor Relations",
        "url": "https://ir.chipotle.com/",
        "markdown": "# Hello\nContent here."
    }
    save_result(1, result)
    expected = tmp_path / "01-chipotle-investor-relations.md"
    assert expected.exists()


def test_save_result_zero_pads_index(tmp_path, monkeypatch):
    monkeypatch.setattr("scrape_pipeline.OUT_DIR", tmp_path)
    result = {
        "title": "Test",
        "url": "https://example.com",
        "markdown": "body"
    }
    save_result(3, result)
    assert (tmp_path / "03-test.md").exists()


def test_save_result_front_matter_fields(tmp_path, monkeypatch):
    monkeypatch.setattr("scrape_pipeline.OUT_DIR", tmp_path)
    result = {
        "title": "My Title",
        "url": "https://example.com/page",
        "markdown": "body text"
    }
    save_result(1, result)
    content = (tmp_path / "01-my-title.md").read_text()
    assert content.startswith("---\n")
    assert 'title: "My Title"' in content
    assert 'url: "https://example.com/page"' in content
    assert 'scraped_at: "' in content


def test_save_result_markdown_body_appended(tmp_path, monkeypatch):
    monkeypatch.setattr("scrape_pipeline.OUT_DIR", tmp_path)
    result = {
        "title": "Foo",
        "url": "https://foo.com",
        "markdown": "## Section\nSome content."
    }
    save_result(1, result)
    content = (tmp_path / "01-foo.md").read_text()
    assert "## Section\nSome content." in content


def test_save_result_creates_output_dir(tmp_path, monkeypatch):
    nested = tmp_path / "knowledge" / "raw"
    monkeypatch.setattr("scrape_pipeline.OUT_DIR", nested)
    result = {
        "title": "Dir Test",
        "url": "https://example.com",
        "markdown": "content"
    }
    save_result(1, result)
    assert nested.exists()
    assert (nested / "01-dir-test.md").exists()
```

- [ ] **Step 2: Run the new tests — expect all to pass**

```bash
.venv/bin/pytest tests/test_save_result.py -v
```

Expected output (all PASSED):
```
tests/test_save_result.py::test_slugify_lowercases PASSED
tests/test_save_result.py::test_slugify_removes_special_chars PASSED
tests/test_save_result.py::test_slugify_truncates_before_slugifying PASSED
tests/test_save_result.py::test_slugify_collapses_whitespace_and_hyphens PASSED
tests/test_save_result.py::test_slugify_strips_leading_trailing_hyphens PASSED
tests/test_save_result.py::test_save_result_creates_file PASSED
tests/test_save_result.py::test_save_result_zero_pads_index PASSED
tests/test_save_result.py::test_save_result_front_matter_fields PASSED
tests/test_save_result.py::test_save_result_markdown_body_appended PASSED
tests/test_save_result.py::test_save_result_creates_output_dir PASSED
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_save_result.py
git commit -m "test: add save_result unit tests"
```

---

### Task 4: Smoke-test the full pipeline end-to-end

Verify the script actually writes files when run with a real API key.

**Files:**
- No changes — read-only verification step.

- [ ] **Step 1: Run the pipeline**

```bash
.venv/bin/python scrape_pipeline.py
```

Expected output (exact titles will vary):
```
Firecrawl returned 5 results
Saved: knowledge/raw/01-<slug>.md
Saved: knowledge/raw/02-<slug>.md
...
```

Any result without markdown should print:
```
WARNING: no markdown for "<title>" (<url>) — skipping
```

- [ ] **Step 2: Confirm files exist and contain front-matter**

```bash
ls knowledge/raw/
head -6 knowledge/raw/01-*.md
```

Expected `head` output:
```
---
title: "..."
url: "..."
scraped_at: "2026-05-06"
---
```

- [ ] **Step 3: Commit the generated files (optional)**

Only commit if the course/project expects raw data to be tracked in git. If `knowledge/raw/` is in `.gitignore`, skip this step.

```bash
git add knowledge/raw/
git commit -m "data: add initial Firecrawl raw markdown results"
```
