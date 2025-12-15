# Design and Planning Rules

## Architecture

- **datafirst**: Design data structures first: names, attributes, types,
  docstrings. Code design flows from data structure design
- **Deslop** (condense/simplify) generated code: remove unnecessary comments,
  blank lines, redundancy
- Make code concise while retaining functionality and readability
- Avoid trivial data structures: if map values are computable or identical to
  keys, use simpler structure (set instead of dict with identity mapping)
- Reuse code with shared intent: check existing patterns in codebase before
  implementing utilities. Use established idioms (Path.name vs os.path.basename)
- Reuse existing infrastructure: before adding new environment variables or IPC
  mechanisms, check if existing ones can serve the purpose. Reduces complexity
  and maintenance burden.

## Planning

- Keep plans concise: under 200 lines, outline level
- Document unknowns as open questions for research
- Do not make assumptions about implementation details
- Expect iterative refinement through conversation
- Validate understanding: Before finalizing plans or making changes, reformulate
  your understanding back to the user for confirmation. Present concrete
  examples of the proposed behavior.
- Use appendices for supporting information
- Create/update codebase map early for session continuity
- In plan mode: no file writes until plan approved
- Read documentation thoroughly: understand actual tool behavior before
  implementing integrations, don't rely on assumptions
- Be precise about data formats: distinguish between terminators vs separators
  (null-terminated means `\0` after each item; null-separated means `\0` between
  items). Document format specs accurately.

## Interface Design

- Present usage examples before implementation details when designing interfaces
- Show concrete examples of how users will interact with the system
- Validate that common cases are simple and require minimal configuration

## Documentation

### Codebase Map

- Location: `docs/codebase-map.md`
- Purpose: Token-efficient reference for understanding architecture
- Update when: major architectural changes, new modules, data flow changes
- Keep concise: focus on structure and data flow, not implementation details
- Update atomically: include map updates in feature commits, not separately

### Reference Documentation

- **When integrating external tools**: Create or read reference documentation
  BEFORE designing interfaces. Verify actual tool behavior (argument passing,
  quoting, field substitution, etc.) rather than assuming. Incorrect assumptions
  lead to redesign work.
- **Testing tool integrations**: Use helper scripts (like `fmt_ef.py`) to test
  patterns with actual tool output before writing integration code. Run real
  examples through different pattern combinations to verify behavior.
