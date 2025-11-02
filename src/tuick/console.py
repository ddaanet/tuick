"""Shared console instances for tuick."""

import os
import sys
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import IO, TYPE_CHECKING, Any

from tuick.shell import quote_command

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from tuick.editor import EditorCommand


from rich.console import Console

TUICK_LOG_FILE = "TUICK_LOG_FILE"


_console = Console(soft_wrap=True, stderr=True)


def print_verbose(*args: Any) -> None:  # noqa: ANN401
    """Print general verbose messages."""
    _console.print(*args, style="dim")
    _console.file.flush()


def print_event(message: str) -> None:
    """Print an event message.

    Verbose mode.
    """
    _console.print(">", message, style="dim bold bright_white")
    _console.file.flush()


def print_command(command: list[str] | EditorCommand) -> None:
    """Print a command that will be executed in a subprocess.

    Verbose mode.
    """
    message = quote_command(command) if isinstance(command, list) else command
    _console.print("$", message, style="dim bold bright_white")
    _console.file.flush()


def print_warning(*args: Any) -> None:  # noqa: ANN401
    """Print a warning message."""
    _console.print(*args, style="yellow")
    _console.file.flush()


def print_error(title: str | None, *args: Any) -> None:  # noqa: ANN401
    """Print an error message."""
    title = title or "Error:"
    _console.print(f"[bold]{title}", *args, style="red")
    _console.file.flush()


@contextmanager
def setup_log_file() -> Iterator[None]:
    """Configure console to use the log file specified in TUICK_LOG_FILE.

    Close the file and revert the console configuration when done.

    If TUICK_LOG_FILE is not set, we are in a top-level tuick command, create a
    log file and set TUICK_LOG_FILE so that child processes can use it, then
    copy the log file to stderr when done.
    """
    if _console.file is not sys.stderr:
        yield  # Console already redirected, presumably in a test
        return
    log_cleanup: Callable[[], None]
    log_file: IO[str]
    env_path = os.environ.get(TUICK_LOG_FILE)
    if env_path:
        # Open the log file if it is set in TUICK_LOG_FILE
        try:
            log_file = open(env_path, "a")  # noqa: SIM115 PTH123
        except OSError as error:
            print_error("Error opening log file:", error)
            raise SystemExit(1) from error
        log_cleanup = log_file.close
    else:
        # If TUICK_LOG_FILE is not set, create a temporary log file.
        tempfile = NamedTemporaryFile(  # noqa: SIM115
            "a+", prefix="tuick-", suffix=".log"
        )
        os.environ[TUICK_LOG_FILE] = tempfile.name
        log_cleanup = tempfile.close
        log_file = tempfile.file

    _console.file = log_file
    try:
        yield
    finally:
        if env_path is None:
            del os.environ[TUICK_LOG_FILE]
            log_file.seek(0)
            while chunk := log_file.read(32 * 1024):
                sys.stderr.write(chunk)
        _console.file = sys.stderr
        log_cleanup()
