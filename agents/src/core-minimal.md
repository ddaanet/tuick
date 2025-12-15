# Core Rules (Minimal - For Execution Agents)

## Critical Rules

**RULE 0:** When anything fails, STOP. Think. Output reasoning. Do not proceed
until you understand actual cause and have stated expectations.

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
