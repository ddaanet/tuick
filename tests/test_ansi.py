"""Tests for ANSI escape code utilities."""

from tuick.ansi import strip_ansi


def test_strip_ansi_csi_sequences() -> None:
    """strip_ansi removes CSI color and formatting codes."""
    text = "\x1b[1m\x1b[31merror:\x1b[0m message"
    assert strip_ansi(text) == "error: message"


def test_strip_ansi_scs_g0_sequences() -> None:
    """strip_ansi removes SCS G0 character set selection codes."""
    # Example from commit 74788e6 - ruff output with \x1b(B codes
    text = (
        "src/tuick/console.py:77: \x1b[1m\x1b[31merror:\x1b(B\x1b[m Name "
        '\x1b(B\x1b[m\x1b[1m"undefined_variable_here"\x1b(B\x1b[m is not '
        "defined  \x1b(B\x1b[m\x1b[33m[name-defined]\x1b(B\x1b[m\n"
    )
    expected = (
        'src/tuick/console.py:77: error: Name "undefined_variable_here" '
        "is not defined  [name-defined]\n"
    )
    assert strip_ansi(text) == expected


def test_strip_ansi_fe_sequences() -> None:
    """strip_ansi removes Fe two-byte escape sequences."""
    # ESC M (reverse index) and ESC D (index)
    text = "\x1bMsave\x1bDrestore"
    assert strip_ansi(text) == "saverestore"


def test_strip_ansi_empty_string() -> None:
    """strip_ansi handles empty string."""
    assert strip_ansi("") == ""


def test_strip_ansi_no_ansi() -> None:
    """strip_ansi returns unchanged text with no ANSI codes."""
    text = "plain text with no formatting"
    assert strip_ansi(text) == text


def test_strip_ansi_complex_csi() -> None:
    """strip_ansi handles complex CSI sequences with parameters."""
    text = "\x1b[1;32mbold green\x1b[0m"
    assert strip_ansi(text) == "bold green"
