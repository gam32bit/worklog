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

    def test_does_not_raise(self):
        d = date(2026, 3, 12)
        try:
            result = log_template(d, project="TestProject", contacts=["Alice", "Bob"], title="My Log")
        except Exception as e:
            self.fail(f"log_template() raised an exception: {e}")

    def test_contains_date(self):
        d = date(2026, 3, 12)
        result = log_template(d)
        self.assertIn("2026-03-12", result)

    def test_contains_project(self):
        d = date(2026, 3, 12)
        result = log_template(d, project="MyProject")
        self.assertIn("MyProject", result)

    def test_contains_contacts(self):
        d = date(2026, 3, 12)
        result = log_template(d, contacts=["Alice", "Bob"])
        self.assertIn("Alice", result)
        self.assertIn("Bob", result)

    def test_contains_title(self):
        d = date(2026, 3, 12)
        result = log_template(d, title="My Sprint Log")
        self.assertIn("My Sprint Log", result)

    def test_has_session_actions_section(self):
        d = date(2026, 3, 12)
        result = log_template(d)
        self.assertIn("## Session Actions", result)

    def test_has_next_steps_section(self):
        d = date(2026, 3, 12)
        result = log_template(d)
        self.assertIn("## Next Steps", result)

    def test_has_yaml_frontmatter_markers(self):
        d = date(2026, 3, 12)
        result = log_template(d)
        self.assertTrue(result.startswith("---"))
        # There should be at least two '---' markers
        self.assertGreaterEqual(result.count("---"), 2)

    def test_empty_contacts_list(self):
        d = date(2026, 3, 12)
        result = log_template(d, contacts=[])
        self.assertIn("contacts: []", result)

    def test_none_contacts(self):
        d = date(2026, 3, 12)
        result = log_template(d, contacts=None)
        self.assertIn("contacts: []", result)

    def test_body_placeholder_not_doubled(self):
        """Ensure the template does not contain {{BODY}} (raw braces) in output."""
        d = date(2026, 3, 12)
        result = log_template(d)
        self.assertNotIn("{{BODY}}", result)
        self.assertIn("{BODY}", result)


if __name__ == '__main__':
    unittest.main()
