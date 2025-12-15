# Quality and Error Suppression Rules

## Error Suppression Rules

All commits must be clean (zero mypy/ruff errors, zero warnings).

- **NO** `type: ignore` or bare `# noqa` - always use specific codes
- **NO** silencing deprecation warnings - fix them by updating code
- Prefer fixing root cause over suppression
- All suppressions require comment explaining WHY (not just what)
- **"too much work"** is NOT an acceptable justification
- Run `just agent` before committing to verify all checks pass
- Suppressions: ALL noqa/type:ignore suppressions require explanatory comments. Complexity errors (C901, PLR0912, PLR0915) can be suppressed if a refactoring task is added to TODO.md. Other suppressions need inline justification.

## Technical Debt Management

Document technical debt so it can be measured and repaid. Suppress errors with specific codes and comments, AND document in TODO.md with fix options.

**TODO.md pattern:**
```markdown
#### Error Type (N errors)
**Files**: locations with line numbers
**Issue**: what's wrong and why
**Fix Options**: specific approaches to fix
```

**Cross-reference:** code comments ↔ TODO.md

## Test Infrastructure

- **testutil**: Create utilities for repeated mocking patterns, but at the right abstraction level
- **testclarity**: Test infrastructure must not obscure test intent. If mocking setup dominates the test, extract to utility
- **testevent**: Track meaningful system events in tests, not language-level details (e.g., process creation/termination, not `__enter__`)
- Example: `patch_popen(sequence, procs)` encapsulates both patching and proc sequencing
- Mock data tracking: when tracking mock calls in tests, avoid using `!r` repr formatting which adds extra quotes. Use `f"event:{data}"` not `f"event:{data!r}"` for cleaner assertions.
- ALWAYS check for existing test helpers before writing mock setup. Use `patch_popen()`, `make_cmd_proc()`, `make_fzf_proc()` etc. Never manually construct mocks that helpers already provide. Grep test files for helper functions if unsure what exists.
- Mock simplicity: Avoid over-abstracting mock wrappers. Use patch contexts directly and access `mock.mock_calls` or `mock.call_args_list` in tests. Create helper functions for extracting data from mock_calls if needed, but don't wrap the context manager itself. Example: `get_command_calls_from_mock()` extracts commands from mock_calls, but patch returns unwrapped context.
- Mock call structure: Each entry in `mock.mock_calls` is a tuple `(name, args, kwargs)`. Use tuple unpacking or indexing: `_name, args, kwargs = mock.mock_calls[0]`. For `call_args_list`, use `call[0]` for args tuple, `call[1]` for kwargs dict.
- Integration test requirements: Some dependencies (like errorformat) are hard requirements and should NOT be mocked in CLI integration tests. Only mock UI components (fzf) and use real subprocess calls for required tools. This validates actual integration.
- Mock subprocess recursion: When mocking subprocess.Popen and the mock may trigger additional subprocess calls, save original_popen = subprocess.Popen before patching to avoid infinite recursion. Use original_popen for passthrough cases.
- Click/Typer CLI testing: Do not use pytest capture fixtures (capsys/capfd) with Click/Typer test runners. Click's runner captures output internally before pytest can intercept it. Use `result.stdout` and `result.stderr` from Click's Result object. Apply `strip_ansi()` to remove color codes before assertions. Example:
  ```python
  result = runner.invoke(app, ["--verbose", "arg"])
  output = strip_ansi(result.stderr)
  assert "expected text" in output
  ```
