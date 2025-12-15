# Test Design and Quality

## Test Quality

- Test coverage: Never reduce test coverage when refactoring tests. If
  simplifying a complex test, add separate tests to cover removed scenarios.
  Integration test modules should document their purpose in module docstrings.
- **testsize**: Keep tests compact, fit in ~50 lines. Use helper functions to
  format expected output declaratively
- Minimize test count: combine related assertions testing the same behavior into
  one test. Separate tests should test different behaviors, not just different
  inputs. Don't write tests for trivial variations or CLI usage errors.
- Read error messages: they contain hints or directions
- Test verification: When testing parsing/transformation, verify ALL output
  fields, not just content. For location-based parsers, explicitly verify file,
  line, col, end_line, end_col extraction.
- Test formatting: Create custom formatters (like format_for_test()) that show
  differences clearly. Omit empty/default fields to reduce noise. Format complex
  fields (like multi-line content) with indentation and repr
- Real tool output: Use actual tool output for test data, not invented examples.
  Run the tool (with various flags/modes) to capture real output. Verify tool
  capabilities (e.g., check errorformat -list) before assuming support. Check
  tool registries (BUILTIN_TOOLS, CUSTOM_PATTERNS, OVERRIDE_PATTERNS) before
  writing integration tests.
- Test data reuse: NEVER duplicate test data. Extract to module-level constants
  and import them. If one test file already has the data, import from there. If
  data format is inconvenient, preprocess/transform, but do not copy-paste.
- Never guess at fixes: get proper diagnostics (tracebacks, error output) before
  fixing. If error output is unclear, add logging or error handlers first.
- Verify before fixing: When a bug is described in TODO.md or elsewhere, verify
  the problem exists before implementing a fix. Check documentation, stdlib
  source, or write a reproduction test. Don't assume the bug description is
  accurate without verification.
- Spec mocks: always use create_autospec() or patch(autospec=True), do not use
  plain Mock or MagicMock
- Do not mock the hell out of things. When testing a single unit of behavior,
  prefer integration tests over isolated unit tests. Integration tests provide
  better confidence with less maintenance. Use unit tests with mocking only when
  testing complex behavior with multiple edge cases requiring controlled inputs.
- Do not patch SUT components: only mock external dependencies (UI, external
  processes). Core application components like ReloadSocketServer are part of
  the SUT and must run real code.
- Tests must not compensate for SUT deviations: do not add workarounds (like
  calling .end_output() manually) to make tests pass when SUT behavior is
  incorrect. Tests document expected behavior; workarounds hide real bugs.
- Never silently handle corrupted input: assert and fail fast when detecting
  invalid data (e.g., Mock objects where strings expected). Silent failures hide
  bugs.
- Assert messages: Don't add trivial assert messages. Pytest already shows
  actual vs expected values by default. Only add messages when they provide
  context that the bare assertion values don't give. Example: use
  `assert x == y` not `assert x == y, f"expected {y}, got {x}"`.
- Checking complex structures:
  - When comparing complex structures (lists, dicts, dataclasses) in tests
  - Do not assert comparisons to the value of individual members
  - Instead assert a single comparison for the whole structure
  - If some items must be ignored in the comparison, build a dict for the
    comparison, omitting those items.
- Fixture design: avoid implicit/magical behavior. If a fixture has side effects
  or requirements (like output checking), make them explicit through method
  calls, not automatic in teardown based on hidden state.
- xfail integration tests: For multi-mode features, write xfail integration
  tests for each configuration first, not unit tests for routing. Remove xfail
  as each mode is implemented.
- xfail for TDD of registries: when building registries that start empty and
  grow, write xfail test for first entry to be added, passing test for unknown
  entries
- xfail precision: When marking tests xfail during incremental implementation,
  reference the specific task number or feature name. Use "Task N: reason"
  format so it's clear when to remove the marker. Example:
  `@pytest.mark.xfail(reason="Task 9: fzf delimiter config not implemented")`
  not generic "feature not ready".
- Option parsing tests: When testing CLI option routing/parsing, mock the routed
  command function and verify call arguments, rather than full integration
  tests. Faster and more focused on the routing logic being tested.
- Test docstrings: Describe behavior, not command syntax. Keep command names
  lowercase (e.g., "tuick" not "Tuick"). Focus on what the test verifies.
- Multi-phase integration tests: When testing environment inheritance or state
  propagation across process boundaries, use capture-and-replay pattern: capture
  state from phase 1, clean environment, replay with captured state in phase 2.
  Prevents false positives from state pollution.

## Test Infrastructure

- testutil: Create utilities for repeated mocking patterns, but at the right
  abstraction level

- testclarity: Test infrastructure must not obscure test intent. If mocking
  setup dominates the test, extract to utility

- testevent: Track meaningful system events in tests, not language-level details
  (e.g., process creation/termination, not `__enter__`)

- Example: `patch_popen(sequence, procs)` encapsulates both patching and proc
  sequencing

- Mock data tracking: when tracking mock calls in tests, avoid using `!r` repr
  formatting which adds extra quotes. Use `f"event:{data}"` not
  `f"event:{data!r}"` for cleaner assertions.

- ALWAYS check for existing test helpers before writing mock setup. Use
  `patch_popen()`, `make_cmd_proc()`, `make_fzf_proc()` etc. Never manually
  construct mocks that helpers already provide. Grep test files for helper
  functions if unsure what exists.

- Mock simplicity: Avoid over-abstracting mock wrappers. Use patch contexts
  directly and access `mock.mock_calls` or `mock.call_args_list` in tests.
  Create helper functions for extracting data from mock_calls if needed, but
  don't wrap the context manager itself. Example:
  `get_command_calls_from_mock()` extracts commands from mock_calls, but patch
  returns unwrapped context.

- Mock call structure: Each entry in `mock.mock_calls` is a tuple
  `(name, args, kwargs)`. Use tuple unpacking or indexing:
  `_name, args, kwargs = mock.mock_calls[0]`. For `call_args_list`, use
  `call[0]` for args tuple, `call[1]` for kwargs dict.

- Integration test requirements: Some dependencies (like errorformat) are hard
  requirements and should NOT be mocked in CLI integration tests. Only mock UI
  components (fzf) and use real subprocess calls for required tools. This
  validates actual integration.

- Mock subprocess recursion: When mocking subprocess.Popen and the mock may
  trigger additional subprocess calls, save original_popen = subprocess.Popen
  before patching to avoid infinite recursion. Use original_popen for
  passthrough cases.

- Click/Typer CLI testing: Do not use pytest capture fixtures (capsys/capfd)
  with Click/Typer test runners. Click's runner captures output internally
  before pytest can intercept it. Use `result.stdout` and `result.stderr` from
  Click's Result object. Apply `strip_ansi()` to remove color codes before
  assertions. Example:

```python
result = runner.invoke(app, ["--verbose", "arg"])
output = strip_ansi(result.stderr)
assert "expected text" in output
```

## Test Synchronization

- **testsync**: Multithreaded tests must use proper synchronization.
  - **testawake**: `time.sleep()` is _strictly forbidden_ in tests.
  - **fastgreen**: Never block on the green path. The execution of a successful
    test must never block on a timeout.
  - **testrace**: Don't test race conditions by trying to trigger undefined
    behavior. Test that synchronization mechanisms work by verifying concurrent
    operations complete successfully. Use explicit synchronization (Events,
    Barriers) to control thread timing in tests.
  - The green execution path can move from one thread to another through
    blocking synchronization.
  - After teardown of a successful test, all created threads and processes must
    be joined.
  - Blocking on a timeout in test and teardown is allowed for failing tests.
