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
