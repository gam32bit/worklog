"""Tests for worklog.parser module."""

import unittest
import tempfile
import os
from pathlib import Path
from datetime import date

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from worklog.parser import ParsedLog, parse_file, mark_action_reviewed


SAMPLE_FRONTMATTER = """\
---
date: 2026-03-10
project: MyProject
contacts: [Alice, Bob]
title: Sprint planning
---
"""

SAMPLE_CONTENT = """\
Some notes here.

## Next Steps
- Follow up with Alice
- [ ] Review PR #42
- [x] Send email to Bob
- Write tests
  continuation line here

## Session Actions
- Reviewed PRs
- Had standup
  with the team
"""


class TestParsedLogProperties(unittest.TestCase):
    def _make_log(self, frontmatter, content):
        import yaml
        fm = yaml.safe_load(frontmatter) if frontmatter else {}
        return ParsedLog(filepath=Path("/fake/path.md"), frontmatter=fm, content=content)

    def test_date_from_frontmatter_date_object(self):
        log = self._make_log("date: 2026-03-10\nproject: X\ncontacts: []", "")
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

    def test_contacts_list(self):
        log = self._make_log("contacts: [Alice, Bob]", "")
        self.assertEqual(log.contacts, ["Alice", "Bob"])

    def test_contacts_string(self):
        log = ParsedLog(filepath=Path("/fake/path.md"), frontmatter={"contacts": "Alice, Bob"}, content="")
        self.assertEqual(log.contacts, ["Alice", "Bob"])

    def test_contacts_empty(self):
        log = ParsedLog(filepath=Path("/fake/path.md"), frontmatter={}, content="")
        self.assertEqual(log.contacts, [])

    def test_title_from_frontmatter(self):
        log = self._make_log("title: Sprint planning", "")
        self.assertEqual(log.title, "Sprint planning")

    def test_title_from_heading(self):
        log = ParsedLog(filepath=Path("/fake/path.md"), frontmatter={}, content="# My Heading\nsome content")
        self.assertEqual(log.title, "My Heading")

    def test_title_empty(self):
        log = ParsedLog(filepath=Path("/fake/path.md"), frontmatter={}, content="no heading here")
        self.assertEqual(log.title, "")


class TestExtractActionItems(unittest.TestCase):
    def _make_log(self, content):
        return ParsedLog(filepath=Path("/fake/path.md"), frontmatter={}, content=content)

    def test_basic_items(self):
        log = self._make_log("## Next Steps\n- Do this\n- Do that\n")
        items = log.extract_action_items()
        self.assertEqual(items, ["Do this", "Do that"])

    def test_skips_empty_bullets(self):
        log = self._make_log("## Next Steps\n- \n- Real item\n")
        items = log.extract_action_items()
        self.assertEqual(items, ["Real item"])

    def test_skips_reviewed_by_default(self):
        log = self._make_log("## Next Steps\n- [x] Done item\n- Pending item\n")
        items = log.extract_action_items()
        self.assertEqual(items, ["Pending item"])

    def test_includes_reviewed_with_flag(self):
        log = self._make_log("## Next Steps\n- [x] Done item\n- Pending item\n")
        items = log.extract_action_items(include_reviewed=True)
        self.assertIn("[done] Done item", items)
        self.assertIn("Pending item", items)

    def test_strips_unchecked_checkbox(self):
        log = self._make_log("## Next Steps\n- [ ] Unchecked item\n")
        items = log.extract_action_items()
        self.assertEqual(items, ["Unchecked item"])

    def test_action_items_header(self):
        log = self._make_log("## Action Items\n- Task one\n")
        items = log.extract_action_items()
        self.assertEqual(items, ["Task one"])

    def test_actions_header(self):
        log = self._make_log("## Actions\n- Task one\n")
        items = log.extract_action_items()
        self.assertEqual(items, ["Task one"])

    def test_todo_header(self):
        log = self._make_log("## Todo\n- Task one\n")
        items = log.extract_action_items()
        self.assertEqual(items, ["Task one"])

    def test_tasks_header(self):
        log = self._make_log("## Tasks\n- Task one\n")
        items = log.extract_action_items()
        self.assertEqual(items, ["Task one"])

    def test_stops_at_next_heading(self):
        log = self._make_log("## Next Steps\n- Item one\n## Session Actions\n- Not an action\n")
        items = log.extract_action_items()
        self.assertEqual(items, ["Item one"])

    def test_continuation_lines(self):
        log = self._make_log("## Next Steps\n- Main item\n  continuation text\n- Another item\n")
        items = log.extract_action_items()
        self.assertEqual(items[0], "Main item continuation text")
        self.assertEqual(items[1], "Another item")

    def test_tab_continuation(self):
        log = self._make_log("## Next Steps\n- Main item\n\tcontinuation\n")
        items = log.extract_action_items()
        self.assertEqual(items[0], "Main item continuation")

    def test_no_action_section(self):
        log = self._make_log("Just some notes.\nNo action section here.\n")
        items = log.extract_action_items()
        self.assertEqual(items, [])


