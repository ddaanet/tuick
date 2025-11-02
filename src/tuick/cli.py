"""Tuick command line interface.

Tuick is a wrapper for compilers and checkers that integrates with fzf and your
text editor to provide fluid, keyboard-friendly, access to code error
locations.
"""

import contextlib
import os
import shutil
import socket
import subprocess
import sys
import threading
import typing
from pathlib import Path

import typer

import tuick.console
from tuick.console import (
    print_command,
    print_error,
    print_event,
    print_verbose,
    print_warning,
)
from tuick.editor import (
    UnsupportedEditorError,
    get_editor_command,
    get_editor_from_env,
)
from tuick.monitor import MonitorThread
from tuick.parser import FileLocationNotFoundError, get_location, split_blocks
from tuick.reload_socket import ReloadSocketServer, generate_api_key
from tuick.shell import quote_command

app = typer.Typer()


# ruff: noqa: FBT001 FBT003 Typer API uses boolean arguments for flags
# ruff: noqa: B008 function-call-in-default-argument


@app.command()
def main(  # noqa: PLR0913
    command: list[str] = typer.Argument(default_factory=list),
    reload: bool = typer.Option(
        False, "--reload", help="Internal: run command and output blocks"
    ),
    select: str = typer.Option(
        "", "--select", help="Internal: open editor at error location"
    ),
    start: bool = typer.Option(
        False, "--start", help="Internal: notify fzf port to parent process"
    ),
    message: str = typer.Option(
        "", "--message", help="Internal: log a message"
    ),
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Show verbose output"
    ),
) -> None:
    """Tuick: Text User Interface for Compilers and checkers."""
    with tuick.console.setup_log_file():
        if verbose:
            base_cmd = Path(sys.argv[0]).name
            print_event(quote_command([base_cmd, *sys.argv[1:]]))

        exclusive_options = sum([reload, bool(select), start, bool(message)])
        if exclusive_options > 1:
            message = (
                "Options --reload, --select, --start, and --message are"
                " mutually exclusive"
            )
            print_error(None, message)
            raise typer.Exit(1)

        if not exclusive_options and not command:
            print_error(None, "No command specified")

        if reload:
            reload_command(command, verbose=verbose)
        elif select:
            select_command(select, verbose=verbose)
        elif start:
            start_command(verbose=verbose)
        elif message:
            message_command(message)
        else:
            list_command(command, verbose=verbose)


def list_command(command: list[str], *, verbose: bool = False) -> None:  # noqa: C901, PLR0915
    """List errors from running COMMAND."""
    # TODO: Fix PLR0915, too many statements
    myself = sys.argv[0]
    # Shorten the command name if it is the same as the default
    default: str | None = shutil.which(Path(myself).name)
    if default and Path(default).resolve() == Path(myself).resolve():
        myself = Path(myself).name

    verbose_flag = ["-v"] if verbose else []
    reload_cmd = quote_command(
        [myself, *verbose_flag, "--reload", "--", *command]
    )
    select_cmd = quote_command([myself, *verbose_flag, "--select"])
    start_cmd = quote_command([myself, *verbose_flag, "--start"])
    message_command = quote_command([myself, "--message"])
    header = quote_command(command)
    running_header = f"{header} Running..."

    with contextlib.ExitStack() as stack:
        # Create tuick reload coordination server
        tuick_api_key = generate_api_key()
        reload_server = ReloadSocketServer(tuick_api_key)
        reload_server.start()
        tuick_port = reload_server.server_address[1]

        # Generate fzf API key for monitor thread
        fzf_api_key = generate_api_key()

        monitor = MonitorThread(
            reload_cmd,
            running_header,
            reload_server,
            fzf_api_key,
            verbose=verbose,
        )
        monitor.start()
        stack.callback(monitor.stop)

        # Run command and stream to fzf stdin
        env = os.environ.copy()
        env["FORCE_COLOR"] = "1"
        env["TUICK_PORT"] = str(tuick_port)
        env["TUICK_API_KEY"] = tuick_api_key
        env["FZF_API_KEY"] = fzf_api_key

        if verbose:
            print_command(command)
        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        ) as cmd_proc:
            reload_server.cmd_proc = cmd_proc
            # Read first chunk to check if there's any output
            assert cmd_proc.stdout is not None
            chunks = split_blocks(cmd_proc.stdout)
            first_chunk = None
            try:
                first_chunk = next(chunks)
            except StopIteration:
                # No output, don't start fzf
                return

            def report_exit() -> None:
                cmd_proc.wait()
                args = "  Initial load command exit:", cmd_proc.returncode
                print_verbose(*args)

            if verbose:
                threading.Thread(target=report_exit, daemon=True).start()

            # Have output, start fzf
            def binding_verbose(
                event: str,
                message: str,
                plus: bool = False,  # noqa: FBT002
            ) -> list[str]:
                if not verbose:
                    return []
                action = f"execute-silent({message_command} {message})"
                return [f"{event}:{'+' if plus else ''}{action}"]

            fzf_bindings = [
                f"start:change-header({running_header})",
                f"start:+execute-silent({start_cmd})",
                f"load:change-header({header})",
                *binding_verbose("load", "LOAD", plus=True),
                f"enter,right:execute({select_cmd} {{}})",
                f"r:change-header({running_header})",
                *binding_verbose("r", "RELOAD", plus=True),
                f"r:+reload({reload_cmd})",
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
                if fzf_proc.stdin is None:
                    return

                # Write first chunk
                fzf_proc.stdin.write(first_chunk)

                # Stream remaining chunks
                for chunk in chunks:
                    fzf_proc.stdin.write(chunk)

                fzf_proc.stdin.close()

            if verbose:
                if fzf_proc.returncode == 0:
                    print_verbose("fzf exited normally (0)")
                elif fzf_proc.returncode == 130:
                    print_verbose("fzf aborted by user (130)")
                else:
                    args = "fzf exited with status", fzf_proc.returncode
                    print_warning(*args)

            if fzf_proc.returncode not in (0, 130):
                # 130 means fzf was aborted with ctrl-C or ESC
                sys.exit(fzf_proc.returncode)


def _send_to_tuick_server(message: str, expected: str) -> None:
    """Send authenticated message to tuick server and verify response."""
    tuick_port = os.environ.get("TUICK_PORT")
    tuick_api_key = os.environ.get("TUICK_API_KEY")

    if not tuick_port or not tuick_api_key:
        message = "Missing environment variable: TUICK_PORT or TUICK_API_KEY"
        print_error(None, message)
        raise typer.Exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("127.0.0.1", int(tuick_port)))
        sock.sendall(f"secret: {tuick_api_key}\n{message}\n".encode())
        response = sock.recv(1024).decode().strip()

    if response != expected:
        print_error(None, "Server response:", response)
        raise typer.Exit(1)


