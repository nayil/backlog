"""Tests for ColorConfig: user-configurable Status/Priority colors."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from color_config import ColorConfig


class TestColorConfigDefaults(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")

    def test_default_status_colors(self):
        cc = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc.get_status_color("todo"), "#61AFEF")
        self.assertEqual(cc.get_status_color("in_progress"), "#E5C07B")
        self.assertEqual(cc.get_status_color("done"), "#98C379")

    def test_default_priority_colors(self):
        cc = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc.get_priority_color("high"), "#E06C75")
        self.assertEqual(cc.get_priority_color("medium"), "#E5C07B")
        self.assertEqual(cc.get_priority_color("low"), "#98C379")


class TestColorConfigUserOverrides(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")

    def test_partial_status_override(self):
        with open(self.config_file, "w") as f:
            json.dump({"status_colors": {"todo": "#FF0000"}}, f)
        cc = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc.get_status_color("todo"), "#FF0000")
        self.assertEqual(cc.get_status_color("done"), "#98C379")

    def test_partial_priority_override(self):
        with open(self.config_file, "w") as f:
            json.dump({"priority_colors": {"high": "#00FF00"}}, f)
        cc = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc.get_priority_color("high"), "#00FF00")
        self.assertEqual(cc.get_priority_color("low"), "#98C379")


class TestColorConfigUnknownKeys(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")

    def test_unknown_status_key_ignored(self):
        with open(self.config_file, "w") as f:
            json.dump({"status_colors": {"nonexistent": "#FF0000"}}, f)
        cc = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc.get_status_color("nonexistent"), "")
        self.assertEqual(cc.get_status_color("todo"), "#61AFEF")


class TestColorConfigInvalidHex(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")

    def test_invalid_hex_falls_back(self):
        with open(self.config_file, "w") as f:
            json.dump({"status_colors": {"todo": "not-a-color"}}, f)
        cc = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc.get_status_color("todo"), "#61AFEF")

    def test_non_string_value_falls_back(self):
        with open(self.config_file, "w") as f:
            json.dump({"status_colors": {"todo": 12345}}, f)
        cc = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc.get_status_color("todo"), "#61AFEF")


class TestColorConfigMalformedJson(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")

    def test_malformed_json(self):
        with open(self.config_file, "w") as f:
            f.write("{invalid json")
        cc = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc.get_status_color("todo"), "#61AFEF")


class TestColorConfigSetters(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmpdir, "config.json")

    def test_set_status_color_persists(self):
        cc = ColorConfig(config_path=self.config_file)
        cc.set_status_color("todo", "#FF0000")
        cc2 = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc2.get_status_color("todo"), "#FF0000")

    def test_set_priority_color_persists(self):
        cc = ColorConfig(config_path=self.config_file)
        cc.set_priority_color("high", "#00FF00")
        cc2 = ColorConfig(config_path=self.config_file)
        self.assertEqual(cc2.get_priority_color("high"), "#00FF00")

    def test_set_invalid_hex_raises(self):
        cc = ColorConfig(config_path=self.config_file)
        with self.assertRaises(ValueError):
            cc.set_status_color("todo", "not-valid")

    def test_set_preserves_other_config_keys(self):
        with open(self.config_file, "w") as f:
            json.dump({"theme": "old-theme", "other": 42}, f)
        cc = ColorConfig(config_path=self.config_file)
        cc.set_status_color("todo", "#AABBCC")
        with open(self.config_file) as f:
            data = json.load(f)
        self.assertEqual(data["other"], 42)
        self.assertEqual(data["theme"], "old-theme")


if __name__ == "__main__":
    unittest.main()
