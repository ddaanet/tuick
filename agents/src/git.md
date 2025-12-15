# Git Workflow and Commit Rules

## Development Workflow - Commit Workflow

1. **Implement**: Follow TDD or Refactor workflow
2. **Validate**: Run `just agent` before commit to verify all checks pass
3. **Update TODO.md**: Remove completed tasks, add new tasks identified during implementation
4. **Retrospective**: MANDATORY before commit. Review session, identify learnings, update AGENTS.md if needed. DO NOT SKIP.
   - Retrospective meta-rule: Always capture recurring feedback here. When a reminder repeats (including "remember this"/RMMBR), either add a new rule or reinforce the existing one so future sessions do not need the same reminder.
5. **Commit**: Short informative message with gitmoji

## Git Commit Messages

- **DO NOT** add "Co-Authored-By: Claude" or any AI attribution to commit messages
- **DO NOT** advertise AI assistance in commit messages ("Generated with", etc.)
- Keep commit messages professional and focused on the changes
- Describe actual changes made, not original task descriptions.
- Use [gitmojis] as unicode. Common ones:
  - ✨ introduce new features
  - 🐛 fix a bug
  - ♻️ refactor code
  - ✅ add, update, or pass tests
  - 🔨 add or update development scripts/config
  - 🤖 add or update agent configuration/documentation (AGENTS.md, agents/*.md)
  - 📝 add or update documentation
  - 🚚 move/rename files or folders
  - 🏷️ add or update types
- Do not include complete content in commit messages - summarize changes concisely

[gitmojis]: https://gitmoji.dev

## Version Control

- Commit with short informative messages
- Use gitmojis (https://gitmoji.dev) as unicode
- `just agent` before every commit, to run all checks and tests
- Update TODO.md before commit: remove completed tasks, add new tasks identified during implementation
- **NEVER** use `git add .` or `git add -A` - always add specific files explicitly (e.g., `git add AGENTS.md`). This prevents accidentally committing unintended changes.