def _run_command_and_stream_blocks(
    command: list[str], output: typing.TextIO, *, verbose: bool = False
) -> None:
    """Run COMMAND with FORCE_COLOR=1 and stream null-separated blocks."""
    env = os.environ.copy()
    env["FORCE_COLOR"] = "1"
    if verbose:
        print_command(command)
    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    ) as process:
        if process.stdout:
            output.writelines(split_blocks(process.stdout))
    if verbose:
        print_verbose("  Reload command exit:", process.returncode)


def start_command(*, verbose: bool = False) -> None:
    """Notify parent process of fzf port."""
    fzf_port = os.environ.get("FZF_PORT")
    if not fzf_port:
        print_error(None, "Missing environment variable: FZF_PORT")
        raise typer.Exit(1)
    _send_to_tuick_server(f"fzf_port: {fzf_port}", "ok")
    if verbose:
        print_verbose("  fzf_port:", fzf_port)


def reload_command(command: list[str], *, verbose: bool = False) -> None:
    """Notify parent, wait for go, then run command and output blocks."""
    try:
        _send_to_tuick_server("reload", "go")
        _run_command_and_stream_blocks(command, sys.stdout, verbose=verbose)
    except Exception as error:
        print_error("Reload error:", error)
        raise


def select_command(selection: str, *, verbose: bool = False) -> None:
    """Display the selected error in the text editor."""
    try:
        location = get_location(selection)
    except FileLocationNotFoundError:
        if verbose:
            print_warning("No location found:", repr(selection))
        return

    # Get editor from environment
    editor = get_editor_from_env()
    if editor is None:
        message = "No editor configured. Set EDITOR environment variable."
        print_error(None, message)
        raise typer.Exit(1)

    # Build editor command
    try:
        editor_command = get_editor_command(editor, location)
    except UnsupportedEditorError as error:
        print_error(None, error)
        raise typer.Exit(1) from error

    # Display and execute command
    if verbose:
        print_command(editor_command)
    try:
        editor_command.run()
    except subprocess.CalledProcessError as error:
        print_error(None, "Editor exit status:", error.returncode)
        raise typer.Exit(1) from error


def message_command(message: str) -> None:
    """Print a message to the error console."""
    if message == "RELOAD":
        print_event("Manual reload")
    elif message == "LOAD":
        print_verbose("  [cyan]Loading complete")
    elif message == "ZERO":
        print_warning("  Reload produced no output")


if __name__ == "__main__":
    app()
