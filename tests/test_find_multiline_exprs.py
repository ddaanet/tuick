"""Tests for scripts/find_multiline_exprs.py."""

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from find_multiline_exprs import (
    ClosingDelimiter,
    filter_outermost,
    find_opener,
    main,
    output_context,
    parse_diff,
)

if TYPE_CHECKING:
    import pytest

# Iteration 1 Tests: Parse git diff - Find closing delimiters


def test_parse_diff_single_closing_paren() -> None:
    """parse_diff finds closing paren at line start in added line."""
    diff = """\
diff --git a/test1.py b/test1.py
index 06fbfd9..6e60bf4 100644
--- a/test1.py
+++ b/test1.py
@@ -1,0 +2,3 @@
+def foo(
+    x
+)
"""
    delimiters = list(parse_diff(diff))
    # Closing paren is at line 4 (2 + 3 - 1), indent 0
    expected = [ClosingDelimiter("test1.py", 4, 0, ")")]
    assert delimiters == expected


def test_parse_diff_closing_bracket_with_indent() -> None:
    """parse_diff captures indentation of closing bracket."""
    diff = """\
diff --git a/test2.py b/test2.py
index 2ae2839..3a7d160 100644
--- a/test2.py
+++ b/test2.py
@@ -0,0 +1,4 @@
+items = [
+    1, 2,
+    3
+    ]
"""
    delimiters = list(parse_diff(diff))
    # Closing bracket is at line 4, indent 4
    expected = [ClosingDelimiter("test2.py", 4, 4, "]")]
    assert delimiters == expected


def test_parse_diff_skip_non_python_files() -> None:
    """parse_diff ignores non-.py files."""
    diff = """\
diff --git a/test3.md b/test3.md
index 8ae0569..c3ddfa6 100644
--- a/test3.md
+++ b/test3.md
@@ -1,0 +2 @@
+)
"""
    delimiters = list(parse_diff(diff))
    assert delimiters == []


def test_parse_diff_multiple_files_and_delimiters() -> None:
    """parse_diff finds all delimiters across multiple files."""
    diff = """\
diff --git a/test4a.py b/test4a.py
index 2ae2839..08f62f9 100644
--- a/test4a.py
+++ b/test4a.py
@@ -0,0 +1,2 @@
+foo(
+)
diff --git a/test4b.py b/test4b.py
index 2ae2839..51e15be 100644
--- a/test4b.py
+++ b/test4b.py
@@ -0,0 +1,2 @@
+bar[
+]
"""
    delimiters = list(parse_diff(diff))
    # test4a.py closing paren at line 2, indent 0
    # test4b.py closing bracket at line 2, indent 0
    expected = [
        ClosingDelimiter("test4a.py", 2, 0, ")"),
        ClosingDelimiter("test4b.py", 2, 0, "]"),
    ]
    assert delimiters == expected


def test_parse_diff_multiple_chunks() -> None:
    """parse_diff tracks line numbers correctly across multiple chunks."""
    diff = """\
diff --git a/test5.py b/test5.py
index 086e798..2580cae 100644
--- a/test5.py
+++ b/test5.py
@@ -5,0 +6,2 @@ def existing():
+foo(
+)
@@ -19,0 +22,2 @@ def another():
+bar(
+)
"""
    delimiters = list(parse_diff(diff))
    # First closing paren: chunk starts at line 6, paren at line 7
    # Second closing paren: chunk starts at line 22, paren at line 23
    expected = [
        ClosingDelimiter("test5.py", 7, 0, ")"),
        ClosingDelimiter("test5.py", 23, 0, ")"),
    ]
    assert delimiters == expected


def test_parse_diff_ignore_delimiter_not_at_end() -> None:
    """parse_diff ignores delimiters not at end of line."""
    diff = """\
diff --git a/test6.py b/test6.py
index 2ae2839..a6bfd8d 100644
--- a/test6.py
+++ b/test6.py
@@ -0,0 +1,2 @@
+) and more
+    ]  # comment
"""
    delimiters = list(parse_diff(diff))
    # These should be ignored because delimiter is not at line end
    assert delimiters == []


# Iteration 2 Tests: Filter to outermost delimiters


def test_filter_outermost_nested_delimiters() -> None:
    """filter_outermost keeps only outermost delimiter."""
    delimiters = [
        ClosingDelimiter("test.py", 10, 8, ")"),  # nested
        ClosingDelimiter("test.py", 11, 4, ")"),  # nested
        ClosingDelimiter("test.py", 12, 0, ")"),  # outermost
    ]
    result = list(filter_outermost(delimiters))
    expected = [ClosingDelimiter("test.py", 12, 0, ")")]
    assert result == expected


def test_filter_outermost_same_indent_level() -> None:
    """filter_outermost keeps all delimiters at minimum indent."""
    delimiters = [
        ClosingDelimiter("test.py", 10, 0, ")"),
        ClosingDelimiter("test.py", 15, 0, "]"),
        ClosingDelimiter("test.py", 20, 0, "}"),
    ]
    result = list(filter_outermost(delimiters))
    assert result == delimiters  # All kept


