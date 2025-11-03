"""Tuick module that handles the fzf command."""

import os
import subprocess
from contextlib import contextmanager
from typing import TYPE_CHECKING

from tuick.console import print_command, print_verbose, print_warning
from tuick.shell import quote_command

if TYPE_CHECKING:
    from collections.abc import Iterator

    from tuick.cli import CallbackCommands
    from tuick.reload_socket import TuickServerInfo


# tuick_port: reload server config
# tuick_api_key: reload server config

# fzf_api_key: monitor thread config


class FzfUserInterface:
    """Define user interface elements for fzf."""

    def __init__(self, command: list[str]) -> None:
        """Initialize fzf interface."""
        self.header = quote_command(command)
        self.running_header = f"{self.header} Running..."


@contextmanager
def open_fzf_process(
    callbacks: CallbackCommands,
    user_interface: FzfUserInterface,
    tuick_server_info: TuickServerInfo,
    fzf_api_key: str,
    *,
    verbose: bool,
) -> Iterator[subprocess.Popen[str]]:
    """Open and manage fzf process."""
    env = os.environ.copy()
    env["FORCE_COLOR"] = "1"
    env["TUICK_PORT"] = str(tuick_server_info.port)
    env["TUICK_API_KEY"] = tuick_server_info.api_key
    env["FZF_API_KEY"] = fzf_api_key

    # Have output, start fzf
    def binding_verbose(
        event: str, message: str, *, plus: bool = False
    ) -> list[str]:
        if not verbose:
            return []
        action = f"execute-silent({callbacks.message_prefix} {message})"
        return [f"{event}:{'+' if plus else ''}{action}"]

    fzf_bindings = [
        f"start:change-header({user_interface.running_header})",
        f"start:+execute-silent({callbacks.start_command})",
        f"load:change-header({user_interface.header})",
        *binding_verbose("load", "LOAD", plus=True),
        f"enter,right:execute({callbacks.select_prefix} {{}})",
        f"r:change-header({user_interface.running_header})",
        *binding_verbose("r", "RELOAD", plus=True),
        f"r:+reload({callbacks.reload_command})",
        "q:abort",
        *binding_verbose("zero", "ZERO"),
        "zero:+abort",
        "space:down",
        "backspace:up",
    ]
    fzf_cmd = [
        *("fzf", "--listen", "--read0", "--track"),
        *("--no-sort", "--reverse", "--header-border"),
        *("--ansi", "--color=dark", "--highlight-line", "--wrap"),
        *("--disabled", "--no-input", "--bind"),
        ",".join(fzf_bindings),
    ]

    if verbose:
        print_command(fzf_cmd)

    with subprocess.Popen(
        fzf_cmd, stdin=subprocess.PIPE, text=True, env=env
    ) as fzf_proc:
        yield fzf_proc

    if verbose:
        if fzf_proc.returncode == 0:
            print_verbose("fzf exited normally (0)")
        elif fzf_proc.returncode == 130:
            print_verbose("fzf aborted by user (130)")
        else:
            args = "fzf exited with status", fzf_proc.returncode
            print_warning(*args)
