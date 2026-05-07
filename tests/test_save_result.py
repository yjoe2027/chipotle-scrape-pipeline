import pytest
from pathlib import Path
from scrape_pipeline import slugify, save_result


# --- slugify ---

def test_slugify_lowercases():
    assert slugify("Chipotle Investor Relations") == "chipotle-investor-relations"


def test_slugify_removes_special_chars():
    assert slugify("Q1 2025: Earnings & Press Release!") == "q1-2025-earnings-press-release"


def test_slugify_truncates_before_slugifying():
    long_title = "a" * 70
    result = slugify(long_title)
    assert result == "a" * 60


def test_slugify_collapses_whitespace_and_hyphens():
    assert slugify("foo  --  bar") == "foo-bar"


def test_slugify_strips_leading_trailing_hyphens():
    assert slugify("!hello world!") == "hello-world"


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