def test_filter_outermost_non_contiguous_blocks() -> None:
    """filter_outermost treats gaps >1 line as separate blocks."""
    delimiters = [
        # Block 1: lines 10-12 (keep line 12)
        ClosingDelimiter("test.py", 10, 4, ")"),
        ClosingDelimiter("test.py", 12, 0, ")"),
        # Block 2: lines 20-22 (keep line 22)
        ClosingDelimiter("test.py", 20, 4, ")"),
        ClosingDelimiter("test.py", 22, 0, ")"),
    ]
    result = list(filter_outermost(delimiters))
    expected = [
        ClosingDelimiter("test.py", 12, 0, ")"),
        ClosingDelimiter("test.py", 22, 0, ")"),
    ]
    assert result == expected


def test_filter_outermost_multiple_files() -> None:
    """filter_outermost processes each file independently."""
    delimiters = [
        ClosingDelimiter("a.py", 10, 4, ")"),
        ClosingDelimiter("a.py", 12, 0, ")"),
        ClosingDelimiter("b.py", 10, 4, "]"),
        ClosingDelimiter("b.py", 12, 0, "]"),
    ]
    result = list(filter_outermost(delimiters))
    expected = [
        ClosingDelimiter("a.py", 12, 0, ")"),
        ClosingDelimiter("b.py", 12, 0, "]"),
    ]
    assert result == expected


# Iteration 3 Tests: Find matching opening delimiter


def test_find_opener_previous_line() -> None:
    """find_opener finds opener on previous line."""
    lines = ["foo(", ")"]
    opener_line = find_opener(lines, close_line=1, closer=")")
    assert opener_line == 0


def test_find_opener_several_lines_back() -> None:
    """find_opener finds opener across multiple lines."""
    lines = [
        "result = calculate(",
        "    x,",
        "    y,",
        "    z",
        ")",
    ]
    opener_line = find_opener(lines, close_line=4, closer=")")
    assert opener_line == 0


def test_find_opener_nested_delimiters() -> None:
    """find_opener matches correct opener for nested delimiters."""
    lines = [
        "outer(",
        "    inner(",
        "        x",
        "    )",
        ")",
    ]
    # Find opener for closing paren at line 4
    opener_line = find_opener(lines, close_line=4, closer=")")
    assert opener_line == 0  # Matches "outer(", not "inner("


def test_find_opener_mixed_delimiters() -> None:
    """find_opener handles multiple delimiter types."""
    lines = [
        "foo([",
        "    {",
        "        'key': 'value'",
        "    }",
        "])",
    ]
    # Find opener for closing bracket at line 4
    opener_line = find_opener(lines, close_line=4, closer="]")
    assert opener_line == 0  # Matches "[" from line 0


def test_find_opener_no_match() -> None:
    """find_opener returns None when no matching opener found."""
    lines = ["x = 5", ")"]
    opener_line = find_opener(lines, close_line=1, closer=")")
    assert opener_line is None


# Iteration 4 Tests: Read file and output context


def test_output_context_basic(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """output_context prints header and numbered lines."""
    test_file = tmp_path / "test.py"
    test_file.write_text("line1\nline2\nline3\nline4\nline5\n")

    # Opener at line 2 (0-indexed: 1), closer at line 5 (0-indexed: 4)
    # With CONTEXT_LINES=5, start = max(1, 2-5) = 1, so includes line1
    output_context(str(test_file), close_idx=4, opener_idx=1)

    captured = capsys.readouterr()
    expected = """\
=== test.py:1-5 ===
   1: line1
   2: line2
   3: line3
   4: line4
   5: line5
"""
    assert captured.out == expected


def test_output_context_with_context_lines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """output_context includes CONTEXT_LINES before opener."""
    test_file = tmp_path / "test.py"
    lines = [f"line{i}\n" for i in range(1, 21)]
    test_file.write_text("".join(lines))

    # Opener at line 10 (0-indexed: 9), closer at line 15 (0-indexed: 14)
    # Context should include lines 5-15 (5 lines before opener)
    output_context(str(test_file), close_idx=14, opener_idx=9)

    captured = capsys.readouterr()
    lines_out = captured.out.splitlines()

    # Check header
    assert lines_out[0] == "=== test.py:5-15 ==="

    # Check first content line (line 5, 1-indexed)
    assert lines_out[1] == "   5: line5"

    # Check last content line (line 15, 1-indexed)
    assert lines_out[-1] == "  15: line15"


def test_output_context_start_of_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """output_context handles files shorter than CONTEXT_LINES."""
    test_file = tmp_path / "test.py"
    test_file.write_text("foo(\n)\n")

    # Opener at line 1 (0-indexed: 0), closer at line 2 (0-indexed: 1)
    output_context(str(test_file), close_idx=1, opener_idx=0)

    captured = capsys.readouterr()
    expected = """\
=== test.py:1-2 ===
   1: foo(
   2: )
"""
    assert captured.out == expected


# Iteration 5 Tests: Main function and git integration


def test_main_integration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Main() integrates all components with git diff."""
    # Create a git repo with a commit containing multi-line expression
    repo = tmp_path / "repo"
    repo.mkdir()
    test_file = repo / "test.py"

    # Setup git repo
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    test_file.write_text("# Initial\n")
    subprocess.run(
        ["git", "add", "."], cwd=repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Add multi-line expression
    test_file.write_text("# Initial\nresult = calculate(\n    x,\n    y\n)\n")

    # Change to repo directory
    monkeypatch.chdir(repo)

    # Run main()
    main()

    captured = capsys.readouterr()

    # Verify output includes the multi-line expression
    assert "=== test.py:" in captured.out
    assert "calculate(" in captured.out
    assert ")" in captured.out
