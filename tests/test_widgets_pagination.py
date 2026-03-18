"""Tests for widgets.pagination module."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestPagination(unittest.TestCase):
    def test_total_pages_zero_count(self):
        from widgets.pagination import calc_total_pages
        self.assertEqual(calc_total_pages(0, 20), 1)

    def test_total_pages_one_page(self):
        from widgets.pagination import calc_total_pages
        self.assertEqual(calc_total_pages(10, 20), 1)

    def test_total_pages_multi_page(self):
        from widgets.pagination import calc_total_pages
        self.assertEqual(calc_total_pages(50, 20), 3)

    def test_clamp_page_in_range(self):
        from widgets.pagination import clamp_page
        self.assertEqual(clamp_page(1, 3), 1)

    def test_clamp_page_exceeds(self):
        from widgets.pagination import clamp_page
        self.assertEqual(clamp_page(5, 3), 2)


if __name__ == "__main__":
    unittest.main()
