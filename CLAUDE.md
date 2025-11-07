# Claude-Specific Development Rules

Follow all rules in @AGENTS.md - this file contains Claude-specific directives only.

## Task Delegation

- Simple mechanical refactoring: use Task tool with `model="haiku"` to save context and speed
  - Examples: renaming types across files, updating function signatures, fixing imports
  - When you find yourself doing 5+ similar edits, delegate to haiku
- Complex logic changes or new features: continue with current model

## Tool Usage

- Prefer Task tool for any multi-step work that can be described clearly
- Use haiku model for well-defined, mechanical tasks
- Use current model for tasks requiring architectural decisions
