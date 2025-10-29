"""Shared console instances for tuick."""

from rich.console import Console

console = Console()
err_console = Console(stderr=True)
