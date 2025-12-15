# Code Style and Quality Rules

## General Principles

- Avoid confusing names: module/file names must be clearly distinct. Don't use names differing by one character (errorformat.py vs errorformats.py). Use descriptive, distinct names (tool_registry.py vs errorformat.py).
- Validate input once when entering system, handle errors explicitly
- Include docstrings for functions/modules
- Limit lines to 88 characters (project standard)
- Write only necessary code for required use cases
- Do not write speculative and boilerplate code
- Factor duplicated logic: extract helper functions when same logic appears twice, even for small chunks (5-6 lines). Reduces maintenance burden and ensures consistency
- All other things being equal, prefer code that takes fewer lines
- Consider intermediate variables where they make code more compact. For command-line options/flags, extract meaningful intermediate lists like `reload_opts`, `verbose_flag` that represent cohesive option sets
- Do not write trivial docstrings, except for important public objects
- Helper function docstrings must not exceed implementation length. One-line docstrings for simple helpers. Detailed Args/Returns only for public APIs.
- Preserve compact notation for function signatures: keep on one line when possible. For function calls with long arguments, use intermediate variables to prevent wrapping and reduce vertical space waste.
- Docstring first line must be concise, details go in body or comments
- Implementation details belong in comments, not docstrings
- Streaming: Never buffer entire input in memory when processing iterables. Process line-by-line, yield results incrementally. Use generator functions, not list() calls that force materialization. MUST maintain streaming: consume one item, process, yield result, repeat.
- Performance: prefer built-in functions and stdlib over manual iteration when performance matters. Example: use `re.split()` over char-by-char loops for string splitting.

## Problem Solving

- **Root cause analysis**: See Cognitive Protocols > Root Cause Analysis. Ask why 5 times to identify systemic and root causes, not just immediate causes.
- **Respect user interrupts**: If user repeatedly rejects tool use, stop and wait for explicit direction. Don't keep trying variations - ask what to do.
- **On failure**: See Cognitive Protocols > On Failure. Stop, explain, propose, wait for confirmation. Never retry without understanding.

## Python

- Require Python >=3.14: recursive types, no future, no quotes
- Write fully typed code with modern hints (`list[T]` not `List[T]`)
- Keep try blocks minimal to catch only intended errors
- Exception handling: NEVER use `except Exception: pass` - it hides bugs. Instead, catch specific exceptions around specific statements with minimal scope. Example: wrap only the statement expected to fail, not entire blocks. Use bytes literals (b"\x1b") instead of string.encode().
- All imports at module level, except there is a specific reason not to
- Unused parameters: Mark with leading underscore (`_param`) rather than noqa comments. More Pythonic and makes intent explicit.
- Don't start unittest docstrings with "Test"
- Exception chaining: Use `raise NewException from exc` when re-raising or transforming exceptions in except blocks. Preserves stack trace and makes debugging easier. Example: `except FileNotFoundError as exc: raise CustomError from exc`. Follow ruff B904.
- Enum design: Use `StrEnum` with `auto()` for string enums. For option types with special values, create separate enum (e.g., `ColorTheme` vs `ColorThemeAuto`), then use type alias: `type ColorThemeOption = ColorTheme | ColorThemeAuto`.

### Python Version and Type Annotations

This project uses **Python 3.14t (freethreaded)**.

Follow these type annotation rules:

- **NO** `from __future__ import annotations` - not needed in Python 3.14
- **NO** `ForwardRef` - Python 3.14 has native forward reference support
- **NO** string type annotations (e.g., `"ClassName"`) - use direct class references
- **NO** `TypeVar` for generics - use Python 3.14 native generic syntax with `type` parameter lists
- Use native Python 3.14 forward reference capabilities

### Datetime and Timezone Handling

**CRITICAL**: Do not use naive datetimes. A naive datetime is NOT a datetime in the system timezone.

### Documentation vs Comments

**Docstrings are for users, not implementation details.**

```python
# WRONG - implementation details in docstring
class Foo:
    """Request model.

    Note: FBT003 suppressed for Field() - Pydantic idiom.
    """

# RIGHT - implementation comment above code
class Foo:
    """Request model."""

    # FBT003 suppressed - Pydantic idiom uses positional bool default
    field: bool = Field(True, description="...")
```

### Plan File Management

Git history shows what was done. Plan files show what remains.

- Remove completed tasks from TODO.md
- Don't list "recent fixes" or "completed items" in plan files
- Git commits document what changed
- Plan files (TODO.md) only show remaining work

## Type Hints

- TYPE_CHECKING blocks: Import types only used in annotations under `if typing.TYPE_CHECKING:` to avoid runtime overhead
- Use most general type that works: `Iterable` over `Iterator` when only iteration needed
- Missing values: Use `None` for missing/optional data, not `0` or `''`
- Context managers: Use `Self` type (from typing) for `__enter__` return annotation in context manager classes

## Function Design

- **newfunc**: Write new functions instead of adding optional parameters for alternate behavior paths
- If dispatch is needed, use polymorphism or explicit dispatch functions
- Example: `split_blocks_auto()` dispatches to `split_blocks()` or `split_blocks_errorformat()` based on tool
- Optional parameters: don't make parameters optional if they're always provided at call sites. Simpler to require them. Use `Optional` only for truly optional values.
- Separate intent from behavior: when a feature can be triggered explicitly or implicitly (e.g., `--top` flag vs auto-detected build system), use separate parameters for user intent vs implementation behavior. Example: `explicit_top` (preserve flag in bindings) vs `top_mode` (use top-mode parsing). Prevents unintended propagation when auto-detection and explicit flags must behave differently.
- Boolean parameters: Use keyword-only arguments for boolean parameters to improve call-site clarity. Add `*,` separator before boolean params:
  ```python
  def process(data: str, *, stream: bool = True) -> None:
      """Process data with optional streaming."""
      ...

  # Call site is clear:
  process(data, stream=False)  # Obviously disabling streaming
  process(data, False)  # Error: positional arg not allowed
  ```
