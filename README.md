# Tuick, the Text-based User Interface for Compilers and checKers

Tuick is a terminal browser for compiler and linter errors.

Tuick is an terminal-based interactive error browser for command-line tools,
powered by [`fzf`] and [`errorformat`], with extensive text editor integration.

## Introduction

Tuick is the programmer's tool I was surprised did not exist yet.

  - Display the terminal output unmodified.
  - Standalone, not coupled with any text editor, and supports every editor.
  - Easy navigation and selection, with preview.
  - Updates automatically when source files change.
  - Requires no configuration, but can be configured if needed.

## Status

This tool is in early development. Feedback is more than welcome.

- **More error formats.** [reviewdog/errorformat] focuses on static analysis
  tools, and does not support compilers or interpreter stack traces. Please
  provide error dumps from your favorite tools, and I will add support for
  them.
- **Editor support.** If your text editor is not supported, please provide
  example commands to open files on a line, or line and column, and I will add
  support for it.
- **Windows support.** I made every effort to support Windows, but I have not
  tested it, so please report any issues.
- **Usability.** I welcome any feedback on the user interface.

## Features

- **Errorformat parsing**: Parse output from any tool with errorformat
  patterns. Right now, it has built-in support for tools supported by
  [reviewdog/errorformat], plus pytest and ruff. Improved support for mypy.
- **Multi-line error grouping**: Complex errors displayed as blocks, one
  keypress to navigate to the next error.
- **Editor integration**: Jump directly to error locations in your editor.
  Built-in support for 20 text editors. Can be configured to support any
  editor.
- **Auto-reload**: Automatic refresh on file changes using [`watchexec`],
  respecting .gitignore properly and other VCS ignore files.
- **Handle mixed output**: Can display a single list of errors from multiple
  tools, with potentially incompatible syntaxes.
- **Theme detection**: Automatic dark/light theme detection for fzf and bat.

[reviewdog/errorformat]: https://github.com/reviewdog/errorformat

## Quick Start

## Usage Modes

### List Mode (Default)

Default mode when the command name is not detected as a compiler. All output is
parsed using a single format.

```bash
tuick -- mypy src tests  # Parse and browse mypy errors
tuick -- ruff check      # Parse and browse ruff errors
```

The `--` is not necessary here, but it's a good habit to have, because it will
become necessary when you add options to the build command.

Run the command, if it outputs anything, parse it and start `fzf`.

- **Move:** up, down, space, backspace, page down, page up.
- **Open in editor:** Enter.
- **Toggle preview:** /, Ctrl-/
- **Manual reload:** r
- **Exit:** q, Esc, Ctrl-C

If a reload produces no output, tuick will exit.

If you exit manually, tuick prints the raw output of the last complete command
run.

### Top Mode

Run build systems with output from multiple commands.

```bash
tuick make          # Auto-detect make as build system
tuick just check    # Auto-detect just as build system
tuick --top script  # Explicit top mode for unrecognized commands
```
To support build systems that orchestrate multiple tools, tuick has an optional
layered mode of operation.

In top mode, the command output is expected to contain mixed data: raw output
from the build system, and structured blocks from `tuick --format`.

Build systems (make, just, cmake, ninja) are auto-detected and use top mode
automatically.

Explicit top mode (with `--top`) is required for unrecognized build systems.

The `TUICK_PORT` environment variable is set by tuick in top mode or list mode.

### Format Mode

Intended for use in build systems:

```makefile
# In Makefile:
check:
    tuick --format -- mypy .
    tuick --format -- ruff check
```

```shell
make check        # Non interactive, pass-through mode
tuick make check  # Interactive
```

If the `TUICK_PORT` environment variable is not set, stream command output
unchanged (passthrough mode). So `make check` will work normally.

If the `TUICK_PORT` environment variable is set, parse the command output, and
output null-terminated blocks, and markers. This is for the top tuick to detect
output that has not been parsed.

## Command-Line Options

### Top-Level Options

- `-f`, `--format-name NAME` — Override autodetected errorformat name.
- `-p`, `--pattern PATTERN` — Custom errorformat pattern(s), can be specified
  multiple times
- `--top` — Force top mode (override build system detection)
- `-v`, `--verbose` — Show verbose output on exit.
- `--theme THEME` — Color theme: `dark`, `light`, `bw`, `auto` (default:
  `auto`)

**Note**: `-f/--format-name` and `-p/--pattern` are mutually exclusive.

### Internal Options

These options are for internal use by tuick when communicating between
processes:

- `--reload` — Run command and output blocks (called by fzf binding)
- `--select` — Open editor at error location (called by fzf binding)
- `--message TEXT` — Log a message (used for event logging)
- `--start` — Notify fzf port to parent process

## Auto-Reload on File Changes

Tuick automatically monitors the filesystem and reloads on changes using
[`watchexec`]:

- Monitors current directory recursively
- Honors `.gitignore` (properly, with subdirs ignores, user ignores, etc.) and
  other VCS ignore files by default
- Debounces rapid changes
- No configuration needed

## Theme Detection and Configuration

Tuick supports automatic dark/light theme detection for `fzf` and `bat`
preview, and obeys the `NO_COLOR` environment variable.

