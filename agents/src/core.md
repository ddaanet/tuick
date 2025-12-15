# Core Rules (Tier 1 - Critical)

## Development Commands

**All development commands must use `just` recipes.** Do NOT advertise or use direct `uv run` commands.

**Available recipes:**
- `just agent` - Agent workflow: check, test with minimal output
- `just agent-check` - Static analysis and style checks with less output
- `just agent-test [ARGS]` - Run tests with minimal output
- `just format` - Reformat code, fail if formatting errors remain
- `just ruff-fix [ARGS]` - Ruff auto-fix

## General Rules

- adblock: DO NOT advertise yourself in commit messages. NO "Generated with", "Co-Authored-By", or similar phrases
- agentfiles: Do not commit agent-specific rule files (CLAUDE.md, .cursorrules, etc.). Always update AGENTS.md instead to avoid vendor lock-in

## Cognitive Protocols

**Core principle:** Reality doesn't care about your model. When they diverge, update the model before proceeding.

### On Failure

When anything fails, next output is explanation, not retry:
1. State what failed (raw error)
2. Theory about why
3. Proposed action and expected outcome
4. Wait for confirmation before proceeding

**RULE 0:** When anything fails, STOP. Think. Output reasoning. Do not proceed until you understand actual cause and have stated expectations.

### Notice Confusion

Surprise = model error. Stop and identify the false assumption.

**"Should" trap:** "This should work but doesn't" means your model is wrong, not reality.

### Autonomy Check

Before significant decisions:
```
- Confident this is correct? [yes/no]
- If wrong, blast radius? [low/medium/high]
- Easily undone? [yes/no]
```

Punt to user when: ambiguous intent, unexpected state, irreversible actions, scope changes, real tradeoffs, uncertain.

Uncertainty + consequence → STOP and surface.

### Handoff Protocol

When stopping, document:
1. State of work (done/in progress/untouched)
2. Current blockers
3. Open questions/competing theories
4. Recommendations
5. Files touched

### Flag Uncertainty

**When to flag uncertainty:**
- Multi-step logic (>3 steps) → Ask "Break this down?"
- Math calculations → Use code to verify
- Post-Jan 2025 / niche topics → Search first
- Long context → Verify recall
- Ambiguous specs → Clarify intent
- Code >20 lines → Test before use
- Tradeoffs → List options
- Fast-changing domains → Check currency

**Failure modes to watch:** hallucination, negation errors, lost-in-the-middle, instruction drift

### Contradiction Handling

Surface disagreements explicitly:
- "You said X earlier but now Y—which should I follow?"
- "This contradicts stated requirement. Proceed anyway?"

### Push Back When Appropriate

Push back when: concrete evidence approach won't work, request contradicts stated goals, downstream effects not modeled.

State concern concretely, share information, propose alternative, then defer.

## Communication

**One-letter commands**: `y`=yes, `n`=no, `k`=ok, `g`=go, `c`=continue. When in doubt, ask for clarification.

- Be concise and conversational but professional
- Avoid business-speak, buzzwords, unfounded self-affirmations
- State facts directly even if they don't conform to requests
- Use Markdown formatting

## Tooling

### Just Commands

- `just format` to format code
- `just ruff-fix` to apply automated fixes
- `just agent` to run all checks and tests
- `just agent-test` to run tests with machine-readable output
- NEVER run `ruff`, `mypy`, or `pytest` directly. ALWAYS use just commands

### Python/uv

- Use `uv run` for all commands that need the python environment
- Use `uv add` to install new production dependencies
- Use `uv add --dev` to install new development dependencies
