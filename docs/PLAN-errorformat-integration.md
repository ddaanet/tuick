# Feature Plan: Reviewdog/Errorformat Integration

**Created**: 2025-11-09
**Status**: Approved - Ready for Implementation

## Goal

Add `tuick --format` command for error parsing. Build tools invoke it to format checker output.

## Control Flow

```
tuick {build-command}
  → (in-process) run build-command
      → build tool calls: tuick --format {checker}
          → errorformat subprocess + checker
          → output: blocks to stdout
  → blocks → fzf (--read0 --delimiter=\x1f --with-nth=6)
  → watchexec monitors files
      → sends reload to fzf HTTP
  → fzf reload: tuick --reload {build-command}
      → subprocess: build-command
          → tuick --format {checker}
              → blocks
  → fzf select: tuick --select {1} {2} {3} ...
```

**Example**:
```bash
# justfile
check:
    tuick --format ruff check
    tuick --format mypy .

# User runs
tuick just check
```

## Components

### `tuick --format COMMAND ...`

Parse checker output into blocks.

**Input**: Command that produces errors (ruff, mypy, etc.)

**Processing**:
1. Auto-detect format from command name
2. Run command, capture stdout
3. Strip ANSI codes for parsing
4. Parse with errorformat subprocess
5. Detect block boundaries (using errorformat line types)
6. Extract locations (file, line, col)
7. Preserve ANSI codes in content

**Output**: `file\x1fline\x1fcol\x1fend-line\x1fend-col\x1fcontent\0`

**Options**:
- `-f auto` (default): detect from command
- `-f <name>`: explicit format name
- `-e <pattern>`: custom errorformat pattern

### `tuick COMMAND` (list mode, default)

Orchestrate build → fzf.

**Processing**:
1. Run build command in-process
2. Collect blocks from stdout
3. Spawn fzf with delimiter config
4. Setup watchexec integration
5. Handle reload/select callbacks
6. Print last output on exit
7. Save raw output separately

### Block Format

```
file\x1fline\x1fcol\x1fend-line\x1fend-col\x1fcontent\0
```

**Fields**:
1-5: Location (empty for informational blocks)
6: Original text with ANSI codes (multiple lines joined with \n)

**fzf config**: `--delimiter=\x1f --with-nth=6`

### Block Boundaries

How does errorformat indicate block structure?
- Multi-line patterns: `%A` (start), `%C` (continuation), `%Z` (end)
- Does errorformat output metadata about line types?
- Or infer from location changes?

Research required.

## Tool Detection

```python
ERRORFORMAT_MAP = {
    "ruff": "%f:%l:%c: %m",
    "mypy": "%f:%l:%c: %t%*[^:]: %m",
    "flake8": "%f:%l:%c: %m",
    "pylint": "%f:%l: %m",
    "pytest": "%f:%l: %m",
}

def detect_tool(cmd: list[str]) -> str:
    # ["ruff", "check"] → "ruff"
    # ["python", "-m", "pytest"] → "pytest"
```

## Sequential Commits (TDD)

### 1. Add --format to CLI
- Route to format_command()
- Options: -f, -e
- Tests: routing, options

### 2. Tool detection
- `errorformats.py`: map, detect_tool()
- Tests: detection logic

### 3. Errorformat wrapper
- `errorformat.py`: subprocess, parse output
- Strip ANSI → errorformat → extract locations
- Research: block boundary detection
- Tests: location extraction

### 4. Block assembly
- `blocks.py`: buffer, boundaries, format
- Apply ANSI dim to informational
- Tests: block formation

### 5. Implement format_command
- Wire: detect → run command → errorformat → blocks
- Tests: end-to-end

### 6. Update list_command for blocks
- Collect blocks from command output
- Configure fzf with delimiter
- Update CallbackCommands bindings
- Tests: integration

### 7. Update select_command
- Receive location fields from fzf
- Build FileLocation from fields
- Tests: selection

### 8. Update reload_command
- Ensure format propagation
- Tests: reload preserves format

### 9. Documentation
- README, codebase-map.md, errorformat-guide.md
- Update TODO.md

## Open Questions

- How does errorformat handle multi-line blocks?
- Does errorformat expose line type metadata?
- Does errorformat strip ANSI codes?
- How to detect block boundaries from errorformat output?

## Success Criteria

- [ ] Build tool can call `tuick --format checker`
- [ ] Blocks output correctly formatted
- [ ] fzf shows only content field
- [ ] Select extracts location from fields
- [ ] Reload works through build tool
- [ ] Tests pass: `just agent`

## Appendix A: Errorformat Research Findings

### Output Formats

From reviewdog/errorformat research:

**errorformat CLI** outputs in these modes:
- Default: prints matched errors line by line
- Format: `file:line:col: message` (or custom format)
- Does NOT provide structured output (no JSON, no delimiters)

**Key limitations**:
- No built-in block grouping
- No line type metadata in output
- ANSI handling: unknown, requires testing

### Multi-line Block Detection

