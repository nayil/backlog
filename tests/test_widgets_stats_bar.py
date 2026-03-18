"""Tests for widgets.stats_bar module."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestStatsBar(unittest.TestCase):
    """StatsBar displays total count, by_status, and page info."""

    def test_stats_bar_update_displays_content(self):
        """After update_stats, renderable contains Total, Page, Todo, In Progress, Done."""
        from widgets.stats_bar import StatsBar

        bar = StatsBar(id="stats-bar")
        bar.update_stats(
            total_count=10,
            by_status={"todo": 3, "in_progress": 2, "done": 5},
            current_page=1,
            total_pages=2,
        )
        text = getattr(bar, "renderable", None) or getattr(bar, "content", None)
        self.assertIsNotNone(text, "StatsBar should have renderable/content after update_stats")
        text = str(text)
        self.assertIn("Total: 10", text)
        self.assertIn("Page 1/2", text)
        self.assertIn("Todo:", text)
        self.assertIn("In Progress:", text)
        self.assertIn("Done:", text)


if __name__ == "__main__":
    unittest.main()
