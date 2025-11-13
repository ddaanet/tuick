"""Errorformat integration for parsing tool output."""

import json
import re
import shutil
import subprocess
import typing
from dataclasses import dataclass, replace

from tuick.ansi import strip_ansi
from tuick.tool_registry import (
    BUILTIN_TOOLS,
    CUSTOM_PATTERNS,
    OVERRIDE_PATTERNS,
)

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


class ErrorformatNotFoundError(Exception):
    """Errorformat CLI not found."""

    def __init__(self) -> None:  # noqa: D107
        super().__init__(
            "errorformat not found. Install with:\n"
            "  go install github.com/reviewdog/errorformat/cmd/"
            "errorformat@latest"
        )


@dataclass
class ErrorformatEntry:
    """Parsed entry from errorformat JSONL output."""

    filename: str
    lnum: int | None
    col: int | None
    end_lnum: int | None
    end_col: int | None
    lines: list[str]
    text: str
    type: str
    valid: bool


def run_errorformat(
    tool: str, input_lines: Iterable[str]
) -> Iterator[ErrorformatEntry]:
    """Run errorformat subprocess, yield parsed entries.

    Args:
        tool: Tool name (mypy, etc.)
        input_lines: Tool output lines (with ANSI codes)

    Yields:
        ErrorformatEntry objects

    Raises:
        ErrorformatNotFoundError: If errorformat not in PATH
        subprocess.CalledProcessError: If errorformat fails
    """
    if shutil.which("errorformat") is None:
        raise ErrorformatNotFoundError

    # Build errorformat command based on tool configuration
    cmd = ["errorformat", "-w=jsonl"]
    if tool in OVERRIDE_PATTERNS:
        cmd.extend(OVERRIDE_PATTERNS[tool])
    elif tool in CUSTOM_PATTERNS:
        cmd.extend(CUSTOM_PATTERNS[tool])
    elif tool in BUILTIN_TOOLS:
        cmd.append(f"-name={tool}")
    else:
        msg = f"Unknown tool: {tool} (is_known_tool() should be checked first)"
        raise AssertionError(msg)
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    input_text = "".join(input_lines)
    stdout, stderr = proc.communicate(input_text)

    if proc.returncode != 0:
        raise subprocess.CalledProcessError(
            proc.returncode, cmd, stderr=stderr
        )

    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            yield ErrorformatEntry(
                filename=data.get("filename", ""),
                lnum=data.get("lnum") or None,
                col=data.get("col") or None,
                end_lnum=data.get("end_lnum") or None,
                end_col=data.get("end_col") or None,
                lines=data.get("lines", []),
                text=data.get("text", ""),
                type=data.get("type", ""),
                valid=data.get("valid", False),
            )
        except json.JSONDecodeError:
            continue


def group_entries_by_location(  # noqa: C901, PLR0912
    entries: Iterable[ErrorformatEntry],
) -> Iterator[ErrorformatEntry]:
    """Group errorformat entries by location.

    Notes (entries without line numbers) are merged with following errors from
    the same file. Entries with the same (filename, lnum, col) are grouped
    together.
    """
    pending_note: ErrorformatEntry | None = None
    pending_block: ErrorformatEntry | None = None

    for entry in entries:
        if not entry.lnum:
            # Context note entry - buffer or replace
            if pending_note and pending_note.filename != entry.filename:
                # Different file - keep only the new note.
                # That should not happen, being defensive.
                yield pending_note
                pending_note = entry
            elif pending_note:
                # Same file - merge
                pending_note = replace(
                    pending_note, lines=pending_note.lines + entry.lines
                )
            else:
                pending_note = entry
        else:
            # Location entry
            if pending_note:
                if pending_note.filename != entry.filename:
                    # Pending note does not match file, flush
                    yield pending_note
                else:
                    # Pending note with matching file, swallow
                    entry = replace(  # noqa: PLW2901
                        entry, lines=pending_note.lines + entry.lines
                    )
                pending_note = None

            loc = (entry.filename, entry.lnum, entry.col)
            pending_loc = (
                (pending_block.filename, pending_block.lnum, pending_block.col)
                if pending_block
                else None
            )

            if pending_loc == loc:
                # Same location - merge
                assert pending_block is not None
                pending_block = replace(
                    pending_block, lines=pending_block.lines + entry.lines
                )
            else:
                # New location - flush pending block
                if pending_block:
                    yield pending_block
                # Start new block, attach note if same file
                if pending_note and pending_note.filename == entry.filename:
                    pending_block = replace(
                        entry, lines=pending_note.lines + entry.lines
                    )
                    pending_note = None
                else:
                    pending_block = entry

    # Flush remaining
    if pending_block:
        yield pending_block
    if pending_note:
        yield pending_note


def format_block_from_entry(entry: ErrorformatEntry) -> str:
    r"""Format errorformat entry as tuick block.

    Block format: file\x1fline\x1fcol\x1fend-line\x1fend-col\x1ftext\0
    """
    text = "\n".join(entry.lines)
    line_str = str(entry.lnum) if entry.lnum is not None else ""
    col_str = str(entry.col) if entry.col is not None else ""
    return f"{entry.filename}\x1f{line_str}\x1f{col_str}\x1f\x1f\x1f{text}\0"


def parse_with_errorformat(tool: str, lines: Iterable[str]) -> Iterator[str]:
    """Parse tool output with errorformat, yield block chunks.

    Args:
        tool: Tool name matching errorformat -name option
        lines: Tool output lines (may contain ANSI codes)

    Yields:
        Null-terminated block chunks (with ANSI codes preserved)
    """
    # Build mapping from stripped lines to original (with ANSI) while streaming
    stripped_to_original: dict[str, str] = {}

    def strip_and_track(lines: Iterable[str]) -> Iterator[str]:
        """Strip ANSI codes and track mapping while streaming."""
        for line in lines:
            stripped = strip_ansi(line)
            stripped_to_original[stripped.rstrip("\n")] = line.rstrip("\n")
            yield stripped

    # Parse with errorformat using stripped lines
    entries = run_errorformat(tool, strip_and_track(lines))

    # Group entries by location (merges notes with errors)
    if tool == "mypy":
        entries = group_entries_by_location(entries)

    for entry in entries:
        # Restore original colored lines from mapping
        entry.lines = [
            stripped_to_original.get(line, line) for line in entry.lines
        ]
        yield format_block_from_entry(entry)


def split_at_markers(lines: Iterable[str]) -> Iterator[tuple[bool, str]]:
    r"""Split lines at \x02 and \x03 markers.

    Yields:
        (is_nested, content) tuples where is_nested indicates if content
        came from between markers (True) or outside markers (False).
    """
    text = "".join(lines)
    parts = re.split(r"(\x02|\x03)", text)
    in_nested = False

    for part in parts:
        if part == "\x02":
            in_nested = True
        elif part == "\x03":
            in_nested = False
        elif part:  # Non-empty content
            yield (in_nested, part)


def wrap_blocks_with_markers(blocks: Iterable[str]) -> Iterator[str]:
    r"""Wrap blocks with \x02 and \x03 markers."""
    yield "\x02"
    yield from blocks
    yield "\x03"
