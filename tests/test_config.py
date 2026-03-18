"""Tests for BacklogConfig: title_truncate_length."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import BacklogConfig


class TestTitleTruncateLength(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")

    def test_missing_config_returns_default(self):
        bc = BacklogConfig(config_path=self.config_file)
        self.assertEqual(bc.get_title_truncate_length(), 35)

    def test_empty_config_returns_default(self):
        with open(self.config_file, "w") as f:
            json.dump({}, f)
        bc = BacklogConfig(config_path=self.config_file)
        self.assertEqual(bc.get_title_truncate_length(), 35)

    def test_valid_positive_integer(self):
        with open(self.config_file, "w") as f:
            json.dump({"title_truncate_length": 50}, f)
        bc = BacklogConfig(config_path=self.config_file)
        self.assertEqual(bc.get_title_truncate_length(), 50)

    def test_zero_falls_back_to_default(self):
        with open(self.config_file, "w") as f:
            json.dump({"title_truncate_length": 0}, f)
        bc = BacklogConfig(config_path=self.config_file)
        self.assertEqual(bc.get_title_truncate_length(), 35)

    def test_negative_falls_back_to_default(self):
        with open(self.config_file, "w") as f:
            json.dump({"title_truncate_length": -1}, f)
        bc = BacklogConfig(config_path=self.config_file)
        self.assertEqual(bc.get_title_truncate_length(), 35)

    def test_non_integer_falls_back_to_default(self):
        with open(self.config_file, "w") as f:
            json.dump({"title_truncate_length": "40"}, f)
        bc = BacklogConfig(config_path=self.config_file)
        self.assertEqual(bc.get_title_truncate_length(), 35)

    def test_float_falls_back_to_default(self):
        with open(self.config_file, "w") as f:
            json.dump({"title_truncate_length": 40.5}, f)
        bc = BacklogConfig(config_path=self.config_file)
        self.assertEqual(bc.get_title_truncate_length(), 35)


class TestPageSize(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")

    def test_missing_returns_default(self):
        bc = BacklogConfig(config_path=self.config_file)
        self.assertEqual(bc.get_page_size(), 20)

    def test_empty_returns_default(self):
        with open(self.config_file, "w") as f:
            json.dump({}, f)
        bc = BacklogConfig(config_path=self.config_file)
        self.assertEqual(bc.get_page_size(), 20)

    def test_valid_positive(self):
        with open(self.config_file, "w") as f:
            json.dump({"page_size": 50}, f)
        bc = BacklogConfig(config_path=self.config_file)
        self.assertEqual(bc.get_page_size(), 50)

    def test_zero_falls_back(self):
        with open(self.config_file, "w") as f:
            json.dump({"page_size": 0}, f)
        bc = BacklogConfig(config_path=self.config_file)
        self.assertEqual(bc.get_page_size(), 20)

    def test_negative_falls_back(self):
        with open(self.config_file, "w") as f:
            json.dump({"page_size": -1}, f)
        bc = BacklogConfig(config_path=self.config_file)
        self.assertEqual(bc.get_page_size(), 20)

    def test_non_integer_falls_back(self):
        with open(self.config_file, "w") as f:
            json.dump({"page_size": "30"}, f)
        bc = BacklogConfig(config_path=self.config_file)
        self.assertEqual(bc.get_page_size(), 20)

    def test_float_falls_back(self):
        with open(self.config_file, "w") as f:
            json.dump({"page_size": 40.5}, f)
        bc = BacklogConfig(config_path=self.config_file)
        self.assertEqual(bc.get_page_size(), 20)
