# Errorformat Reference

Complete, token-efficient API reference for the reviewdog/errorformat tool.

## Overview

**errorformat** is a Go implementation of Vim's quickfix errorformat functionality. It parses compiler, linter, and static analyzer output using Vim-style errorformat patterns, converting error messages into structured data.

**Compatibility**: ~90% compatible with Vim's errorformat syntax. Does not support Vim regex.

**Installation**:
```bash
go install github.com/reviewdog/errorformat/cmd/errorformat@latest
```

---

## Command-Line Usage

### Basic Syntax

```bash
errorformat [flags] [errorformat ...]
```

### Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `-name=<tool>` | string | required | Use predefined errorformat for tool |
| `-w=<format>` | string | template | Output writer format |
| `-f=<template>` | string | `{{.String}}` | Format template for -w=template output |
| `-list` | bool | false | List all available predefined errorformats |
| `-sarif.tool-name=<name>` | string | (inferred) | Tool name for SARIF output |
| `-h`, `--help` | bool | false | Show help message |

### Output Formats (-w flag)

| Format | Description | Use Case |
|--------|-------------|----------|
| `template` | Default text format with custom template | Human-readable output, custom formatting |
| `jsonl` | JSON Lines (one JSON object per line) | Programmatic parsing, integration |
| `checkstyle` | Checkstyle XML format | CI/CD integration (Jenkins, etc.) |
| `sarif` | Static Analysis Results Interchange Format | Standard security/analysis reporting |

---

## Errorformat Syntax

### Format Codes (Basic)

| Code | Matches | Example Input | Captured |
|------|---------|----------------|----------|
| `%f` | Filename | `/path/to/file.py` | File path |
| `%l` | Line number | `42` | Line number |
| `%c` | Column number | `10` | Column number |
| `%m` | Message text | `error message here` | Error message |
| `%t` | Error type (single char) | `E` or `W` | Type (E=error, W=warning, I=info) |
| `%v` | Virtual column | `10` | Virtual column position |
| `%n` | Error number | `123` | Error code/number |
| `%p` | Pointer line | `^` (preceded by spaces) | Column position via caret |
| `%r` | Rest of line | `remaining text` | Text to end of line |
| `%s` | Search text | `text to find` | Literal string to search |

### Multi-line Error Codes

| Code | Purpose | Usage |
|------|---------|-------|
| `%E` | Error start (multi-line) | Marks beginning of multi-line error |
| `%A` | Any message start | Generic multi-line start (error/warning) |
| `%C` | Continuation line | Middle of multi-line message |
| `%Z` | End of multi-line | Marks end of multi-line message |
| `%G` | General message | Skipped line (informational) |

### Modifiers

| Modifier | Position | Effect |
|----------|----------|--------|
| `%+` | Before uppercase code | **Include** entire matching line in message |
| `%-` | Before uppercase code | **Exclude** matching line from output |
| `%%` | Literal percent | Matches literal `%` character |

**Usage**: `%+A`, `%-G`, `%%`

### Special Characters and Escaping

| Character | Escape | Description |
|-----------|--------|-------------|
| `,` (comma) | `\,` | Pattern separator; precede with backslash to include literal comma |
| `\` (backslash) | `\\` | Escape character; use `\\` for literal backslash |
| ` ` (space) | `\ ` | Literal space in pattern |
| `.` (dot) | `.` | Literal dot (not wildcard in errorformat) |
| `%` (percent) | `%%` | Literal percent sign |

**Example escaping**:
```
%f\:%l\:\ %m        # Escaped colon and space
directory\,\ name   # Escaped comma in pattern
```

### Wildcards and Patterns

| Pattern | Matches |
|---------|---------|
| `%.%#` | Any text (wildcard, equivalent to `.*` in regex) |
| `[chars]` | Character class (not fully supported) |
| `%\|` | Alternation (limited support) |

### Directory Stack Codes

