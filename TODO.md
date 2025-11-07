# Tuick Task List

- Refactor error handling: replace print_error + raise typer.Exit with custom
  exceptions, catch in main and print with rich. (TRY301)

- Add allow_interspersed_args=False to command, so we do not need to use --
  most of the time.

- Use execute-silent for select_command in client editors.

- Find type-safe solution to avoid cast in ReloadRequestHandler.handle().

- Test editors with CLI integration. (Already tested code, surf, cursor, idea,
  pycharm, micro)

- Test editors with URL integration, on Mac/Linux/Windows.

- Fix uses of generic mocks where specs could be used.

- Refactor test_cli.py to reduce verbosity: factorize subprocess mocking setup
  to make tests easier to understand and maintain.

- Refactor existing tests that manually create ReloadSocketServer() to use the
  server_with_key fixture from conftest.py.

- Refactor test_cli.py to use make_cmd_proc and make_fzf_proc helpers, make
  sequence parameter optional for tests that don't track sequences.

- Fix race condition in reload server: catch ProcessLookupError from
  .terminate() to handle process that already completed. The proc.poll() check
  before proc.terminate() is insufficient.

- Optimize output handling: use binary files for saved output instead of text
  files, use TextIOWrapper when printing to console. This avoids redundant
  decode-encode operations when streaming output through sockets and files.

- Create custom Popen subclass with thread-safe wait(): add lock around wait()
  method since it can be called from main thread (normal completion) or reload
  server thread (termination).

- Enable filtering.
  - That (probably) implies removing the "zero:abort" binding.
  - If a reload (manual or automatic) command produces no output, kill fzf
  - For the case of a manual reload, that requires IPC between the reload
    command and the top command, probably through a unix socket.

- Maybe integrate with bat for preview. Possible approaches:
  1. `tuick --preview bat` as a wrapper to bat
  2. Hidden data (--with-nth) or invisible delimiters (so the path and line
     number are in fixed fields)
