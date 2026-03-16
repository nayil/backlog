"""Integration tests for Title truncation (display + config)."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from display import truncate_title
from config import BacklogConfig


class TestTitleTruncationIntegration(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.tmpdir, "config.json")

    def test_config_and_truncate_combined(self):
        with open(self.config_path, "w") as f:
            json.dump({"title_truncate_length": 10}, f)
        bc = BacklogConfig(config_path=self.config_path)
        self.assertEqual(
            truncate_title("x" * 80, bc.get_title_truncate_length()),
            "x" * 10 + "…",
        )
