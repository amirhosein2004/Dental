"""
The behaviours that are easy to get wrong and expensive to get wrong: week
rollover (the whole "resets every Saturday" promise), the double-booking race,
and the identity checks standing between the schedule and junk data.
"""
from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.appointments.models import Appointment, AvailabilitySlot
from apps.appointments.weeks import (
    current_week_start,
    from_py_weekday,
    slot_date,
    to_py_weekday,
    week_start_for,
)
from apps.dashboard.models import Doctor
from apps.users.models import CustomUser
from utils.data.validators import validate_national_code

PASSWORD = 'test-pass-1234'

# A known Saturday, so tests never depend on the day they happen to run.
SATURDAY = date(2026, 7, 25)


class WeekMathTests(TestCase):
    def test_reference_date_really_is_saturday(self):
        self.assertEqual(SATURDAY.weekday(), 5)

    def test_saturday_is_its_own_week_start(self):
        self.assertEqual(week_start_for(SATURDAY), SATURDAY)

    def test_every_day_maps_back_to_its_saturday(self):
        for offset in range(7):
            day = SATURDAY + timedelta(days=offset)
            with self.subTest(day=day.isoformat()):
                self.assertEqual(week_start_for(day), SATURDAY)

    def test_friday_still_belongs_to_the_week_that_is_running(self):
        """Friday is the last day; it must not roll over early."""
        self.assertEqual(week_start_for(SATURDAY + timedelta(days=6)), SATURDAY)

    def test_next_saturday_starts_a_new_week(self):
        next_saturday = SATURDAY + timedelta(days=7)
        self.assertEqual(week_start_for(next_saturday), next_saturday)
        self.assertNotEqual(week_start_for(next_saturday), SATURDAY)

    def test_weekday_index_roundtrip(self):
        for iranian in range(7):
            with self.subTest(iranian=iranian):
                self.assertEqual(from_py_weekday(to_py_weekday(iranian)), iranian)

    def test_index_zero_is_saturday(self):
        self.assertEqual(to_py_weekday(0), 5)

    def test_slot_date_walks_the_week(self):
        self.assertEqual(slot_date(SATURDAY, 0), SATURDAY)
        self.assertEqual(slot_date(SATURDAY, 6), SATURDAY + timedelta(days=6))

    def test_datetime_input_is_accepted(self):
        self.assertEqual(week_start_for(datetime(2026, 7, 28, 13, 30)), SATURDAY)


