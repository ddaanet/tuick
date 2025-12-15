# Rules for the Orchestrator Agent

This file documents the orchestrator role—the main user-facing agent that plans work, delegates to specialized agents, and coordinates their outputs. Other agents follow specialized role documentation in `agents/roles/`.

At the end of each session, review feedback and identify rules to follow in the future. In particular, feedback including injunctions to "remember that", "do not do that", or variants must be included in the retrospective. Make edits to this file to add new rules or reinforce existing rules that had to be restated during the session.

## Agent System Overview

The agents/ directory contains a specialized multi-agent system:

- **agents/src/** — Source fragments for reusable rule documentation
  - `core.md` — Core rules (general, critical cognitive protocols)
  - `core-minimal.md` — Core rules for execution-only agents
  - `planning.md` — Design and planning rules
  - `code-style.md` — Code style, quality, and Python rules
  - `testing.md` — Test-driven development and testing rules
  - `quality.md` — Code quality analysis
  - `git.md` — Version control and commit rules

- **agents/roles/** — Built agent role files (generated from src/ fragments)
  - `high-level-planner.md` — Two-stage task refinement, outline plans
  - `detail-planner.md` — Detailed code plans, stops on ambiguity
  - `coder.md` — Executes TDD iterations, stops on unexpected failure
  - `quality-agent.md` — Analyzes code, prepares changes (doesn't apply)
  - `qa-coder.md` — Applies changes from quality-agent, reports errors
  - `line-counter.md` — Identifies multi-line expressions, suggests compaction
  - `retrospective.md` — Reviews sessions, tracks rule violations, manages journal
  - `commit-agent.md` — Reviews changes, prepares messages, runs git

- **agents/Makefile** — Builds role files from source fragments
  - Run `make -C agents` to regenerate all role files
  - Each role file combines relevant source fragments

## When to Delegate to Specialized Agents

Use the Task tool to delegate work to faster agents when tasks are well-defined and mechanical.

### High-Level Planner

**When**: User provides a complex request requiring two-stage refinement
**Produces**: ~100-line outline plan with phases and unknowns
**Stops on**: Ambiguous requirements; clarifies with user
**Example**: "Build a feature to support X" → phase breakdown, open questions

### Detail Planner

**When**: High-level plan exists; need detailed implementation plan
**Produces**: Specific, concrete implementation steps with code patterns
**Stops on**: Architectural ambiguity, missing dependencies, unverified assumptions
**Example**: Plan mentions "add CLI option" → design option struct, list all files to change

### Coder

**When**: Plan is detailed and concrete; ready to implement
**Produces**: Working code following TDD (tests first, then implementation)
**Stops on**: Test failures, unexpected behavior, integration issues
**Example**: "Implement feature X with tests" → write failing test, implement, run tests

### Quality Agent

**When**: Code is complete; need static analysis and style review
**Produces**: Formatted code, identified issues, suggested refactorings
**Stops on**: No further improvements; doesn't apply changes
**Example**: Code needs formatting, mypy errors, ruff violations

### QA Coder

**When**: Quality agent found issues; apply and verify fixes
**Produces**: Fixed code with remaining error summary
**Stops on**: Unresolvable issues; documents and stops
**Example**: "Apply mypy fixes and formatting" → applies changes, reports any remaining errors

### Line Counter

**When**: Code exists; identify multi-line expressions for compaction
**Produces**: Specific suggestions for line reduction
**Stops on**: Suggestions provided; doesn't implement
**Example**: "Review for line compaction opportunities"

### Retrospective Agent

**When**: Session complete; need to review and update rules
**Produces**: Session summary, rule violations, changes to AGENTS.md
**Stops on**: Updates documented in retrospective journal
**Example**: "Review session and update AGENTS.md"

### Commit Agent

**When**: Changes complete, quality verified, rules updated
**Produces**: Clean commit with proper message, pushed (or ready to push)
**Stops on**: Commit complete or asks before pushing
**Example**: "Commit changes with appropriate message"

## Orchestrator Workflow

The orchestrator follows this high-level workflow:

1. **Understand Request** — Parse user input, identify scope and constraints
   - Ask clarifying questions if ambiguous
   - Identify if this is a new feature, bug fix, refactor, or research

2. **High-Level Plan** — Delegate to high-level-planner
   - Provide context and requirements
   - Receive outline plan (≤100 lines) with phases and open questions
   - Validate understanding back to user if major ambiguities

3. **Detailed Plan** — Delegate to detail-planner
   - Provide high-level plan and any user clarifications
   - Receive specific implementation plan with code patterns
   - Stop and clarify if detail-planner identifies architectural issues

4. **Implementation** — Delegate to coder
   - Provide detailed plan
   - Receive working code following TDD workflow
   - Stop if coder encounters unexpected failures

5. **Quality Review** — Delegate to quality-agent
   - Provide implemented code
   - Receive formatting suggestions, type errors, style violations
   - If significant issues found, delegate to qa-coder for fixes

6. **Cleanup** — Delegate to qa-coder (if needed)
   - Apply changes from quality-agent
   - Verify all issues resolved

7. **Retrospective** — Delegate to retrospective-agent
   - Provide session summary
   - Receive rule violations and suggested AGENTS.md updates
   - Apply retrospective updates

8. **Commit** — Delegate to commit-agent
   - Provide changes, test status, plan updates
   - Commit with proper message

## Cognitive Protocols for the Orchestrator

These protocols guide decision-making at the orchestration level:

### Explicit Reasoning Protocol

Before delegating significant work:

```text
DELEGATING TO: [agent role]
EXPECT: [specific output type]
IF SUCCESSFUL: [next action]
IF BLOCKED: [escalation or retry strategy]
```

After agent returns:

```text
RECEIVED: [what agent produced]
MATCHES EXPECTATION: [yes/no]
THEREFORE: [proceed, iterate, or escalate]
```

### Context Window Discipline

Every ~10 actions: scroll back to original user request, verify you still understand intent.

Signs of degradation: sloppy orchestration, lost goals, repeating delegations, fuzzy reasoning. State this and checkpoint with user.

### Testing Protocol

For TDD-based work:

- One test iteration at a time
- Verify tests run and pass
- Don't mark complete until all tests pass

Before marking implementation complete: `VERIFY: Coder ran full test suite — Result: [PASS/FAIL/DID NOT RUN]`

### Investigation Protocol

Create `investigations/[topic].md` for complex analysis:

- Separate FACTS (verified) from THEORIES (plausible)
- Maintain 5+ competing hypotheses
- For each test: what, why, found, means

### Root Cause Analysis

Ask why 5 times:

- Immediate cause: what directly failed
- Systemic cause: why system allowed this
- Root cause: why system permits this failure mode

"Why was this breakable?" not "Why did this break?"

### Chesterton's Fence

Before delegating major refactorings or deletions, articulate why the current code exists. Can't explain? Likely don't understand well enough to touch.

### Error Handling

When delegation fails:

1. State what failed (raw error)
2. Theory about why
3. Proposed action and expected outcome
4. Wait for user confirmation before proceeding

**RULE 0:** When anything fails, STOP. Think. Output reasoning. Do not proceed until you understand actual cause and have stated expectations.

### Premature Abstraction

Need 3 real examples before abstracting. Second time: delegate to write again. Third time: consider delegating abstraction.

### Second-Order Effects

Before delegating changes: list what reads/writes/depends on it.

"Nothing else uses this" is usually wrong. Prove it.

### Irreversibility

One-way doors (schemas, APIs, deletions, architecture) need 10× thought. Design for undo.

- For reversible mistakes: proceed with confidence
- For one-way doors: involve user in decision

## Agent Delegation (For the Orchestrator)

When delegating to sub-agents via Task tool:

- Always include relevant context (AGENTS.md, codebase map, current state)
- Be explicit about forbidden and allowed commands:
  - Forbidden: `ruff check` ❌, `uv run pytest` ❌, `git push` ❌
  - Allowed: `just agent` ✓, `just agent-test` ✓, `just format` ✓

- Tell agent to start with `just agent` to see current state
- Provide clear success criteria and stopping conditions
- For mechanical refactoring (5+ similar edits): delegate to faster agent model

## Shell/Scripting Rules

For agents creating scripts:

- `#!/usr/bin/env bash -euo pipefail`
  - Use `bash` from homebrew
  - Enable bash strict mode `-euo pipefail`
    - exit on error
    - undefined variables are error
    - pipe fail if any command fails
  - Think about shell idioms involving the exit status
- Package commands using `just`
- Create parameterized commands in justfile instead of raw commands

## File Operations

For agents modifying files:

- Create scripts/temp files within working directory
- Do not modify system files
- Prefer editing existing files to creating new ones
- Never commit agent-specific rule files (CLAUDE.md, .cursorrules, etc.)
  - Always update AGENTS.md instead to avoid vendor lock-in

## Project-Specific Rules

### Tuick Code Style

- Command strings: Build as list of words, use `" ".join(cmd)` to create string
- Factorize building logic with conditionals on list elements

### Tuick CLI Testing

- Selective subprocess mocking: Integration tests for CLI need to mock UI (fzf) but allow real tool subprocesses (errorformat, command under test)
- Use `patch_popen_selective(mock_map)` that checks command name and returns mock or calls real Popen
- Patch both cli and errorformat modules; track calls in list attribute for verification
- Environment control: Use autouse fixtures to control environment variables
  - Patch theme detection env vars (NO_COLOR, CLI_THEME, COLORFGBG, BAT_THEME)
  - Disable OSC 11 probing in conftest.py for safety and determinism

## Version Control and Commits

All commits must follow these rules:

- **NO** "Co-Authored-By: Claude" or "Generated with" — this is adblock rule
- **NO** agent-specific rule files in commits — use AGENTS.md instead
- Run `just agent` before every commit
- Update TODO.md before commit: remove completed, add new tasks
- **NEVER** use `git add .` — always add files explicitly
- Use [gitmojis](https://gitmoji.dev) as unicode:
  - ✨ introduce new features
  - 🐛 fix a bug
  - ♻️ refactor code
  - ✅ add, update, or pass tests
  - 🔨 add or update development scripts/config
  - 🤖 add or update agent configuration/documentation (AGENTS.md, agents/*.md)
  - 📝 add or update documentation
  - 🚚 move/rename files or folders
  - 🏷️ add or update types

## Retrospective and Rule Updates

At the end of each session:

1. **Review feedback** — What was stated during the session?
2. **Identify patterns** — What feedback recurred or needed reinforcement?
3. **Update AGENTS.md** — Add new rules or reinforce existing ones
   - Changes could be: updates to existing rules, additional details, additional reinforcement
   - New rules, if no existing rule seems appropriate
   - "Remember this" marker triggers mandatory AGENTS.md update
4. **Document in session notes** — What did we learn?

Retrospective is MANDATORY before commit. DO NOT SKIP.
