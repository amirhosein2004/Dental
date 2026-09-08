"""
Reading environment variables in settings.

Every example env file in this repository lists keys with no value, so the
reader can see the full shape of the file. That means the settings module is
routinely handed variables that are *present but empty* — and `os.getenv`'s
default only applies when a name is missing entirely.

For a string setting an empty value is a quiet misconfiguration. For
`EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))` it was a ValueError raised at
import time, which took the whole project down before a single setting had
been read: copying `.env.example` to `.env` and running `manage.py check` was
enough to trigger it.
"""
import os
from unittest import mock

from django.test import SimpleTestCase

from config.settings.base import _env


class EnvHelperTests(SimpleTestCase):
    def test_a_missing_variable_falls_back(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(_env('NOT_SET_ANYWHERE', 587), 587)

    def test_an_empty_variable_falls_back_too(self):
        """The case `os.getenv` gets wrong, and the reason this helper exists."""
        with mock.patch.dict(os.environ, {'DENTAL_PROBE': ''}):
            self.assertEqual(_env('DENTAL_PROBE', 587), 587)

    def test_a_real_value_wins(self):
        with mock.patch.dict(os.environ, {'DENTAL_PROBE': '2525'}):
            self.assertEqual(_env('DENTAL_PROBE', 587), '2525')

    def test_a_whitespace_value_is_kept(self):
        """
        Only truly empty counts as absent. A value of `' '` is more likely a
        deliberate oddity than a blank line, and silently discarding it would
        hide the mistake rather than surface it.
        """
        with mock.patch.dict(os.environ, {'DENTAL_PROBE': ' '}):
            self.assertEqual(_env('DENTAL_PROBE', 587), ' ')


class EmailPortTests(SimpleTestCase):
    def test_the_port_is_an_int(self):
        """
        Django hands EMAIL_PORT to smtplib, which needs a number. A string
        survives import and fails later, at the point of sending — which for
        this project is inside a login OTP.
        """
        from django.conf import settings

        self.assertIsInstance(settings.EMAIL_PORT, int)
