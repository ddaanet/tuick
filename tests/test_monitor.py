r"""Tests for filesystem monitoring."""

import contextlib
import http.server
import socketserver
import tempfile
import threading
from pathlib import Path
from queue import Queue
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

import pytest

from tuick.monitor import FilesystemMonitor, MonitorEvent, MonitorThread

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def http_socket(
    request: pytest.FixtureRequest,
) -> Iterator[tuple[Path, Queue[str]]]:
    """HTTP server on Unix socket, returns socket path and request queue."""
    num_requests = getattr(request, "param", 1)
    request_queue: Queue[str] = Queue()

    class TestHandler(http.server.BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            request_queue.put(body)
            self.send_response(200)
            self.end_headers()

        def log_message(
            self,
            format: str,  # noqa: A002
            *args: Any,  # noqa: ANN401
        ) -> None:
            pass

    with contextlib.ExitStack() as stack:
        tmpdir = stack.enter_context(tempfile.TemporaryDirectory())
        socket_path = Path(tmpdir) / "fzf.sock"
        server = socketserver.UnixStreamServer(str(socket_path), TestHandler)
        server.timeout = 1
        has_timed_out = False

        def handle_timeout():
            nonlocal has_timed_out
            has_timed_out = True

        def handle_requests() -> None:
            for _ in range(num_requests):
                server.handle_request()
                if has_timed_out:
                    break

        server.handle_timeout = handle_timeout  # type: ignore[method-assign]
        stack.enter_context(server)
        thread = threading.Thread(target=handle_requests)
        thread.start()
        yield socket_path, request_queue
        thread.join()


def test_monitor_thread_sends_reload_to_socket(
    tmp_path: Path, http_socket: tuple[Path, Queue[str]]
) -> None:
    """MonitorThread sends POST reload(command) to socket on file change."""
    socket_path, request_queue = http_socket
    reload_cmd = "ruff check src/"

    mock_monitor = Mock(spec=FilesystemMonitor)
    mock_event = Mock(spec=MonitorEvent)
    mock_monitor.iter_changes.return_value = iter([mock_event])

    with patch("tuick.monitor.FilesystemMonitor", return_value=mock_monitor):
        monitor_thread = MonitorThread(
            socket_path, reload_cmd, path=tmp_path, testing=True
        )
        monitor_thread.start()

        try:
            body = request_queue.get(timeout=1)
            assert body == f"reload:{reload_cmd}"
        finally:
            monitor_thread.stop()

    mock_monitor.iter_changes.assert_called_once()
    mock_monitor.stop.assert_called_once()
