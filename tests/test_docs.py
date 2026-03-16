"""Tests for documentation: README and user manual updates for v1.1.0."""

import os
import unittest

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


class TestReadmeConfigSection(unittest.TestCase):
    """README must have Configuration section."""

    def setUp(self):
        with open(os.path.join(PROJECT_ROOT, "README.md"), encoding="utf-8") as f:
            self.content = f.read()

    def test_has_configuration_heading(self):
        self.assertIn("## Configuration", self.content)

    def test_has_config_json_example(self):
        self.assertIn("config.json", self.content)
        self.assertIn("status_colors", self.content)
        self.assertIn("priority_colors", self.content)

    def test_has_default_hex_values(self):
        self.assertIn("#61AFEF", self.content)
        self.assertIn("#E06C75", self.content)


class TestReadmePipInstall(unittest.TestCase):
    """README must document pip install method."""

    def setUp(self):
        with open(os.path.join(PROJECT_ROOT, "README.md"), encoding="utf-8") as f:
            self.content = f.read()

    def test_has_pip_install(self):
        self.assertIn("pip install", self.content)

    def test_has_pip_install_editable(self):
        self.assertIn("pip install -e", self.content)


class TestReadmeVersionBump(unittest.TestCase):
    """README should reference v1.1.0."""

    def setUp(self):
        with open(os.path.join(PROJECT_ROOT, "README.md"), encoding="utf-8") as f:
            self.content = f.read()

    def test_version_badge(self):
        self.assertIn("1.1.0", self.content)


class TestUserManualExists(unittest.TestCase):
    """v1.1.0 user manual must exist."""

    def test_manual_exists(self):
        path = os.path.join(PROJECT_ROOT, ".release", "backlog-v1.1.0-用户手册.md")
        self.assertTrue(os.path.isfile(path), "v1.1.0 用户手册 not found")

    def test_manual_has_v110_content(self):
        path = os.path.join(PROJECT_ROOT, ".release", "backlog-v1.1.0-用户手册.md")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("v1.1.0", content)
        self.assertIn("Configuration", content)
        self.assertIn("pip install", content)
        self.assertIn("退出", content)


if __name__ == "__main__":
    unittest.main()
