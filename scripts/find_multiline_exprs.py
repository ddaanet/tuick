#!/usr/bin/env python3
"""Find outermost closing delimiters at line start in git diff, output context.

Usage:
    uv run --dev scripts/find_multiline_exprs.py

This script analyzes the current git diff to find multi-line expressions that
might benefit from compaction. It identifies closing delimiters at line start,
filters to outermost only, and outputs context for analysis.
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Iterator

# Constants
FILE_HEADER = re.compile(r"^diff --git a/.+ b/(.+\.py)$")
CHUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
CLOSING_LINE = re.compile(r"^\+(\s*)([)\]}])\s*$")
OPENERS: dict[str, str] = {")": "(", "]": "[", "}": "{"}
CONTEXT_LINES: int = 5
CONTIGUITY_THRESHOLD = 5  # Max line gap within a block


class ClosingDelimiter(NamedTuple):
    """A closing delimiter found in a git diff."""

    filepath: str  # Path to .py file (e.g., "src/tuick/cli.py")
    line_no: int  # 1-indexed line number in file
    indent: int  # Number of leading spaces
    closer: str  # Closing char: ')', ']', or '}'


class DiffBlock(NamedTuple):
    """A contiguous sequence of closing delimiters in one file."""

    filepath: str
    delimiters: list[ClosingDelimiter]  # Sorted by line_no descending


def parse_diff(diff_text: str) -> Iterator[ClosingDelimiter]:
    """Parse git diff, yield closing delimiters in added Python lines."""
    current_file: str | None = None
    current_line = 0

    for line in diff_text.splitlines():
        # Skip --- and +++ file marker lines
        if line.startswith(("---", "+++")):
            continue

        # Match file header
        if match := FILE_HEADER.match(line):
            current_file = match[1]
            continue

        # Match chunk header to get line number
        if match := CHUNK_HEADER.match(line):
            current_line = int(match[1])
            continue

        # Skip if not in Python file
        if not current_file:
            continue

        # Check for added line with closing delimiter at line end
        if match := CLOSING_LINE.match(line):
            indent_str, closer = match.groups()
            yield ClosingDelimiter(
                current_file,
                current_line,
                len(indent_str),
                closer,
            )

        # Track line numbers for added/unchanged lines
        if line.startswith(("+", " ")):
            current_line += 1


def filter_outermost(
    delimiters: list[ClosingDelimiter],
) -> Iterator[ClosingDelimiter]:
    """Keep only outermost delimiters from contiguous blocks."""
    # Group by file
    by_file: dict[str, list[ClosingDelimiter]] = {}
    for d in delimiters:
        by_file.setdefault(d.filepath, []).append(d)

    # Collect results to maintain input order
    results: list[ClosingDelimiter] = []

    # Process each file's delimiters
    for file_delims in by_file.values():
        # Sort by line number descending for backward scan
        file_delims.sort(key=lambda d: d.line_no, reverse=True)

        # Split into contiguous blocks
        blocks: list[list[ClosingDelimiter]] = []
        current_block: list[ClosingDelimiter] = []
        prev_line: int | None = None

        for delim in file_delims:
            # Check if delimiter is within threshold of previous line
            is_contiguous = (
                prev_line is None
                or prev_line - delim.line_no <= CONTIGUITY_THRESHOLD
            )
            if is_contiguous:
                current_block.append(delim)
            else:
                if current_block:
                    blocks.append(current_block)
                current_block = [delim]
            prev_line = delim.line_no

        if current_block:
            blocks.append(current_block)

        # Filter each block to outermost
        for block in blocks:
            results.extend(_keep_outermost_in_block(block))

    # Sort results by filepath and line_no to match input order
    results.sort(key=lambda d: (d.filepath, d.line_no))
    yield from results


def _keep_outermost_in_block(
    block: list[ClosingDelimiter],
) -> Iterator[ClosingDelimiter]:
    """Keep delimiters with no subsequent delimiter at <= indent."""
    min_indent_after = float("inf")

    for delim in block:  # Already sorted descending by line_no
        if delim.indent <= min_indent_after:
            yield delim
            min_indent_after = delim.indent


def find_opener(
    lines: list[str],
    close_line: int,
    closer: str,
) -> int | None:
    """Find line number of matching opener (0-indexed).

    Returns None if not found.
    """
    opener = OPENERS[closer]
    depth = 1  # Start at 1 for the closing delimiter

    # Walk backwards from line before closer
    for line_idx in range(close_line - 1, -1, -1):
        line = lines[line_idx]

        # Count openers and closers in this line
        for char in line:
            if char == closer:
                depth += 1
            elif char == opener:
                depth -= 1
                if depth == 0:
                    return line_idx

    return None  # No matching opener found


def output_context(
    filepath: str,
    close_idx: int,
    opener_idx: int,
) -> None:
    """Output context: CONTEXT_LINES before opener through closer.

    Args:
        filepath: Path to the file
        close_idx: 0-indexed line number of closing delimiter
        opener_idx: 0-indexed line number of opening delimiter
    """
    # Calculate line range (convert to 1-indexed for display)
    opener_line = opener_idx + 1
    close_line = close_idx + 1
    start_line = max(1, opener_line - CONTEXT_LINES)
    end_line = close_line

    # Read file lines
    try:
        with Path(filepath).open() as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Warning: File not found: {filepath}", file=sys.stderr)  # noqa: T201
        return

    # Print header (use basename for cleaner output)
    filename = Path(filepath).name
    print(f"=== {filename}:{start_line}-{end_line} ===")  # noqa: T201

    # Print numbered lines
    for line_num in range(start_line, end_line + 1):
        if line_num <= len(lines):
            content = lines[line_num - 1].rstrip("\n")
            print(f"{line_num:4d}: {content}")  # noqa: T201


def main() -> None:
    """Find and output multi-line expressions in git diff."""
    # Get git diff
    result = subprocess.run(
        ["git", "diff", "--unified=0", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    diff_text = result.stdout

    # Parse diff to find closing delimiters
    all_delimiters = list(parse_diff(diff_text))

    # Filter to outermost
    outermost = list(filter_outermost(all_delimiters))

    # For each delimiter, find opener and output context
    first = True
    for delim in outermost:
        # Read file to find opener
        try:
            with Path(delim.filepath).open() as f:
                lines = f.readlines()
        except FileNotFoundError:
            continue

        # Convert to 0-indexed
        close_idx = delim.line_no - 1

        # Find opener
        opener_idx = find_opener(
            [line.rstrip("\n") for line in lines],
            close_idx,
            delim.closer,
        )

        if opener_idx is None:
            # Fallback to showing from line 1
            opener_idx = 0

        # Output context with blank line separator
        if not first:
            print()  # noqa: T201  # Blank line between blocks
        first = False
        output_context(delim.filepath, close_idx, opener_idx)


if __name__ == "__main__":
    main()
