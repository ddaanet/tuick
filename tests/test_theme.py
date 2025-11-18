"""Tests for theme detection and configuration."""

import os
import unittest
from contextlib import contextmanager
from typing import TYPE_CHECKING
from unittest.mock import patch

from tuick.theme import ColorTheme, ColorThemeAuto, DetectedTheme, detect_theme

if TYPE_CHECKING:
    from collections.abc import Iterator

# Known COLORFGBG values from https://github.com/rocky/shell-term-background/
LIGHT_COLORFGBG_VALUES = ("0;15", "0;default;15")
DARK_COLORFGBG_VALUES = ("15;0", "15;default;0")

# Env variables that affect theme detection
THEME_ENV_VARS = ("NO_COLOR", "CLI_THEME", "COLORFGBG")


@contextmanager
def patch_theme_detection(
    env: dict[str, str], osc11_result: DetectedTheme = None
) -> Iterator[None]:
    """Patch environment and OSC11 detection for theme tests."""
    # Clear all theme env vars, then apply provided env
    clean_env = dict.fromkeys(THEME_ENV_VARS, "") | env
    with (
        patch.dict(os.environ, clean_env, clear=True),
        patch("tuick.theme._detect_via_osc11", return_value=osc11_result),
    ):
        yield


class TestDetectTheme(unittest.TestCase):
    """Test theme detection priority order."""

    def test_cli_option_dark(self):
        """CLI option overrides all other sources."""
        env = {"CLI_THEME": "light", "NO_COLOR": "1"}
        with patch_theme_detection(env):
            assert detect_theme(ColorTheme.DARK) == ColorTheme.DARK

    def test_cli_option_light(self):
        """CLI option light."""
        with patch_theme_detection({}):
            assert detect_theme(ColorTheme.LIGHT) == ColorTheme.LIGHT

    def test_cli_option_bw(self):
        """CLI option bw."""
        with patch_theme_detection({}):
            assert detect_theme(ColorTheme.BW) == ColorTheme.BW

    def test_cli_theme_env_dark(self):
        """CLI_THEME env var used when CLI option is auto."""
        with patch_theme_detection({"CLI_THEME": "dark"}):
            assert detect_theme(ColorThemeAuto.AUTO) == ColorTheme.DARK

    def test_cli_theme_env_light(self):
        """CLI_THEME env var light."""
        with patch_theme_detection({"CLI_THEME": "light"}):
            assert detect_theme(ColorThemeAuto.AUTO) == ColorTheme.LIGHT

    def test_cli_theme_env_bw(self):
        """CLI_THEME env var bw."""
        with patch_theme_detection({"CLI_THEME": "bw"}):
            assert detect_theme(ColorThemeAuto.AUTO) == ColorTheme.BW

    def test_cli_theme_env_case_insensitive(self):
        """CLI_THEME env var is case insensitive."""
        with patch_theme_detection({"CLI_THEME": "DARK"}):
            assert detect_theme(ColorThemeAuto.AUTO) == ColorTheme.DARK

    def test_cli_theme_env_invalid_fallthrough(self):
        """Invalid CLI_THEME value falls through to NO_COLOR."""
        with patch_theme_detection({"CLI_THEME": "invalid", "NO_COLOR": "1"}):
            assert detect_theme(ColorThemeAuto.AUTO) == ColorTheme.BW

    def test_no_color_defined_and_nonempty(self):
        """NO_COLOR defined and not empty returns BW."""
        with patch_theme_detection({"NO_COLOR": "1"}):
            assert detect_theme(ColorThemeAuto.AUTO) == ColorTheme.BW

    def test_no_color_empty_ignored(self):
        """NO_COLOR defined but empty is ignored."""
        with patch_theme_detection({"COLORFGBG": LIGHT_COLORFGBG_VALUES[0]}):
            assert detect_theme(ColorThemeAuto.AUTO) == ColorTheme.LIGHT

    def test_autodetect_colorfgbg_light(self):
        """COLORFGBG light values detected."""
        for colorfgbg in LIGHT_COLORFGBG_VALUES:
            with (
                self.subTest(colorfgbg=colorfgbg),
                patch_theme_detection({"COLORFGBG": colorfgbg}),
            ):
                assert detect_theme(ColorThemeAuto.AUTO) == ColorTheme.LIGHT

    def test_autodetect_colorfgbg_dark(self):
        """COLORFGBG dark values detected."""
        for colorfgbg in DARK_COLORFGBG_VALUES:
            with (
                self.subTest(colorfgbg=colorfgbg),
                patch_theme_detection({"COLORFGBG": colorfgbg}),
            ):
                assert detect_theme(ColorThemeAuto.AUTO) == ColorTheme.DARK

    def test_autodetect_colorfgbg_unknown_fallthrough(self):
        """Unknown COLORFGBG value falls through to default."""
        with patch_theme_detection({"COLORFGBG": "unknown"}):
            assert detect_theme(ColorThemeAuto.AUTO) == ColorTheme.DARK

    def test_autodetect_default_dark(self):
        """Autodetect defaults to DARK when all methods fail."""
        with patch_theme_detection({}):
            assert detect_theme(ColorThemeAuto.AUTO) == ColorTheme.DARK

    def test_osc11_overrides_colorfgbg(self):
        """OSC 11 detection has priority over COLORFGBG."""
        env = {"COLORFGBG": DARK_COLORFGBG_VALUES[0]}
        with patch_theme_detection(env, osc11_result=ColorTheme.LIGHT):
            assert detect_theme(ColorThemeAuto.AUTO) == ColorTheme.LIGHT
