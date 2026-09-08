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


class NationalCodeTests(TestCase):
    def test_accepts_valid_codes(self):
        for code in ('0499370899', '0790419904', '0084575948'):
            with self.subTest(code=code):
                validate_national_code(code)  # must not raise

    def test_rejects_bad_check_digit(self):
        with self.assertRaises(ValidationError):
            validate_national_code('0499370898')

    def test_rejects_wrong_length(self):
        for code in ('123', '12345678901'):
            with self.subTest(code=code):
                with self.assertRaises(ValidationError):
                    validate_national_code(code)

    def test_rejects_repdigits(self):
        """
        These satisfy the checksum by coincidence, which is exactly why the
        validator rejects them explicitly rather than trusting the arithmetic.
        """
        for code in ('0000000000', '1111111111', '5555555555'):
            with self.subTest(code=code):
                with self.assertRaises(ValidationError):
                    validate_national_code(code)

    def test_rejects_non_digits(self):
        with self.assertRaises(ValidationError):
            validate_national_code('04993708ab')


