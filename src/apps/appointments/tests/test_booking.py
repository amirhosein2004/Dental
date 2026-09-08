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


class BookingModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='apdoc', email='ap@x.test', first_name='سعیده',
            last_name='بابایی', password=PASSWORD, is_doctor=True,
        )
        cls.doctor = Doctor.objects.get(user=cls.user)
        cls.slot = AvailabilitySlot.objects.create(
            doctor=cls.doctor, weekday=6, time=time(23, 30),
        )

    def _book(self, week_start=None, **overrides):
        data = {
            'slot': self.slot,
            'week_start': week_start or current_week_start(),
            'full_name': 'مریم احمدی',
            'national_code': '0499370899',
            'phone': '09121234567',
        }
        data.update(overrides)
        return Appointment.objects.create(**data)

    def test_slot_can_only_be_booked_once_per_week(self):
        self._book()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._book(full_name='رضا موسوی')

    def test_same_slot_is_free_again_next_week(self):
        """The core promise: no cleanup job — the week key does the work."""
        this_week = current_week_start()
        self._book(week_start=this_week)

        next_week = this_week + timedelta(days=7)
        other = self._book(week_start=next_week, full_name='رضا موسوی')

        self.assertEqual(Appointment.objects.count(), 2)
        self.assertEqual(other.week_start, next_week)

    def test_cancelling_frees_the_slot_immediately(self):
        booking = self._book()
        booking.status = Appointment.Status.CANCELLED
        booking.save(update_fields=['status'])

        # The unique constraint is partial (booked only), so this must succeed.
        self._book(full_name='سارا کریمی')
        self.assertEqual(
            Appointment.objects.filter(status=Appointment.Status.BOOKED).count(), 1,
        )

    def test_booking_for_ignores_cancelled(self):
        booking = self._book()
        self.assertEqual(self.slot.booking_for(), booking)

        booking.status = Appointment.Status.CANCELLED
        booking.save(update_fields=['status'])
        self.assertIsNone(self.slot.booking_for())

    def test_clean_pins_bookings_to_the_current_week(self):
        stale = Appointment(
            slot=self.slot,
            week_start=current_week_start() - timedelta(days=7),
            full_name='کاربر', national_code='0499370899', phone='09121234567',
        )
        with self.assertRaises(ValidationError):
            stale.full_clean()

    def test_duplicate_slot_definition_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AvailabilitySlot.objects.create(
                    doctor=self.doctor, weekday=6, time=time(23, 30),
                )

    def test_has_passed_compares_against_the_week_occurrence(self):
        slot = AvailabilitySlot.objects.create(
            doctor=self.doctor, weekday=0, time=time(9, 0),
        )
        week_start = current_week_start()
        start_of_week = datetime.combine(week_start, time(0, 0))
        end_of_week = datetime.combine(week_start + timedelta(days=6), time(23, 59))

        self.assertFalse(slot.has_passed(week_start, now=start_of_week))
        self.assertTrue(slot.has_passed(week_start, now=end_of_week))