class TestExtractSessionActions(unittest.TestCase):
    def _make_log(self, content):
        return ParsedLog(filepath=Path("/fake/path.md"), frontmatter={}, content=content)

    def test_basic_session_actions(self):
        log = self._make_log("## Session Actions\n- Did this\n- Did that\n")
        items = log.extract_session_actions()
        self.assertEqual(items, ["Did this", "Did that"])

    def test_continuation_lines(self):
        log = self._make_log("## Session Actions\n- Had meeting\n  with the team\n- Wrote code\n")
        items = log.extract_session_actions()
        self.assertEqual(items[0], "Had meeting with the team")
        self.assertEqual(items[1], "Wrote code")

    def test_stops_at_next_heading(self):
        log = self._make_log("## Session Actions\n- Action here\n## Next Steps\n- Not session\n")
        items = log.extract_session_actions()
        self.assertEqual(items, ["Action here"])

    def test_no_session_section(self):
        log = self._make_log("## Next Steps\n- Item\n")
        items = log.extract_session_actions()
        self.assertEqual(items, [])

    def test_skips_empty_bullets(self):
        log = self._make_log("## Session Actions\n- \n- Real action\n")
        items = log.extract_session_actions()
        self.assertEqual(items, ["Real action"])


class TestMarkActionReviewed(unittest.TestCase):
    def _write_temp(self, content):
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
        f.write(content)
        f.close()
        return Path(f.name)

    def tearDown(self):
        # Cleanup is handled per-test with try/finally or just leave it to OS
        pass

    def test_marks_plain_item(self):
        path = self._write_temp("## Next Steps\n- Do the thing\n- Other item\n")
        try:
            result = mark_action_reviewed(path, "Do the thing")
            self.assertTrue(result)
            text = path.read_text()
            self.assertIn("- [x] Do the thing", text)
            self.assertIn("- Other item", text)
        finally:
            os.unlink(path)

    def test_marks_unchecked_checkbox_item(self):
        path = self._write_temp("## Next Steps\n- [ ] Do the thing\n")
        try:
            result = mark_action_reviewed(path, "Do the thing")
            self.assertTrue(result)
            text = path.read_text()
            self.assertIn("- [x] Do the thing", text)
        finally:
            os.unlink(path)

    def test_returns_false_if_not_found(self):
        path = self._write_temp("## Next Steps\n- Something else\n")
        try:
            result = mark_action_reviewed(path, "Nonexistent item")
            self.assertFalse(result)
        finally:
            os.unlink(path)

    def test_only_modifies_inside_action_section(self):
        path = self._write_temp("## Session Actions\n- Do the thing\n## Next Steps\n- Do the thing\n")
        try:
            result = mark_action_reviewed(path, "Do the thing")
            self.assertTrue(result)
            text = path.read_text()
            # Only the one in Next Steps should be marked
            lines = text.splitlines()
            session_idx = lines.index("## Session Actions")
            next_idx = lines.index("## Next Steps")
            # Line after Session Actions should still be plain
            self.assertEqual(lines[session_idx + 1], "- Do the thing")
            # Line after Next Steps should be marked
            self.assertEqual(lines[next_idx + 1], "- [x] Do the thing")
        finally:
            os.unlink(path)


class TestParseFile(unittest.TestCase):
    def test_parse_file_with_frontmatter(self):
        content = "---\ndate: 2026-03-10\nproject: Test\ncontacts: [Alice]\ntitle: My Log\n---\n\nSome content here.\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            path = Path(f.name)
        try:
            log = parse_file(path)
            self.assertIsNotNone(log)
            self.assertEqual(log.project, "Test")
            self.assertEqual(log.contacts, ["Alice"])
            self.assertEqual(log.title, "My Log")
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
