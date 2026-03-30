"""Tests for worklog.templates module."""

import unittest
from datetime import date

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from worklog.templates import log_template


class TestLogTemplate(unittest.TestCase):
    def test_generates_valid_content(self):
        d = date(2026, 3, 12)
        result = log_template(d)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_contains_literal_body_placeholder(self):
        d = date(2026, 3, 12)
        result = log_template(d)
        self.assertIn("{BODY}", result)

    def test_body_placeholder_not_doubled(self):
        d = date(2026, 3, 12)
        result = log_template(d)
        self.assertNotIn("{{BODY}}", result)
        self.assertIn("{BODY}", result)

    def test_contains_date(self):
        d = date(2026, 3, 12)
        result = log_template(d)
        self.assertIn("2026-03-12", result)

    def test_contains_project(self):
        d = date(2026, 3, 12)
        result = log_template(d, project="MyProject")
        self.assertIn("MyProject", result)

    def test_contains_title(self):
        d = date(2026, 3, 12)
        result = log_template(d, title="My Sprint Log")
        self.assertIn("My Sprint Log", result)

    def test_has_summary_field(self):
        d = date(2026, 3, 12)
        result = log_template(d)
        self.assertIn("summary:", result)

    def test_has_yaml_frontmatter_markers(self):
        d = date(2026, 3, 12)
        result = log_template(d)
        self.assertTrue(result.startswith("---"))
        self.assertGreaterEqual(result.count("---"), 2)

    def test_no_contacts_field(self):
        d = date(2026, 3, 12)
        result = log_template(d)
        self.assertNotIn("contacts:", result)

    def test_no_session_actions_section(self):
        d = date(2026, 3, 12)
        result = log_template(d)
        self.assertNotIn("## Session Actions", result)

    def test_no_next_steps_section(self):
        d = date(2026, 3, 12)
        result = log_template(d)
        self.assertNotIn("## Next Steps", result)

    def test_does_not_raise(self):
        d = date(2026, 3, 12)
        try:
            log_template(d, project="TestProject", title="My Log")
        except Exception as e:
            self.fail(f"log_template() raised an exception: {e}")


if __name__ == '__main__':
    unittest.main()
