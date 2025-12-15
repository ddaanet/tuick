# Core Rules (Minimal - For Execution Agents)

## Development Commands

**All development commands must use `just` recipes.** Do NOT advertise or use direct `uv run` commands.

**Available recipes:**
- `just agent` - Agent workflow: check, test with minimal output
- `just agent-test [ARGS]` - Run tests with minimal output
- `just format` - Reformat code

## Critical Rules

**RULE 0:** When anything fails, STOP. Think. Output reasoning. Do not proceed until you understand actual cause and have stated expectations.

### On Failure

When anything fails, next output is explanation, not retry:
1. State what failed (raw error)
2. Theory about why
3. Proposed action and expected outcome
4. Wait for confirmation before proceeding

### Handoff Protocol

When stopping, document:
1. State of work (done/in progress/untouched)
2. Current blockers
3. Files touched

## Tooling

- `just format` to format code
- `just agent` to run all checks and tests
- `just agent-test` to run tests with machine-readable output
- NEVER run `ruff`, `mypy`, or `pytest` directly. ALWAYS use just commands
