"""Tests for errorformat integration."""

import subprocess

import pytest

from tuick.errorformat import parse_with_errorformat


@pytest.mark.skipif(
    subprocess.run(
        ["which", "errorformat"], capture_output=True, check=False
    ).returncode
    != 0,
    reason="errorformat not installed",
)
def test_parse_with_errorformat_mypy() -> None:
    """Integration test: parse mypy output with errorformat."""
    # Real mypy output from test_parser.py test data
    mypy_output = [
        "src/jobsearch/search.py:58: error: Returning Any from function...\n",
        "src/jobsearch/cadremploi_scraper.py:43:35: error: Missing type "
        'parameters for "dict"  [type-arg]\n',
        "    def extract_json_ld(html: str) -> dict | None:\n",
        "                                      ^\n",
        "tests/test_search.py:144: error: Non-overlapping equality check...\n",
        "Found 8 errors in 6 files (checked 20 source files)\n",
    ]

    result = "".join(parse_with_errorformat("mypy", iter(mypy_output)))

    # Block 1: file:line (no column)
    # Block 2: file:line:col with 2 continuation lines (multi-line)
    # Block 3: file:line (no column)
    # Block 4: informational message (no location, valid=true via %G)
    expected = (
        "src/jobsearch/search.py\x1f58\x1f\x1f\x1f\x1f"
        "src/jobsearch/search.py:58: error: Returning Any from "
        "function...\0"
        "src/jobsearch/cadremploi_scraper.py\x1f43\x1f35\x1f\x1f\x1f"
        "src/jobsearch/cadremploi_scraper.py:43:35: error: Missing type "
        'parameters for "dict"  [type-arg]\n'
        "    def extract_json_ld(html: str) -> dict | None:\n"
        "                                      ^\0"
        "tests/test_search.py\x1f144\x1f\x1f\x1f\x1f"
        "tests/test_search.py:144: error: Non-overlapping equality "
        "check...\0"
        "\x1f\x1f\x1f\x1f\x1f"
        "Found 8 errors in 6 files (checked 20 source files)\0"
    )
    assert result == expected
