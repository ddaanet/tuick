# Testing Rules

## Test-Driven Development (TDD)

### Workflows

- **Red-Green-Refactor Cycle** (for new features and fixes):
  1. **Plan**: Understand requirements and design approach
  2. **Test (Red)**: Write tests that fail, demonstrating the missing functionality
  3. **Code (Green)**: Implement the simplest correct behavior to make tests pass
  4. **Commit**: Commit the working feature with tests
  5. **Refactor**: Improve code structure, factor duplicates, reorganize (non-trivial changes in separate commits)

- **Refactor Workflow** (for reorganizations with no behavior change):
  1. **Plan**: Understand current structure and desired changes
  2. **Code**: Make refactoring changes
  3. **Green**: Run tests to confirm no behavior change
  4. **Commit**: Commit the refactoring

### Key Principles

- Add tests first for new features/fixes - do not implement without a failing test first
- If bugs discovered during implementation, add to TODO.md for test + fix together
- Keep existing tests passing throughout refactoring
- **Prefer integration tests over unit tests** - they are more robust to implementation changes
- **Do not write unit tests for existing code** unless you plan to modify it
- Add tests first, period. Do not fix bugs or add features without a failing test first. If identified during implementation, add to TODO.md for test and fix together.
- Post-hoc testing: When writing tests for existing code/fixes, validate tests by reverting the fix, confirming test failure, then restoring the fix and confirming test passes. This ensures tests actually test the intended behavior.

## Test Execution

- `just agent-test ...` to run full suite or specific tests
- `just full-diff=true agent` or `just full-diff=true agent-test` for full assert diffs
- Never run pytest or `just test` directly, always use `just agent-test` which adds flags to prevent context bloat and format errors for machine readability

## Test Quality

- Test coverage: Never reduce test coverage when refactoring tests. If simplifying a complex test, add separate tests to cover removed scenarios. Integration test modules should document their purpose in module docstrings.
- **testsize**: Keep tests compact, fit in ~50 lines. Use helper functions to format expected output declaratively
- Minimize test count: combine related assertions testing the same behavior into one test. Separate tests should test different behaviors, not just different inputs. Don't write tests for trivial variations or CLI usage errors.
- Read error messages: they contain hints or directions
- Test verification: When testing parsing/transformation, verify ALL output fields, not just content. For location-based parsers, explicitly verify file, line, col, end_line, end_col extraction.
- Test formatting: Create custom formatters (like format_for_test()) that show differences clearly. Omit empty/default fields to reduce noise. Format complex fields (like multi-line content) with indentation and repr
- Real tool output: Use actual tool output for test data, not invented examples. Run the tool (with various flags/modes) to capture real output. Verify tool capabilities (e.g., check errorformat -list) before assuming support. Check tool registries (BUILTIN_TOOLS, CUSTOM_PATTERNS, OVERRIDE_PATTERNS) before writing integration tests.
- Test data reuse: NEVER duplicate test data. Extract to module-level constants and import them. If one test file already has the data, import from there. If data format is inconvenient, preprocess/transform, but do not copy-paste.
- Never guess at fixes: get proper diagnostics (tracebacks, error output) before fixing. If error output is unclear, add logging or error handlers first.
- Verify before fixing: When a bug is described in TODO.md or elsewhere, verify the problem exists before implementing a fix. Check documentation, stdlib source, or write a reproduction test. Don't assume the bug description is accurate without verification.
- Spec mocks: always use create_autospec() or patch(autospec=True), do not use plain Mock or MagicMock
- Do not mock the hell out of things. When testing a single unit of behavior, prefer integration tests over isolated unit tests. Integration tests provide better confidence with less maintenance. Use unit tests with mocking only when testing complex behavior with multiple edge cases requiring controlled inputs.
- Do not patch SUT components: only mock external dependencies (UI, external processes). Core application components like ReloadSocketServer are part of the SUT and must run real code.
- Tests must not compensate for SUT deviations: do not add workarounds (like calling .end_output() manually) to make tests pass when SUT behavior is incorrect. Tests document expected behavior; workarounds hide real bugs.
- Never silently handle corrupted input: assert and fail fast when detecting invalid data (e.g., Mock objects where strings expected). Silent failures hide bugs.
- Assert messages: Don't add trivial assert messages. Pytest already shows actual vs expected values by default. Only add messages when they provide context that the bare assertion values don't give. Example: use `assert x == y` not `assert x == y, f"expected {y}, got {x}"`.
- Checking complex structures:
  - When comparing complex structures (lists, dicts, dataclasses) in tests
  - Do not assert comparisons to the value of individual members
  - Instead assert a single comparison for the whole structure
  - If some items must be ignored in the comparison, build a dict for the comparison, omitting those items.
- Fixture design: avoid implicit/magical behavior. If a fixture has side effects or requirements (like output checking), make them explicit through method calls, not automatic in teardown based on hidden state.
- xfail integration tests: For multi-mode features, write xfail integration tests for each configuration first, not unit tests for routing. Remove xfail as each mode is implemented.
- xfail for TDD of registries: when building registries that start empty and grow, write xfail test for first entry to be added, passing test for unknown entries
- xfail precision: When marking tests xfail during incremental implementation, reference the specific task number or feature name. Use "Task N: reason" format so it's clear when to remove the marker. Example: `@pytest.mark.xfail(reason="Task 9: fzf delimiter config not implemented")` not generic "feature not ready".
- Option parsing tests: When testing CLI option routing/parsing, mock the routed command function and verify call arguments, rather than full integration tests. Faster and more focused on the routing logic being tested.
- Test docstrings: Describe behavior, not command syntax. Keep command names lowercase (e.g., "tuick" not "Tuick"). Focus on what the test verifies.
- Multi-phase integration tests: When testing environment inheritance or state propagation across process boundaries, use capture-and-replay pattern: capture state from phase 1, clean environment, replay with captured state in phase 2. Prevents false positives from state pollution.

## Test Synchronization

- **testsync**: Multithreaded tests must use proper synchronization.
  - **testawake**: `time.sleep()` is _strictly forbidden_ in tests.
  - **fastgreen**: Never block on the green path. The execution of a successful test must never block on a timeout.
  - **testrace**: Don't test race conditions by trying to trigger undefined behavior. Test that synchronization mechanisms work by verifying concurrent operations complete successfully. Use explicit synchronization (Events, Barriers) to control thread timing in tests.
  - The green execution path can move from one thread to another through blocking synchronization.
  - After teardown of a successful test, all created threads and processes must be joined.
  - Blocking on a timeout in test and teardown is allowed for failing tests.
