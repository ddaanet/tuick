# Testing Rules

## Test-Driven Development (TDD)

### Workflows

- **Red-Green-Refactor Cycle** (for new features and fixes):

  1. **Plan**: Understand requirements and design approach
  2. **Test (Red)**: Write tests that fail, demonstrating the missing
     functionality
  3. **Code (Green)**: Implement the simplest correct behavior to make tests
     pass
  4. **Commit**: Commit the working feature with tests
  5. **Refactor**: Improve code structure, factor duplicates, reorganize
     (non-trivial changes in separate commits)

- **Refactor Workflow** (for reorganizations with no behavior change):

  1. **Plan**: Understand current structure and desired changes
  2. **Code**: Make refactoring changes
  3. **Green**: Run tests to confirm no behavior change
  4. **Commit**: Commit the refactoring

### Key Principles

- Add tests first for new features/fixes - do not implement without a failing
  test first
- If bugs discovered during implementation, add to TODO.md for test + fix
  together
- Keep existing tests passing throughout refactoring
- **Prefer integration tests over unit tests** - they are more robust to
  implementation changes
- **Do not write unit tests for existing code** unless you plan to modify it
- Add tests first, period. Do not fix bugs or add features without a failing
  test first. If identified during implementation, add to TODO.md for test and
  fix together.
- Post-hoc testing: When writing tests for existing code/fixes, validate tests
  by reverting the fix, confirming test failure, then restoring the fix and
  confirming test passes. This ensures tests actually test the intended
  behavior.

## Test Execution

- `just agent-test ...` to run full suite or specific tests
- `just full-diff=true agent` or `just full-diff=true agent-test` for full
  assert diffs
- Never run pytest or `just test` directly, always use `just agent-test` which
  adds flags to prevent context bloat and format errors for machine readability