| Code | Purpose | Usage |
|------|---------|-------|
| `%D` | Enter directory | `%D%f` captures entering directory |
| `%X` | Leave directory | `%X%f` captures leaving directory |

Used with `%f` to track directory changes for relative file paths.

---

## Predefined Tool Formats (-name option)

### Common Tools

| Tool Name | Format Pattern | Typical Output |
|-----------|----------------|-----------------|
| `ruff` | `%f:%l:%c: %m` | `file.py:10:5: E501 line too long` |
| `flake8` | `%f:%l:%c: %m` | `file.py:10:5: E501 line too long` |
| `mypy` | `%f:%l:%c: %t%*[^:]: %m` | `file.py:10:5: error: Type mismatch` |
| `pylint` | `%f:%l: %m` | `file.py:10: error: Invalid name` |
| `black` | (formatting tool, no errors) | N/A |
| `isort` | (formatting tool, no errors) | N/A |
| `pytest` | `%f:%l:%m` | `test_file.py:42:AssertionError: ...` |
| `gcc` | `%f:%l:%c: %t%*[^:]: %m` | `main.c:10:5: error: undefined reference` |
| `clang` | `%f:%l:%c: %t%*[^:]: %m` | `main.c:10:5: error: ...` |
| `go` | `%f:%l:%c: %m` | `main.go:10:5: undefined: variable` |
| `rust` | `%f:%l:%c: %t%*[^:]: %m` | `main.rs:10:5: error: ...` |
| `node` | `%f:%l:%c: %m` | `file.js:10:5: error message` |
| `eslint` | `%f:%l:%c: %t%*[^:]: %m` | `file.js:10:5: error: ...` |
| `tsc` | `%f:%l:%c: %m` | `file.ts:10:5: Type error` |
| `java` | `%f:%l: %m` | `Main.java:10: error: ...` |
| `kotlinc` | `%f:%l:%c: %t%*[^:]: %m` | `Main.kt:10:5: error: ...` |
| `make` | `%D%*[^E]%f%*[^:]: %m` | `make: Entering directory '/path/to/file: error` |
| `cmake` | `%f:%l: %m` | `CMakeLists.txt:10: error: ...` |

### List All Available Tools

```bash
errorformat -list
```

Output: Complete list of predefined tool names supported by errorformat.

---

## CLI Examples

### Basic Usage: Parse ruff output

```bash
ruff check | errorformat -name=ruff
```

**Output** (default template):
```
file.py:10:5: E501 line too long
file.py:15:8: F841 local variable assigned but never used
```

### Custom Template Format

```bash
pylint main.py | errorformat -name=pylint -w=template -f="{{.Filename}}:{{.Lnum}}: {{.Text}}"
```

### JSON Lines Output

```bash
mypy . | errorformat -name=mypy -w=jsonl
```

**Output**:
```json
{"filename":"file.py","lnum":10,"col":5,"end_lnum":10,"end_col":6,"text":"error: Type mismatch","type":"E","valid":true}
{"filename":"file.py","lnum":15,"col":1,"end_lnum":15,"end_col":10,"text":"error: Unused variable","type":"E","valid":true}
```

### Checkstyle XML Output

```bash
gcc main.c | errorformat -name=gcc -w=checkstyle
```

**Output**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<checkstyle version="8.0">
  <file name="main.c">
    <error line="10" column="5" severity="error" message="undefined reference to 'printf'" source="gcc"/>
  </file>
