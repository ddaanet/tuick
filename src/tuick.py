#!/usr/bin/env python3
"""Tuick, the Text User Interface for Compilers and checKers.

Tuick is a wrapper for compilers and checkers that integrates with fzf and your
text editor to provide fluid, keyboard-friendly, access to code error
locations.
"""

import os
import re
import shlex
import subprocess
import sys
import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

import typer
from rich.console import Console

app = typer.Typer()

err_console = Console(stderr=True)


@dataclass
class FileLocation:
    """File location with optional row and column."""

    path: str
    row: int | None = None
    column: int | None = None


class FileLocationNotFoundError(ValueError):
    """Error when location pattern not found in selection."""

    def __init__(self, selection: str) -> None:
        """Initialize with the selection text."""
        self.selection = selection
        super().__init__(f"Location pattern not found in: {selection!r}")

    def __rich__(self) -> str:
        """Rich formatted error message."""
        return (
            f"[bold red]Error:[/] Location pattern not found\n"
            f"[bold]Input:[/] {self.selection!r}"
        )


# ruff: noqa: S607 start-process-with-partial-path
# Typer API uses boolean arguments, positional values, and function calls
# in defaults
# ruff: noqa: FBT001 boolean-type-hint-positional-argument
# ruff: noqa: FBT003 boolean-positional-value-in-call
# ruff: noqa: B008 function-call-in-default-argument

# TODO: use watchexec to detect changes, and trigger fzf reload through socket

# TODO: exit when command output is empty. We cannot do that within fzf,
# because it has no event for empty input, just for zero matches.
# We need a socket connection


def quote_command(words: Iterable[str]) -> str:
    """Shell quote words and join in a single command string."""
    return " ".join(shlex.quote(x) for x in words)


@app.command()
def main(
    command: list[str] = typer.Argument(None),
    reload: bool = typer.Option(
        False, "--reload", help="Run command and output blocks"
    ),
    select: str = typer.Option(
        "", "--select", help="Open editor at error location"
    ),
) -> None:
    """Tuick: Text User Interface for Compilers and checKers."""
    if reload and select:
        err_console.print(
            "[bold red]Error:[/] "
            "[red]--reload and --select are mutually exclusive"
        )
        raise typer.Exit(1)

    if command is None:
        command = []

    if reload:
        reload_command(command)
    elif select:
        select_command(select)
    else:
        list_command(command)


def list_command(command: list[str]) -> None:
    """List errors from running COMMAND."""
    myself = sys.argv[0]
    reload_cmd = quote_command([myself, "--reload", "--", *command])
    select_cmd = quote_command([myself, "--select"])
    env = os.environ.copy()
    env["FZF_DEFAULT_COMMAND"] = reload_cmd
    result = subprocess.run(
        [
            "fzf",
            "--read0",
            "--ansi",
            "--no-sort",
            "--reverse",
            "--disabled",
            "--color=dark",
            "--highlight-line",
            "--wrap",
            "--no-input",
            "--bind",
            ",".join(
                [
                    f"enter,right:execute({select_cmd} {{}})",
                    f"r:reload({reload_cmd})",
                    "q:abort",
                    "space:down",
                    "backspace:up",
                ]
            ),
        ],
        env=env,
        text=True,
        check=False,
    )
    if result.returncode not in [0, 130]:
        # 130 means fzf was aborted with ctrl-C or ESC
        sys.exit(result.returncode)


def reload_command(command: list[str]) -> None:
    """Run COMMAND with FORCE_COLOR=1 and split output into blocks."""
    env = os.environ.copy()
    env["FORCE_COLOR"] = "1"
    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    ) as process:
        if process.stdout:
            for chunk in split_blocks(process.stdout):
                sys.stdout.write(chunk)


