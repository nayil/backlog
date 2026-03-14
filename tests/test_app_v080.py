"""Tests for v0.8.0 changes: CSS numeric values in item_form.py."""

import re
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# ── CSS numeric values ────────────────────────────────────────────────────────

def _read_source(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


ITEM_FORM_PY = os.path.join(os.path.dirname(__file__), "..", "src", "screens", "item_form.py")
_SOURCE = _read_source(ITEM_FORM_PY)


class TestCssFormContainerWidth(unittest.TestCase):
    """#form-container width must be 84 (v0.8.0 changed from 70)."""

    def test_form_container_width_is_84(self):
        m = re.search(
            r"#form-container\s*\{[^}]*width\s*:\s*(\d+)\s*;",
            _SOURCE,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "#form-container CSS block not found")
        self.assertEqual(int(m.group(1)), 84)


class TestCssInpDescHeight(unittest.TestCase):
    """#inp-desc height must be 9 (v0.8.0 changed from 7)."""

    def test_inp_desc_height_is_9(self):
        m = re.search(
            r"#inp-desc\s*\{[^}]*height\s*:\s*(\d+)\s*;",
            _SOURCE,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "#inp-desc CSS block not found")
        self.assertEqual(int(m.group(1)), 9)


if __name__ == "__main__":
    unittest.main()