</checkstyle>
```

### SARIF Output

```bash
go vet ./... | errorformat -name=go -w=sarif -sarif.tool-name="go-vet"
```

### List Available Formats

```bash
errorformat -list
```

Shows all predefined tool names that can be used with `-name=` flag.

### Custom Errorformat Pattern

```bash
custom_tool output.txt | errorformat '%f:%l:%c: %t: %m'
```

Directly specify errorformat pattern without using predefined tool name.

### Multiple Patterns (Comma-separated)

```bash
tool_output | errorformat '%E%f:%l:%c: error: %m' '%C%.%#' '%Z'
```

For multi-line error parsing.

---

## Output Data Fields

### JSONL Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `filename` | string | Path to file with error |
| `lnum` | number | Line number (1-indexed) |
| `col` | number | Column number (1-indexed, optional) |
| `end_lnum` | number | End line number (optional, for multi-line) |
| `end_col` | number | End column number (optional, for multi-line) |
| `lines` | array | Array of text lines for the error |
| `text` | string | Main error message text |
| `type` | string | Error type: `E` (error), `W` (warning), `I` (info), or empty |
| `valid` | boolean | Whether entry is valid (matched pattern) |

### Template Output Fields

Available in template format with `{{.FieldName}}` syntax:

| Field | Description |
|-------|-------------|
| `{{.Filename}}` | File path |
| `{{.Lnum}}` | Line number |
| `{{.Col}}` | Column number |
| `{{.EndLnum}}` | End line number |
| `{{.EndCol}}` | End column number |
| `{{.Text}}` | Error message |
| `{{.Type}}` | Error type character |
| `{{.Valid}}` | Boolean validity flag |
| `{{.String}}` | Formatted error string (default) |

### Checkstyle Output Fields

| Attribute | Description |
|-----------|-------------|
| `file` | File name |
| `line` | Line number |
| `column` | Column number |
| `severity` | `error`, `warning`, or `info` |
| `message` | Error message |
| `source` | Tool name |

### SARIF Output Structure

SARIF (Static Analysis Results Interchange Format) - JSON-LD based format containing:
- Tool information
- Runs (analysis results)
- Results (individual findings with location, message, severity)
- Artifacts (file information)

---

## Pattern Examples

### Simple patterns

| Tool | Pattern | Example Output |
|------|---------|-----------------|
| Python | `%f:%l:%c: %m` | `script.py:10:5: error message` |
| JavaScript | `%f:%l:%c: %t%*[^:]: %m` | `app.js:10:5: error: message` |
| Java | `%f:%l: %m` | `Main.java:10: error message` |

### Multi-line patterns

| Tool | Pattern | Notes |
|------|---------|-------|
| GCC | `%E%f:%l:%c: error: %m` `%C%m` `%Z` | Start with error, continuation lines, end marker |
| Mypy | `%A%f:%l:%c: %m` `%C%.%#` | Start line, continuation (4+ spaces) |
| Pytest | `%E%f:%l` `%C%m` `%Z` | Test file, message lines, end marker |

### Directory tracking

```
%D%*[^E]%f      # Enter directory, path after 'E': <
%X%*[^L]%f      # Leave directory, path after 'L': <
```

---

## Common Patterns

### Parse ruff output

```bash
ruff check mymodule | errorformat -name=ruff -w=jsonl
```

Captures: `filename:line:col: code message`

### Parse mypy with multi-line notes

```bash
mypy . --show-column-numbers | errorformat -name=mypy -w=jsonl
```

Pattern handles:
- Main error line: `file:line:col: error: message`
- Note lines: `    note: additional info`

### Parse pytest failures

```bash
pytest tests/ -v | errorformat -name=pytest -w=jsonl
```

Captures:
- Test file location
- Assertion error messages
- Multi-line diffs

### Parse compiler errors

```bash
gcc -Wall main.c | errorformat -name=gcc -w=jsonl
```

Handles:
- Error/warning distinction
- Column numbers
- Multi-line compiler messages

### Integration with build system

```bash
make 2>&1 | errorformat -name=make -w=jsonl
```

Tracks:
- Directory changes (entering/leaving)
- Build errors
- Nested tool output (calls to other errorformat)

---

## Integration Patterns

### With reviewdog

```bash
golint ./... | errorformat -name=golint -w=checkstyle | reviewdog -f checkstyle
```

### In CI/CD

```bash
# Save as JUnit for Jenkins/GitLab
mypy . | errorformat -name=mypy -w=sarif > analysis-result.sarif
```

### Stream processing

```bash
# Consume JSONL output
tool output | errorformat -name=tool -w=jsonl | jq '.text'
```

