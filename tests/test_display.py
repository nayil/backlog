"""Tests for display utilities: truncate_title."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from display import truncate_title


class TestTruncateTitle(unittest.TestCase):
    def test_none_returns_dash(self):
        self.assertEqual(truncate_title(None, 35), "-")

    def test_empty_string_returns_dash(self):
        self.assertEqual(truncate_title("", 35), "-")

    def test_short_title_unchanged(self):
        self.assertEqual(truncate_title("short", 35), "short")

    def test_exact_length_unchanged(self):
        s = "x" * 35
        self.assertEqual(truncate_title(s, 35), s)

    def test_long_title_truncated_with_ellipsis(self):
        s = "a" * 80
        self.assertEqual(truncate_title(s, 35), "a" * 35 + "…")

    def test_truncate_length_respected(self):
        s = "hello world"
        self.assertEqual(truncate_title(s, 5), "hello…")

    # Boundary: max_len <= 0 (CR P2 risk area)
    def test_max_len_zero_none_returns_dash(self):
        self.assertEqual(truncate_title(None, 0), "-")

    def test_max_len_zero_empty_returns_dash(self):
        self.assertEqual(truncate_title("", 0), "-")

    def test_max_len_zero_with_title_returns_ellipsis(self):
        """Current behavior: title[:0] + '…' = '…' when max_len=0."""
        self.assertEqual(truncate_title("abc", 0), "…")

    def test_max_len_negative_with_title_returns_ellipsis(self):
        """Current behavior: title[:-1] + '…' when max_len=-1."""
        self.assertEqual(truncate_title("ab", -1), "a…")

    def test_max_len_negative_none_returns_dash(self):
        self.assertEqual(truncate_title(None, -1), "-")
