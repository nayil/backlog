"""Tests for pyproject.toml: pip-installable package configuration."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


class TestPyprojectExists(unittest.TestCase):
    """pyproject.toml must exist at project root."""

    def test_file_exists(self):
        path = os.path.join(PROJECT_ROOT, "pyproject.toml")
        self.assertTrue(os.path.isfile(path), "pyproject.toml not found")


class TestPyprojectContent(unittest.TestCase):
    """pyproject.toml has required fields."""

    def setUp(self):
        path = os.path.join(PROJECT_ROOT, "pyproject.toml")
        with open(path, encoding="utf-8") as f:
            self.content = f.read()

    def test_has_build_system(self):
        self.assertIn("[build-system]", self.content)

    def test_has_setuptools_backend(self):
        self.assertIn("setuptools.build_meta", self.content)

    def test_has_project_name(self):
        self.assertIn('name = "backlog"', self.content)

    def test_has_entry_point(self):
        self.assertIn("[project.scripts]", self.content)
        self.assertIn("backlog.__main__:main", self.content)

    def test_has_src_layout(self):
        self.assertIn("[tool.setuptools.package-dir]", self.content)
        self.assertIn('backlog = "src"', self.content)

    def test_has_textual_dependency(self):
        self.assertIn("textual", self.content)

    def test_has_rich_dependency(self):
        self.assertIn("rich", self.content)

    def test_python_requires(self):
        self.assertIn("requires-python", self.content)
        self.assertIn("3.9", self.content)


class TestVersionUpdated(unittest.TestCase):
    """Version must be 1.1.0 across all entry points."""

    def test_src_init_version(self):
        from __init__ import __version__
        self.assertEqual(__version__, "1.1.0")

    def test_backlog_main_version(self):
        path = os.path.join(PROJECT_ROOT, "backlog", "__main__.py")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn('"1.1.0"', content)

    def test_root_main_version(self):
        path = os.path.join(PROJECT_ROOT, "__main__.py")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn('"1.1.0"', content)


if __name__ == "__main__":
    unittest.main()
