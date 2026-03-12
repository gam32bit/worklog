"""Tests for worklog.config date parsing and date range helpers."""

import unittest
from datetime import date, timedelta
from unittest.mock import patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from worklog import config


class TestParseDateInput(unittest.TestCase):
    """Tests for config.parse_date_input()."""

    def setUp(self):
        self.today = date(2026, 3, 12)  # Thursday

    def _parse(self, text):
        with patch('worklog.config.date') as mock_date:
            mock_date.today.return_value = self.today
            mock_date.fromisoformat = date.fromisoformat
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            return config.parse_date_input(text)

    def test_empty_string_returns_today(self):
        result = self._parse("")
        self.assertEqual(result, self.today)

    def test_today_keyword(self):
        result = self._parse("today")
        self.assertEqual(result, self.today)

    def test_tomorrow(self):
        result = self._parse("tomorrow")
        self.assertEqual(result, self.today + timedelta(days=1))

    def test_yesterday(self):
        result = self._parse("yesterday")
        self.assertEqual(result, self.today - timedelta(days=1))

    def test_eow_returns_next_friday(self):
        # Today is Thursday 2026-03-12; eow = Friday 2026-03-13
        result = self._parse("eow")
        self.assertEqual(result.weekday(), 4)  # Friday
        self.assertGreaterEqual(result, self.today)
        delta = (result - self.today).days
        self.assertLessEqual(delta, 7)

    def test_eow_when_today_is_friday(self):
        friday = date(2026, 3, 13)
        with patch('worklog.config.date') as mock_date:
            mock_date.today.return_value = friday
            mock_date.fromisoformat = date.fromisoformat
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = config.parse_date_input("eow")
        # (4 - 4) % 7 = 0, so eow on a Friday returns same day
        self.assertEqual(result, friday)

    def test_relative_days(self):
        result = self._parse("+3")
        self.assertEqual(result, self.today + timedelta(days=3))

    def test_relative_days_zero(self):
        result = self._parse("+0")
        self.assertEqual(result, self.today)

    def test_iso_date(self):
        result = self._parse("2025-06-15")
        self.assertEqual(result, date(2025, 6, 15))

    def test_month_day(self):
        result = self._parse("06-15")
        self.assertEqual(result.month, 6)
        self.assertEqual(result.day, 15)

    def test_day_only(self):
        result = self._parse("5")
        self.assertEqual(result.day, 5)

    def test_day_of_week_monday(self):
        # Today is Thursday 2026-03-12; most recent Monday = 2026-03-09
        result = self._parse("monday")
        self.assertEqual(result.weekday(), 0)
        self.assertLessEqual(result, self.today)

    def test_day_of_week_returns_past_or_today(self):
        # Thursday -> returns today itself
        result = self._parse("thursday")
        self.assertEqual(result, self.today)

    def test_invalid_input_returns_today(self):
        # Invalid input should print a warning and return today
        with patch('builtins.print'):
            result = self._parse("notadate")
        self.assertEqual(result, self.today)


class TestDateRangeHelpers(unittest.TestCase):
    """Tests for is_this_week, is_last_week, is_this_month, is_last_month."""

    def setUp(self):
        # Patch date.today() to return a fixed date: Thursday 2026-03-12
        self.today = date(2026, 3, 12)
        self.patcher = patch('worklog.config.date')
        self.mock_date = self.patcher.start()
        self.mock_date.today.return_value = self.today
        self.mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

    def tearDown(self):
        self.patcher.stop()

    def test_is_this_week_monday(self):
        monday = date(2026, 3, 9)
        self.assertTrue(config.is_this_week(monday))

    def test_is_this_week_sunday(self):
        sunday = date(2026, 3, 15)
        self.assertTrue(config.is_this_week(sunday))

    def test_is_this_week_outside(self):
        last_sunday = date(2026, 3, 8)
        self.assertFalse(config.is_this_week(last_sunday))

    def test_is_last_week(self):
        last_monday = date(2026, 3, 2)
        self.assertTrue(config.is_last_week(last_monday))
        last_sunday = date(2026, 3, 8)
        self.assertTrue(config.is_last_week(last_sunday))

    def test_is_last_week_outside(self):
        this_monday = date(2026, 3, 9)
        self.assertFalse(config.is_last_week(this_monday))

    def test_is_this_month(self):
        self.assertTrue(config.is_this_month(date(2026, 3, 1)))
        self.assertTrue(config.is_this_month(date(2026, 3, 31)))
        self.assertFalse(config.is_this_month(date(2026, 2, 28)))

    def test_is_last_month(self):
        self.assertTrue(config.is_last_month(date(2026, 2, 1)))
        self.assertFalse(config.is_last_month(date(2026, 3, 1)))

    def test_is_last_month_january(self):
        # When today is Jan, last month is December of previous year
        jan = date(2026, 1, 15)
        self.mock_date.today.return_value = jan
        self.assertTrue(config.is_last_month(date(2025, 12, 15)))
        self.assertFalse(config.is_last_month(date(2026, 1, 10)))


if __name__ == '__main__':
    unittest.main()