Errorformat supports patterns for multi-line errors:
- `%A` - start of multi-line error
- `%C` - continuation line
- `%Z` - end of multi-line error
- `%+` - multi-line message continuation

**Unknown**: How these are represented in errorformat output.

**Investigation needed**:
1. Test errorformat with multi-line pattern
2. Check if output includes block markers
3. If not, implement block detection from location changes

### ANSI Code Handling

**Unknown**: Does errorformat strip ANSI codes?

**Test approach**:
1. Pipe ANSI-colored output through errorformat
2. Check if colors are stripped or preserved
3. Document behavior

If errorformat doesn't strip ANSI:
- We strip before passing to errorformat
- Keep original for output

### Alternative: Parse errorformat Pattern Definition

Instead of using errorformat as subprocess, parse the pattern ourselves:
- Convert Vim errorformat to regex
- Apply regex to lines
- Detect blocks from pattern structure

**Pros**: Full control, no subprocess overhead
**Cons**: Need to implement Vim errorformat parser

Consider if errorformat subprocess is inadequate.

## Appendix B: Block Boundary Strategies

### Strategy 1: Location Change

New block when:
- File changes
- Line number changes significantly (not +1)
- Blank line appears

**Simple but may split related errors.**

### Strategy 2: State Machine (Current Approach)

Current parser.py uses state machine with:
- `NOTE_CONTEXT` state for mypy notes
- `PYTEST_BLOCK` state for pytest sections
- `SUMMARY` state for summary lines

**Port to errorformat-based parser if needed.**

### Strategy 3: Pattern-Based

Use errorformat multi-line patterns to define boundaries:
- Pattern with `%A...%Z` defines a block
- Everything between `%A` and `%Z` is one block

**Requires errorformat to expose block structure.**

### Strategy 4: Hybrid

Combine strategies:
- Use errorformat for location extraction
- Use heuristics (location change, blank lines) for boundaries
- Use state machine for special cases (pytest, mypy notes)

**Most robust but complex.**

## Appendix C: fzf Integration Details

### Current fzf Configuration

From cli.py, current fzf call:
```python
open_fzf_process(
    blocks=blocks,
    bindings={
        "start": callback.start(),
        "load": callback.load(),
        "reload": callback.reload(),
        "select": callback.select(),
    },
    initial_port=server.port if server else None,
)
```

### Required Changes

**Add delimiter config**:
```python
fzf_args = [
    "--read0",
    "--delimiter=\x1f",
    "--with-nth=6",  # Show only content field
    # ... existing args
]
```

**Update select binding**:
```python
"--bind=enter:execute(tuick --select {1} {2} {3} {4} {5})"
```

fzf will substitute:
- `{1}` = file
- `{2}` = line
- `{3}` = col
- `{4}` = end-line
- `{5}` = end-col

### Field Extraction in select_command

```python
def select_command(
    file: str,
    line: str,
    col: str,
    end_line: str,
    end_col: str,
):
    """Handle selection from fzf."""
    if not file:
        # Informational block
        if verbose:
            print("Informational block (no location)")
        return

    location = FileLocation(
        path=file,
        row=int(line) if line else None,
        column=int(col) if col else None,
    )
    # Open editor...
```

## Appendix D: Dependencies

### Required: errorformat CLI

**Installation**:
```bash
go install github.com/reviewdog/errorformat/cmd/errorformat@latest
```

**Verify**:
```bash
errorformat --version
```

**Document in README**: errorformat is required dependency.

### Optional: reviewdog

Not needed for this implementation. We only use errorformat library.

## Appendix E: Backward Compatibility

### Migration Strategy

Keep current parser.py logic temporarily:
- Use for fallback if errorformat unavailable
- Use for testing comparison
- Remove after validation period

### Compatibility Checks

- [ ] Existing justfile commands still work
- [ ] Saved output format unchanged (raw text)
- [ ] Editor selection behavior unchanged
- [ ] Reload mechanism unchanged

## Appendix F: Testing Strategy

### Unit Tests

- Tool detection from various command formats
- Errorformat subprocess invocation
- Block assembly from parsed lines
- Field formatting with delimiters

### Integration Tests

- End-to-end: ruff check → blocks → fzf (mock fzf)
- End-to-end: mypy . → blocks
- End-to-end: pytest → blocks
- Reload: format preserved through reload
- Select: location extracted from fields

### Manual Testing

Create test files with known errors:
- `test_errors.py` with type errors, unused imports
- Run `tuick --format ruff check test_errors.py`
- Verify blocks formatted correctly
- Verify fzf displays content only
- Verify selection opens editor at correct location

## Appendix G: Performance Considerations

### Subprocess Overhead

errorformat subprocess per format command:
- Startup: ~10-50ms
- Processing: depends on output size

**Acceptable** for build tool integration (not latency-sensitive).

### Block Buffering

Must buffer lines until block complete:
- Memory usage: proportional to largest block
- Typically small (< 1KB per block)

**Monitor** if large blocks cause issues.

### Streaming Output

Emit blocks as soon as complete (don't wait for full command output).

Ensure prompt feedback for interactive use.