def split_blocks(lines: Iterable[str]) -> Iterator[str]:
    r"""Split lines into NULL-separated blocks.

    Args:
        lines: Iterable of lines with line endings preserved

    Yields:
        Chunks of the \0-separated stream
    """
    first_block = True
    pending_nl = ""
    prev_location = None
    note_path = None  # Path from most recent note line

    for line in lines:
        text, trailing_nl = (
            line.removesuffix("\n"),
            "\n" if line.endswith("\n") else "",
        )
        if not text:
            # Blank line resets state, next non-blank starts new block
            pending_nl = ""
            prev_location = None
            note_path = None
            continue

        # Check if this line starts a new block
        starts_new_block = False

        if re.match(MYPY_NOTE_REGEX, text):
            # Note line always starts new block
            starts_new_block = True
            note_path = text.split(":")[0]
            prev_location = None
        elif match := re.match(LINE_REGEX, text):
            # Extract location (path:line or path:line:col)
            current_location = match.group(1)
            current_path = current_location.split(":")[0]

            # Continue block if in note context and paths match
            if note_path is not None and current_path == note_path:
                # Continue the note block
                prev_location = current_location
            elif (
                prev_location is not None and current_location != prev_location
            ):
                # Different location, start new block
                starts_new_block = True
                prev_location = current_location
                note_path = None
            else:
                # First location or same location
                prev_location = current_location
                note_path = None
        elif re.match(SUMMARY_REGEX, text) or re.match(PYTEST_SEP_REGEX, text):
            starts_new_block = True
            prev_location = None
            note_path = None
        else:
            # Regular line, doesn't change state
            pass

        if starts_new_block:
            if not first_block:
                yield "\0"
            pending_nl = ""  # Don't carry newline into new block

        # Always clear first_block after processing first line
        if first_block:
            first_block = False

        yield pending_nl
        yield text
        pending_nl = trailing_nl
    # Don't yield final newline - blocks shouldn't end with newline


LINE_REGEX = re.compile(
    r"""^([^\s:]        # File name, with no colon, not indented
          [^:]*         # File name may contain spaces after first char
          :\d+          # Line number
          (?::\d+)?     # Column number
         )
         (?::\d+:\d+)?  # Line and column of end
         :[ ].+         # Message
    """,
    re.MULTILINE + re.VERBOSE,
)
MYPY_NOTE_REGEX = re.compile(
    r"""^[^\s:]       # File name with no colon, not indented
        [^:]*         # File name my contain spaces
        :[ ]note:[ ]  # no line number, note label
    """,
    re.VERBOSE,
)
SUMMARY_REGEX = re.compile(
    r"""^Found[ ]\d+[ ]error  # Summary line like "Found 12 errors"
    """,
    re.VERBOSE,
)
PYTEST_SEP_REGEX = re.compile(
    r"""^(={3,}|_{3,}|_[ ](_[ ])+_)  # === or ___ or _ _ _ separators
    """,
    re.VERBOSE,
)
RUFF_REGEX = re.compile(
    r"""^[ ]*-->[ ]  # Arrow marker, preceded by number column width padding
        ([^:]+       # File name
        :\d+         # Line number
        :\d+         # Column number
        )$
    """,
    re.MULTILINE + re.VERBOSE,
)


def get_location(selection: str) -> FileLocation:
    """Extract file location from error message selection.

    Args:
        selection: Error message text (line or block format)

    Returns:
        FileLocation with path, row, and optional column

    Raises:
        FileLocationNotFoundError: If location pattern not found
    """
    regex = RUFF_REGEX if "\n" in selection else LINE_REGEX
    match = re.search(regex, selection)
    if match is None:
        raise FileLocationNotFoundError(selection)

    # Parse "path:row" or "path:row:col"
    location_str = match.group(1)
    parts = location_str.split(":")
    path = parts[0]
    row = int(parts[1]) if len(parts) > 1 else None
    column = int(parts[2]) if len(parts) > 2 else None

    return FileLocation(path=path, row=row, column=column)


def select_command(selection: str) -> None:
    """Display the selected error in the text editor."""
    try:
        location = get_location(selection)
    except FileLocationNotFoundError as e:
        err_console.print(e)
        raise typer.Exit(1) from e

    # Build destination string: "path:row" or "path:row:col"
    parts = [location.path]
    if location.row is not None:
        parts.append(str(location.row))
        if location.column is not None:
            parts.append(str(location.column))
    destination = ":".join(parts)

    editor_command = ["code", "--goto", destination]
    result = subprocess.run(
        editor_command, check=False, capture_output=True, text=True
    )
    if result.returncode or result.stderr:
        err_console.print(
            "[bold red]Error running editor:",
            " ".join(shlex.quote(x) for x in editor_command),
        )
        if result.stderr:
            err_console.print(result.stderr)


if __name__ == "__main__":
    app()
