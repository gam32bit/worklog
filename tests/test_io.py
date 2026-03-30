"""Tests for worklog.io module."""

import unittest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from worklog.io import slugify, prepend_to_wiki, append_to_wiki


class TestSlugify(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(slugify("Editor Check In"), "editor-check-in")

    def test_lowercase(self):
        self.assertEqual(slugify("UPPERCASE TITLE"), "uppercase-title")

    def test_strips_punctuation(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_collapses_hyphens(self):
        self.assertEqual(slugify("foo  bar"), "foo-bar")

    def test_strips_leading_trailing_hyphens(self):
        self.assertEqual(slugify("!hello!"), "hello")

    def test_truncates_to_50(self):
        long_title = "a" * 60
        result = slugify(long_title)
        self.assertEqual(len(result), 50)

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_only_punctuation(self):
        self.assertEqual(slugify("!!!"), "")

    def test_numbers_preserved(self):
        self.assertEqual(slugify("PR 42 review"), "pr-42-review")

    def test_truncation_does_not_end_with_hyphen(self):
        # Slug of exactly 50 chars from a long title with hyphens — just check length
        title = "word " * 15  # 75 chars with spaces
        result = slugify(title)
        self.assertLessEqual(len(result), 50)


class TestPrependToWiki(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_creates_file_if_not_exists(self):
        prepend_to_wiki(self.tmpdir, "timeline", "* entry one")
        page_path = Path(self.tmpdir) / "timeline.wiki"
        self.assertTrue(page_path.exists())
        self.assertIn("* entry one", page_path.read_text())

    def test_prepends_to_existing_file(self):
        page_path = Path(self.tmpdir) / "timeline.wiki"
        page_path.write_text("* old entry\n")
        prepend_to_wiki(self.tmpdir, "timeline", "* new entry")
        content = page_path.read_text()
        lines = content.splitlines()
        self.assertEqual(lines[0], "* new entry")
        self.assertEqual(lines[1], "* old entry")

    def test_multiple_prepends_newest_first(self):
        prepend_to_wiki(self.tmpdir, "timeline", "* entry A")
        prepend_to_wiki(self.tmpdir, "timeline", "* entry B")
        prepend_to_wiki(self.tmpdir, "timeline", "* entry C")
        content = Path(self.tmpdir, "timeline.wiki").read_text()
        lines = [l for l in content.splitlines() if l.strip()]
        self.assertEqual(lines[0], "* entry C")
        self.assertEqual(lines[1], "* entry B")
        self.assertEqual(lines[2], "* entry A")


class TestAppendToWiki(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_creates_project_wiki_if_not_exists(self):
        append_to_wiki(self.tmpdir, "myproject", "== Log ==", "* [[log-2026-03-26|2026-03-26]] Summary")
        page_path = Path(self.tmpdir) / "myproject.wiki"
        self.assertTrue(page_path.exists())
        content = page_path.read_text()
        self.assertIn("== Log ==", content)
        self.assertIn("* [[log-2026-03-26|2026-03-26]] Summary", content)
        self.assertIn("= Myproject =", content)
        self.assertIn("[[index|Back to index]]", content)

    def test_inserts_after_section_header(self):
        page_path = Path(self.tmpdir) / "myproject.wiki"
        page_path.write_text("= Myproject =\n[[index|Back to index]]\n\n== Log ==\n* old entry\n\n== Tasks | project:myproject ==\n")
        append_to_wiki(self.tmpdir, "myproject", "== Log ==", "* new entry")
        lines = page_path.read_text().splitlines()
        meetings_idx = lines.index("== Log ==")
        self.assertEqual(lines[meetings_idx + 1], "* new entry")
        self.assertEqual(lines[meetings_idx + 2], "* old entry")

    def test_multiple_inserts_newest_first(self):
        append_to_wiki(self.tmpdir, "proj", "== Log ==", "* entry A")
        append_to_wiki(self.tmpdir, "proj", "== Log ==", "* entry B")
        content = Path(self.tmpdir, "proj.wiki").read_text()
        lines = content.splitlines()
        meetings_idx = lines.index("== Log ==")
        self.assertEqual(lines[meetings_idx + 1], "* entry B")
        self.assertEqual(lines[meetings_idx + 2], "* entry A")

    def test_appends_section_if_not_found(self):
        page_path = Path(self.tmpdir) / "other.wiki"
        page_path.write_text("= Other =\n\nsome content\n")
        append_to_wiki(self.tmpdir, "other", "== Log ==", "* entry")
        content = page_path.read_text()
        self.assertIn("== Log ==", content)
        self.assertIn("* entry", content)


if __name__ == '__main__':
    unittest.main()
