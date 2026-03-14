"""Tests for v0.8.0 changes in src/app.py.

Covers:
  - _category_color() pure-function behaviour
  - CSS numeric values for #form-container width and #inp-desc height
"""

import hashlib
import re
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Import only the pure symbols; avoids loading Textual widgets at import time.
from app import CATEGORY_COLORS, _category_color


# ── _category_color() ────────────────────────────────────────────────────────

class TestCategoryColorEmpty(unittest.TestCase):
    def test_empty_string_returns_empty(self):
        self.assertEqual(_category_color(""), "")

    def test_dash_returns_empty(self):
        self.assertEqual(_category_color("-"), "")

    def test_none_like_falsy_empty(self):
        # Passing empty string (None would be a type error, but "" is the
        # documented sentinel for "no category").
        self.assertEqual(_category_color(""), "")


class TestCategoryColorValid(unittest.TestCase):
    def test_returns_value_from_palette(self):
        color = _category_color("backend")
        self.assertIn(color, CATEGORY_COLORS)

    def test_returns_value_from_palette_another_category(self):
        color = _category_color("frontend")
        self.assertIn(color, CATEGORY_COLORS)

    def test_returns_hex_color_format(self):
        color = _category_color("infra")
        self.assertRegex(color, r"^#[0-9A-Fa-f]{6}$")

    def test_all_palette_colors_are_valid_hex(self):
        for c in CATEGORY_COLORS:
            self.assertRegex(c, r"^#[0-9A-Fa-f]{6}$", msg=f"{c!r} is not valid hex color")


class TestCategoryColorStability(unittest.TestCase):
    """Same input must always produce the same output (deterministic hash)."""

    def test_same_category_same_color(self):
        cat = "data-science"
        self.assertEqual(_category_color(cat), _category_color(cat))

    def test_repeated_calls_consistent(self):
        cat = "ops"
        first = _category_color(cat)
        for _ in range(10):
            self.assertEqual(_category_color(cat), first)

    def test_different_categories_produce_multiple_colors(self):
        """Different category names should map to at least 2 distinct colors,
        confirming the hash distributes across the palette."""
        seen_colors = set()
        sample_categories = [
            "alpha", "beta", "gamma", "delta", "epsilon",
            "zeta", "eta", "theta", "iota", "kappa",
            "lambda", "mu", "nu", "xi", "omicron",
            "pi", "rho", "sigma", "tau", "upsilon",
        ]
        for cat in sample_categories:
            seen_colors.add(_category_color(cat))
        # With 20 diverse inputs we must hit more than 1 distinct color.
        self.assertGreater(len(seen_colors), 1)
        # All returned values must still be valid palette entries.
        for color in seen_colors:
            self.assertIn(color, CATEGORY_COLORS)

    def test_determinism_matches_manual_md5(self):
        """Cross-check against a manually computed expected index."""
        cat = "backend"
        digest = hashlib.md5(cat.encode()).hexdigest()
        expected = CATEGORY_COLORS[int(digest, 16) % len(CATEGORY_COLORS)]
        self.assertEqual(_category_color(cat), expected)


# ── CSS numeric values ────────────────────────────────────────────────────────

def _read_css_block(app_py_path: str) -> str:
    with open(app_py_path, encoding="utf-8") as fh:
        return fh.read()


APP_PY = os.path.join(os.path.dirname(__file__), "..", "src", "app.py")
_SOURCE = _read_css_block(APP_PY)


class TestCssFormContainerWidth(unittest.TestCase):
    """#form-container width must be 84 (v0.8.0 changed from 70)."""

    def test_form_container_width_is_84(self):
        # Match the CSS block: `#form-container { ... width: 84; ... }`
        m = re.search(
            r"#form-container\s*\{[^}]*width\s*:\s*(\d+)\s*;",
            _SOURCE,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "#form-container CSS block not found in app.py")
        self.assertEqual(int(m.group(1)), 84)


class TestCssInpDescHeight(unittest.TestCase):
    """#inp-desc height must be 9 (v0.8.0 changed from 7)."""

    def test_inp_desc_height_is_9(self):
        m = re.search(
            r"#inp-desc\s*\{[^}]*height\s*:\s*(\d+)\s*;",
            _SOURCE,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "#inp-desc CSS block not found in app.py")
        self.assertEqual(int(m.group(1)), 9)


# ── CATEGORY_COLORS palette ───────────────────────────────────────────────────

class TestCategoryColorsPalette(unittest.TestCase):
    def test_palette_has_eight_colors(self):
        self.assertEqual(len(CATEGORY_COLORS), 8)

    def test_palette_has_no_duplicates(self):
        self.assertEqual(len(set(CATEGORY_COLORS)), len(CATEGORY_COLORS))


if __name__ == "__main__":
    unittest.main()
