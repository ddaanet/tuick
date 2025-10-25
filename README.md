# Tuick, the Text-based User Interface for Compilers and checKers

Integrates a command with [`fzf`], allowing you to:

- move around the list, grouping multi-line errors
- filter it by fuzzy search
- open your text editor at an error location
- re-run the command to update the list

Usage:

    tuick dmypy run .

    tuick ruff check

Really, use [`dmypy`], it's awesome. It spawns mypy daemon and use it to run
incremental checks. It's fast, in the same ballpark as [`ty`] (the type checker
from those that made [`ruff`]), with more rules and maturity.

Limitations:

- Currently limited to simple line output and default [`ruff`] output
- filtering disabled
- should only display the list if the command had no output to display

[`fzf`]: https://junegunn.github.io/fzf/
[`ruff`]: https://docs.astral.sh/ruff/
[`dmypy`]: https://mypy.readthedocs.io/en/stable/mypy_daemon.html
[`ty`]: https://docs.astral.sh/ty/