Extract only error messages from JSON output.

### Custom formatting

```bash
# Format as "file(line,col): message"
gcc main.c | errorformat -name=gcc -w=template -f="{{.Filename}}({{.Lnum}},{{.Col}}): {{.Text}}"
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (errors parsed or input empty) |
| 1 | General error (invalid flags, input read failure) |
| 2 | Errorformat error (invalid pattern syntax) |

---

## Error Handling

### ErrorformatNotFoundError

**Condition**: errorformat binary not in PATH

**Resolution**:
```bash
go install github.com/reviewdog/errorformat/cmd/errorformat@latest
export PATH="$PATH:$(go env GOPATH)/bin"
```

### CalledProcessError

**Condition**: errorformat subprocess exits non-zero

**Causes**:
- Invalid pattern syntax
- I/O error reading input
- Unrecognized tool name with `-name=`

**Resolution**: Check pattern syntax, verify tool name with `errorformat -list`

---

## ANSI Code Handling

**Behavior**: errorformat preserves ANSI color codes in input output.

**If you need stripped output**:
```bash
tool_output | sed 's/\x1b\[[0-9;]*m//g' | errorformat -name=tool
```

Or use tool's `--no-color` option when available:
```bash
mypy --no-color | errorformat -name=mypy -w=jsonl
```

---

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Startup | 10-50ms | Binary load overhead (typical) |
| Parse rate | ~1000 lines/sec | Depends on pattern complexity |
| Memory | O(n) | Buffered line-by-line (small memory) |

**Optimization**: Stream large files for minimal memory usage.

---

## Version Information

- **Current**: Latest version published March 20, 2025
- **Stability**: Active maintenance, used by reviewdog and efm-langserver
- **License**: MIT

---

## Platform Support

| Platform | Support | Notes |
|----------|---------|-------|
| Linux | Full | Tested extensively |
| macOS | Full | Intel and ARM (M1+) |
| Windows | Full | Via WSL or native |
| POSIX | Full | sh, bash, zsh compatible |

---

## Related Tools

| Tool | Purpose | Integration |
|------|---------|-------------|
| reviewdog | Code review automation | Uses errorformat for parsing |
| efm-langserver | Language server | Uses errorformat for diagnostics |
| vim/neovim | Text editors | Native errorformat support |
| Syntastic/ALE | Vim plugins | Support errorformat patterns |

---

## Limitations

1. **90% Vim compatibility**: Some advanced Vim errorformat features not supported
2. **No Vim regex**: Patterns use simplified matching, not full Vim regex
3. **Limited character classes**: `[a-z]` style character classes not fully supported
4. **No lookahead/lookbehind**: Advanced regex assertions not supported
5. **No line anchors**: `^` and `$` not supported in patterns

**Workaround**: For unsupported features, write custom integration using Go library directly.

---

## Testing Output

Verify errorformat works with your tool:

```bash
# Test with sample output
echo "file.py:10:5: error message" | errorformat -w=jsonl '%f:%l:%c: %m'

# Expected output
{"filename":"file.py","lnum":10,"col":5,"lines":["error message"],"text":"error message","valid":true}
```

---

## Go API (Library)

For programmatic use in Go code:

```go
import "github.com/reviewdog/errorformat"

efm, _ := errorformat.NewErrorformat([]string{`%f:%l:%c: %m`})
scanner := efm.NewScanner(reader)
for scanner.Scan() {
    entry := scanner.Entry()
    // entry has: Filename, Lnum, Col, Text, Type, Valid
}
```

Key types:
- `Errorformat`: Multiple patterns
- `Scanner`: Iterates entries
- `Entry`: Single parsed error

---

## References

- **GitHub**: https://github.com/reviewdog/errorformat
- **Go Package**: https://pkg.go.dev/github.com/reviewdog/errorformat
- **Vim Docs**: `:help errorformat` (in Vim)
- **Vim Quickfix**: https://vimhelp.org/quickfix.txt.html
