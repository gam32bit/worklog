"""Tests for worklog.parser module."""

import unittest
import tempfile
import os
from pathlib import Path
from datetime import date

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from worklog.parser import ParsedLog, parse_file, find_next_steps, mark_item


class TestParsedLogProperties(unittest.TestCase):
    def _make_log(self, frontmatter, content):
        import yaml
        fm = yaml.safe_load(frontmatter) if frontmatter else {}
        return ParsedLog(filepath=Path("/fake/path.md"), frontmatter=fm, content=content)

    def test_date_from_frontmatter_date_object(self):
        log = self._make_log("date: 2026-03-10\nproject: X", "")
        self.assertEqual(log.date, "2026-03-10")

    def test_date_missing(self):
        log = ParsedLog(filepath=Path("/fake/path.md"), frontmatter={}, content="")
        self.assertEqual(log.date, "")

    def test_date_obj_valid(self):
        log = self._make_log("date: 2026-03-10", "")
        self.assertEqual(log.date_obj, date(2026, 3, 10))

    def test_date_obj_invalid(self):
        log = ParsedLog(filepath=Path("/fake/path.md"), frontmatter={"date": "not-a-date"}, content="")
        self.assertIsNone(log.date_obj)

    def test_project(self):
        log = self._make_log("project: MyProject", "")
        self.assertEqual(log.project, "MyProject")

    def test_project_missing(self):
        log = ParsedLog(filepath=Path("/fake/path.md"), frontmatter={}, content="")
        self.assertEqual(log.project, "")

    def test_title_from_frontmatter(self):
        log = self._make_log("title: Sprint planning", "")
        self.assertEqual(log.title, "Sprint planning")

    def test_title_missing(self):
        log = ParsedLog(filepath=Path("/fake/path.md"), frontmatter={}, content="")
        self.assertEqual(log.title, "")

    def test_summary_from_frontmatter(self):
        log = self._make_log("summary: Covered Q2 roadmap", "")
        self.assertEqual(log.summary, "Covered Q2 roadmap")

    def test_summary_missing(self):
        log = ParsedLog(filepath=Path("/fake/path.md"), frontmatter={}, content="")
        self.assertEqual(log.summary, "")


class TestFindNextSteps(unittest.TestCase):
    def _write_temp(self, content):
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
        f.write(content)
        f.close()
        return Path(f.name)

    def _make_log(self, filepath):
        return ParsedLog(filepath=filepath, frontmatter={}, content="")

    def tearDown(self):
        pass

    def test_finds_unprocessed_lines(self):
        path = self._write_temp("---\ndate: 2026-03-10\n---\n\n>> Follow up with Alice\n>> Review PR\n")
        try:
            log = self._make_log(path)
            items = find_next_steps([log])
            texts = [t for _, _, t in items]
            self.assertIn("Follow up with Alice", texts)
            self.assertIn("Review PR", texts)
        finally:
            os.unlink(path)

    def test_ignores_taskwarrior_marked(self):
        path = self._write_temp(">> Pending task\n>>t Added to taskwarrior\n>>r Reviewed item\n")
        try:
            log = self._make_log(path)
            items = find_next_steps([log])
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0][2], "Pending task")
        finally:
            os.unlink(path)

    def test_returns_correct_line_number(self):
        path = self._write_temp("line zero\nline one\n>> Next step here\nline three\n")
        try:
            log = self._make_log(path)
            items = find_next_steps([log])
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0][1], 2)  # 0-based line index
            self.assertEqual(items[0][2], "Next step here")
        finally:
            os.unlink(path)

    def test_empty_logs_returns_empty(self):
        items = find_next_steps([])
        self.assertEqual(items, [])

    def test_no_next_steps_returns_empty(self):
        path = self._write_temp("Just some notes.\n>>t Already done.\n>>r Already reviewed.\n")
        try:
            log = self._make_log(path)
            items = find_next_steps([log])
            self.assertEqual(items, [])
        finally:
            os.unlink(path)


class TestMarkItem(unittest.TestCase):
    def _write_temp(self, content):
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
        f.write(content)
        f.close()
        return Path(f.name)

    def test_mark_taskwarrior(self):
        path = self._write_temp("Some notes\n>> Do this thing\nMore notes\n")
        try:
            mark_item(path, 1, "t")
            lines = path.read_text().splitlines()
            self.assertEqual(lines[1], ">>t Do this thing")
        finally:
            os.unlink(path)

    def test_mark_reviewed(self):
        path = self._write_temp(">> Item one\n>> Item two\n")
        try:
            mark_item(path, 0, "r")
            lines = path.read_text().splitlines()
            self.assertEqual(lines[0], ">>r Item one")
            self.assertEqual(lines[1], ">> Item two")
        finally:
            os.unlink(path)

    def test_only_modifies_target_line(self):
        path = self._write_temp(">> First\n>> Second\n>> Third\n")
        try:
            mark_item(path, 1, "r")
            lines = path.read_text().splitlines()
            self.assertEqual(lines[0], ">> First")
            self.assertEqual(lines[1], ">>r Second")
            self.assertEqual(lines[2], ">> Third")
        finally:
            os.unlink(path)

    def test_noop_if_line_not_next_step(self):
        original = "plain line\nanother line\n"
        path = self._write_temp(original)
        try:
            mark_item(path, 0, "r")
            self.assertEqual(path.read_text(), original)
        finally:
            os.unlink(path)


class TestParseFile(unittest.TestCase):
    def test_parse_file_with_frontmatter(self):
        content = "---\ndate: 2026-03-10\nproject: Test\ntitle: My Log\nsummary: A summary\n---\n\nSome content here.\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            path = Path(f.name)
        try:
            log = parse_file(path)
            self.assertIsNotNone(log)
            self.assertEqual(log.project, "Test")
            self.assertEqual(log.title, "My Log")
            self.assertEqual(log.summary, "A summary")
            self.assertIn("Some content here.", log.content)
        finally:
            os.unlink(path)

    def test_parse_file_no_frontmatter(self):
        content = "Just plain content.\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            path = Path(f.name)
        try:
            log = parse_file(path)
            self.assertIsNotNone(log)
            self.assertEqual(log.frontmatter, {})
            self.assertIn("Just plain content.", log.content)
        finally:
            os.unlink(path)

    def test_parse_file_nonexistent(self):
        log = parse_file(Path("/nonexistent/path/file.md"))
        self.assertIsNone(log)


if __name__ == '__main__':
    unittest.main()
