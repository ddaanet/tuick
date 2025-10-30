"""Filesystem monitoring."""

import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import requests

from tuick.console import console

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from tuick.reload_socket import ReloadSocketServer

# ruff: noqa: TRY003


@dataclass
class MonitorChange:
    """A filesystem changes."""

    type: str
    path: Path

    @classmethod
    def from_line(cls, line: str) -> MonitorChange:
        """Create a MonitorChange from a single watchexec output line."""
        text = line.removesuffix("\n")
        if ":" not in text:
            raise ValueError(
                f"Expected colon-separated change, received: {text!r}"
            )
        parts = text.split(":", maxsplit=1)
        return cls(parts[0], Path(parts[1]))


@dataclass
class MonitorEvent:
    """A group of filesystem changes in a single event."""

    changes: Iterable[MonitorChange]

    @classmethod
    def from_lines(cls, lines: Iterable[str]) -> MonitorEvent:
        """Create MonitorEvent from a group of watchexec output lines."""
        return cls([MonitorChange.from_line(x) for x in lines])


class FilesystemMonitor:
    """Filesystem monitor using watchexec."""

    def __init__(self, path: Path, *, testing: bool = False) -> None:
        """Initialize and start the filesystem monitor subprocess."""
        cmd = [
            "watchexec",
            "--only-emit-events",
            "--emit-events-to=stdio",
            "--no-meta",
            "--postpone",
        ]
        if testing:
            cmd.append("--debounce=0")

        self._proc = subprocess.Popen(
            cmd,
            cwd=str(path),
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
        )
        assert self._proc.stdout is not None

    def iter_changes(self) -> Iterator[MonitorEvent]:
        """Iterate over filesystem change events."""
        assert self._proc.stdout is not None

        lines: list[str] = []
        while True:
            for line in self._proc.stdout:
                if line == "\n":  # Empty line, group separator
                    break
                lines.append(line)
            else:  # End of stream
                break
            yield MonitorEvent.from_lines(lines)
            lines = []
        if lines:
            yield MonitorEvent.from_lines(lines)

    def stop(self) -> None:
        """Send SIGTERM to the subprocess and wait for it to terminate."""
        self._proc.terminate()
        self._proc.wait()


class MonitorThread:
    """Thread that monitors filesystem and sends reload commands via HTTP."""

    def __init__(  # noqa: PLR0913
        self,
        reload_cmd: str,
        reload_server: ReloadSocketServer,
        fzf_api_key: str,
        *,
        path: Path | None = None,
        testing: bool = False,
        verbose: bool = False,
    ) -> None:
        """Initialize monitor thread."""
        self.path = path if path is not None else Path.cwd()
        self.reload_cmd = reload_cmd
        self.reload_server = reload_server
        self.fzf_api_key = fzf_api_key
        self.testing = testing
        self.verbose = verbose
        self._monitor: FilesystemMonitor | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start monitoring thread."""
        self._monitor = FilesystemMonitor(self.path, testing=self.testing)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        """Monitor filesystem and send reload commands."""
        assert self._monitor is not None
        for _event in self._monitor.iter_changes():
            self._send_reload()

    def _send_reload(self) -> None:
        """Send reload command via HTTP POST to fzf socket."""
        # Wait for fzf_port to be set by start command
        self.reload_server.fzf_port_ready.wait()

        assert self.reload_server.fzf_port is not None
        fzf_url = f"http://127.0.0.1:{self.reload_server.fzf_port}"
        body = f"reload:{self.reload_cmd}"
        headers = {"X-Api-Key": self.fzf_api_key}

        if self.verbose:
            console.print(f"[dim]POST {fzf_url}[/]")
            console.print(f"[dim]  Body: {body!r}[/]")

        response = requests.post(
            fzf_url, data=body, headers=headers, timeout=10
        )

        if self.verbose:
            console.print(f"[dim]  Status: {response.status_code}[/]")
            if response.text:
                console.print(f"[dim]  Response: {response.text!r}[/]")

    def stop(self) -> None:
        """Stop monitoring thread."""
        if self._monitor:
            self._monitor.stop()
        if self._thread:
            self._thread.join(timeout=1.0)
