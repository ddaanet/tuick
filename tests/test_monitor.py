r"""Tests for filesystem monitoring."""

import contextlib
import http.server
import socketserver
import threading
from queue import Queue
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

import pytest

from tuick.monitor import FilesystemMonitor, MonitorEvent, MonitorThread
from tuick.reload_socket import ReloadSocketServer

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


@pytest.fixture
def http_socket(
    request: pytest.FixtureRequest,
) -> Iterator[tuple[int, Queue[tuple[str, dict[str, str]]]]]:
    """HTTP server on TCP localhost, returns port and request queue.

    Each queue item is (body, headers_dict).
    """
    num_requests = getattr(request, "param", 1)
    request_queue: Queue[tuple[str, dict[str, str]]] = Queue()

    class TestHandler(http.server.BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            request_queue.put((body, dict(self.headers)))
            self.send_response(200)
            self.end_headers()

        def log_message(
            self,
            format: str,  # noqa: A002
            *args: Any,  # noqa: ANN401
        ) -> None:
            pass

    with contextlib.ExitStack() as stack:
        server = socketserver.TCPServer(("127.0.0.1", 0), TestHandler)
        port = server.server_address[1]
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
        yield port, request_queue
        thread.join()


def test_monitor_thread_sends_reload_to_socket(
    tmp_path: Path,
    http_socket: tuple[int, Queue[tuple[str, dict[str, str]]]],
) -> None:
    """MonitorThread sends POST reload(command) to fzf port on file change."""
    port, request_queue = http_socket
    reload_cmd = "ruff check src/"

    # Create real reload_server and set fzf_port
    reload_server = ReloadSocketServer()
    reload_server.fzf_port = port
    reload_server.fzf_port_ready.set()

    mock_monitor = Mock(spec=FilesystemMonitor)
    mock_event = Mock(spec=MonitorEvent)
    mock_monitor.iter_changes.return_value = iter([mock_event])

    with patch("tuick.monitor.FilesystemMonitor", return_value=mock_monitor):
        monitor_thread = MonitorThread(
            reload_cmd, "Running...", reload_server, path=tmp_path
        )
        fzf_api_key = monitor_thread.fzf_api_key
        monitor_thread.start()

        try:
            body, headers = request_queue.get(timeout=1)
            assert body == f"change-header(Running...)+reload:{reload_cmd}"
            assert headers.get("X-Api-Key") == fzf_api_key
        finally:
            monitor_thread.stop()

    mock_monitor.iter_changes.assert_called_once()
    mock_monitor.stop.assert_called_once()