class BookingViewTests(TestCase):
    """
    View-level flow.

    `has_passed` is patched off throughout: a real slot is only bookable
    before its weekly occurrence, which would make these tests pass or fail
    depending on the hour the suite runs.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='vdoc', email='v@x.test', first_name='محمد',
            last_name='بهمدی', password=PASSWORD, is_doctor=True,
        )
        cls.doctor = Doctor.objects.get(user=cls.user)
        cls.slot = AvailabilitySlot.objects.create(
            doctor=cls.doctor, weekday=6, time=time(23, 30),
        )

    def setUp(self):
        patcher = patch.object(AvailabilitySlot, 'has_passed', return_value=False)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _payload(self, **overrides):
        data = {
            'full_name': 'مریم احمدی',
            'national_code': '0499370899',
            'phone': '09121234567',
            'note': '',
        }
        data.update(overrides)
        return data

    def test_board_is_public(self):
        self.assertEqual(self.client.get(reverse('appointments:board')).status_code, 200)

    def test_booking_creates_appointment_for_current_week(self):
        resp = self.client.post(
            reverse('appointments:book', args=[self.slot.pk]), self._payload(),
        )
        self.assertEqual(resp.status_code, 302)

        booking = Appointment.objects.get()
        self.assertEqual(booking.week_start, current_week_start())
        self.assertEqual(booking.slot, self.slot)

    def test_second_booking_of_same_slot_is_refused(self):
        self.client.post(reverse('appointments:book', args=[self.slot.pk]), self._payload())
        self.client.post(
            reverse('appointments:book', args=[self.slot.pk]),
            self._payload(full_name='رضا موسوی', phone='09351112233'),
        )
        self.assertEqual(
            Appointment.objects.filter(status=Appointment.Status.BOOKED).count(), 1,
        )

    def test_invalid_national_code_is_rejected(self):
        resp = self.client.post(
            reverse('appointments:book', args=[self.slot.pk]),
            self._payload(national_code='1234567890'),
        )
        self.assertEqual(resp.status_code, 200)  # re-rendered with errors
        self.assertFalse(Appointment.objects.exists())

    def test_persian_digits_are_normalised(self):
        """Iranian phone keyboards produce Persian numerals by default."""
        resp = self.client.post(
            reverse('appointments:book', args=[self.slot.pk]),
            self._payload(national_code='۰۴۹۹۳۷۰۸۹۹', phone='۰۹۱۲۱۲۳۴۵۶۷'),
        )
        self.assertEqual(resp.status_code, 302)

        booking = Appointment.objects.get()
        self.assertEqual(booking.national_code, '0499370899')
        self.assertEqual(booking.phone, '09121234567')

    def test_inactive_slot_is_not_bookable(self):
        self.slot.is_active = False
        self.slot.save(update_fields=['is_active'])
        resp = self.client.get(reverse('appointments:book', args=[self.slot.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_staff_pages_are_hidden_from_anonymous(self):
        for name in ('appointments:manage', 'appointments:list'):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 404)

    def test_doctor_sees_only_their_own_slots(self):
        other = CustomUser.objects.create_user(
            username='other', email='o@x.test', first_name='نگار',
            last_name='رضایی', password=PASSWORD, is_doctor=True,
        )
        AvailabilitySlot.objects.create(
            doctor=Doctor.objects.get(user=other), weekday=1, time=time(10, 0),
        )

        self.client.login(username='vdoc', password=PASSWORD)
        resp = self.client.get(reverse('appointments:manage'))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context['slots']), [self.slot])

    def test_doctor_cannot_delete_another_doctors_slot(self):
        other = CustomUser.objects.create_user(
            username='other2', email='o2@x.test', first_name='نگار',
            last_name='رضایی', password=PASSWORD, is_doctor=True,
        )
        other_slot = AvailabilitySlot.objects.create(
            doctor=Doctor.objects.get(user=other), weekday=1, time=time(10, 0),
        )

        self.client.login(username='vdoc', password=PASSWORD)
        resp = self.client.post(reverse('appointments:delete_slot', args=[other_slot.pk]))

        self.assertEqual(resp.status_code, 404)
        self.assertTrue(AvailabilitySlot.objects.filter(pk=other_slot.pk).exists())

    def test_cancel_frees_the_slot(self):
        self.client.post(reverse('appointments:book', args=[self.slot.pk]), self._payload())
        booking = Appointment.objects.get()

        self.client.login(username='vdoc', password=PASSWORD)
        self.client.post(reverse('appointments:cancel', args=[booking.pk]))

        booking.refresh_from_db()
        self.assertEqual(booking.status, Appointment.Status.CANCELLED)
        self.assertIsNone(self.slot.booking_for())

    def test_booking_queues_a_staff_alert(self):
        with patch('apps.appointments.views.booking_view.notify_staff_task.delay') as delay:
            self.client.post(
                reverse('appointments:book', args=[self.slot.pk]), self._payload(),
            )
        delay.assert_called_once()
        text = delay.call_args[0][0]
        # The doctor must be able to tell *which* slot filled from the SMS alone.
        self.assertIn('23:30', text)
        self.assertIn('مریم احمدی', text)

    def test_booking_survives_a_broken_message_queue(self):
        """A dead broker must not turn a saved booking into an error page."""
        with patch(
            'apps.appointments.views.booking_view.notify_staff_task.delay',
            side_effect=OSError('broker down'),
        ):
            resp = self.client.post(
                reverse('appointments:book', args=[self.slot.pk]), self._payload(),
            )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Appointment.objects.count(), 1)