In order of precedence, highest priority first:

1. `--theme` option: `dark`/`light`/`bw`/`auto`, default `auto`.
2. `CLI_THEME` environment variable: `dark`/`light`.
3. `NO_COLOR` environment variable: if set and non-empty, selects `bw` theme.
4. Terminal probing: OSC11 query to detect terminal background color.
5. `COLORFGBG` environment variable.
6. Default to `dark`.

If the `BAT_THEME` environment variable is set, no theme selection option is
passed to `bat`, so the theme specified by `BAT_THEME` will be used.

The `bw` theme is a special theme that disables colors, but tries to preserve
text styling.

### CLI_THEME and shell integration

Theme detection is a common issue. To avoid repeated terminal probing with
OSC11 queries, I recommend that you set a pre-exec hook in your shell that
updates `CLI_THEME` and other environment variables based on terminal probing.

This should probably be a project of its own.

## User Configuration Environment Variables

### Initial preview visibility

`export TUICK_PREVIEW=0` to start with preview window hidden.

Press `/` or `Ctrl-/` to toggle preview visibility.

### Verbose output

`export TUICK_VERBOSE=1` to enable verbose output showing commands run by tuick.

This is equivalent to using the `--verbose` flag. When set, verbose mode is
inherited by nested tuick processes in build systems.

## Editor Integration

Tuick opens files at error locations in your editor. Editor is selected in this
order:

1. `TUICK_EDITOR` — Tuick-specific editor
2. `EDITOR` — Standard editor variable
3. `VISUAL` — Alternative editor variable

The environment variable can contain a command with additional options. If the
editor command name is recognized, tuick will use the most appropriate method
for opening the file.

In particular, IDEA, PyCharm, VS Code and variants, will open files through the
URL handler registered by the editor. This is often much faster than using the
command-line interface.

### Custom Editor Templates

You can use the following environment variables with unsupported editors:

- `TUICK_EDITOR_LINE` — Template command to open a file on a line.
- `TUICK_EDITOR_LINE_COLUMN` — Template to open a file on a line and column.

Examples:

```bash
export TUICK_EDITOR="myeditor"
export TUICK_EDITOR_LINE="myeditor {file} -g {line}"
export TUICK_EDITOR_LINE_COLUMN="myeditor {file} -g {line}:{col}"
```

## Internal Use Environment Variables

These variables are set by tuick for communication with commands:

- `TUICK_PORT` — Port number for tuick coordination server
- `TUICK_API_KEY` — Authentication key for tuick server
- `TUICK_LOG_FILE` — Path to shared log file for all tuick processes
- `FORCE_COLOR` — Set to `1` for build commands when theme is not
  black-and-white

## Dependencies

**Required**:

- [`uv`] — Python package manager, for installation.
- [`fzf`] — Interactive fuzzy finder
- [`errorformat`] — Error output parser (from reviewdog project)
- [`watchexec`] — Filesystem watcher for auto-reload

**Optional**:

- [`bat`] — Syntax-highlighted preview in fzf (highly recommended)

**Install:**

```bash
# macOS (via Homebrew)
brew install uv go fzf watchexec bat

# errorformat (requires Go)
go install github.com/reviewdog/errorformat/cmd/errorformat@latest

# In the tuick repository
just install
```

## Supported Tools

Tuick supports all tools with [errorformat built-in patterns]. Run `errorformat
-list` to see available formats:

ansible-lint, bandit, black, brakeman, buf, cargo-check, clippy, dotenv-linter,
dotnet, erb-lint, eslint, eslint-compact, fasterer, flake8, go-consistent,
golangci-lint, golint, gosec, govet, haml-lint, hlint, isort, luacheck,
misspell, msbuild, mypy, pep8, phpstan, protolint, psalm, puppet-lint,
pydocstyle, reek, remark-lint, rubocop, sbt, sbt-scalastyle, scalac,
scalastyle, slim-lint, sorbet, standardjs, standardrb, staticcheck, stylelint,
tsc, tslint, typos, yamllint.

Additionally, tuick provides enhanced support for:

- **mypy** — Enhanced multi-line patterns with column support.
- **ruff** — Enhanced patterns for both concise and full formats.
- **pytest** — Custom multi-line patterns for test failures.

Build systems (stub support — groups output into info blocks):
- **make**, **just**, **cmake**, **ninja**

Additional tools can be supported by:

- Using `-f/--format-name` to reference any errorformat built-in format
- Providing custom patterns via `-p/--pattern` option
- Extending `tool_registry.py` for custom patterns

Check the [vim errorformat documentation] for the pattern syntax.

## License

Tuick is released under the MIT License. See [LICENSE](LICENSE) for details.

[`fzf`]: https://junegunn.github.io/fzf/
[`errorformat`]: https://github.com/reviewdog/errorformat
[errorformat built-in patterns]: https://github.com/reviewdog/errorformat
[`watchexec`]: https://github.com/watchexec/watchexec
[`dmypy`]: https://mypy.readthedocs.io/en/stable/mypy_daemon.html
[`bat`]: https://github.com/sharkdp/bat
