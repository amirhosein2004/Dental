"""
Week arithmetic for the booking system.

The clinic's schedule is a *recurring weekly template*: a doctor declares
"Saturday 20:00 is open", and that slot is bookable once per week. Rather than
generating rows for every future date (which would need a cron job to top up
and to expire), each booking is stamped with the Saturday that starts its week.
A slot is therefore free again the moment the week rolls over — no scheduled
job, nothing to clean up.

Weekday numbering follows the Iranian calendar: Saturday is 0 and Friday is 6.
Python's own `date.weekday()` starts on Monday, so every conversion goes
through here instead of being open-coded at call sites.
"""
from datetime import date as date_cls, datetime, timedelta

# Saturday in Python's Monday-based numbering.
_PY_SATURDAY = 5

WEEKDAYS = (
    (0, 'شنبه'),
    (1, 'یک‌شنبه'),
    (2, 'دوشنبه'),
    (3, 'سه‌شنبه'),
    (4, 'چهارشنبه'),
    (5, 'پنج‌شنبه'),
    (6, 'جمعه'),
)

WEEKDAY_LABELS = dict(WEEKDAYS)


def to_py_weekday(weekday):
    """Iranian index (0=Saturday) -> Python index (0=Monday)."""
    return (weekday + _PY_SATURDAY) % 7


def from_py_weekday(py_weekday):
    """Python index (0=Monday) -> Iranian index (0=Saturday)."""
    return (py_weekday - _PY_SATURDAY) % 7


def week_start_for(value):
    """
    Return the Saturday that opens the week containing `value`.

    Accepts a date or datetime; always returns a date. This is the value
    stored on every booking, and the reason bookings expire on their own.
    """
    if isinstance(value, datetime):
        value = value.date()
    return value - timedelta(days=from_py_weekday(value.weekday()))


def current_week_start(today=None):
    """Week start for today (injectable for tests)."""
    return week_start_for(today or date_cls.today())


def slot_date(week_start, weekday):
    """Calendar date of `weekday` inside the week beginning at `week_start`."""
    return week_start + timedelta(days=weekday)


def slot_datetime(week_start, weekday, time):
    """Full datetime of a slot occurrence — used for 'already passed' checks."""
    return datetime.combine(slot_date(week_start, weekday), time)
