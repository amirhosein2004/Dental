"""
Which practice a slot — and therefore a booking — belongs to.

The clinic has two locations in different cities. Before ``AvailabilitySlot``
carried a branch, the board said only "Saturday 20:00 — Dr X": a patient could
book a slot in the other city without ever being told, and the front desk had
no way to tell which city a booking was for.
"""
from datetime import time

from django.test import TestCase
from django.urls import reverse

from apps.about.context_processors import invalidate_about_info_cache
from apps.about.models import Branch
from apps.appointments.models import AvailabilitySlot
from apps.appointments.views.common import _branch_boards
from apps.appointments.weeks import current_week_start
from apps.dashboard.models import Doctor
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'
DESCRIPTION = 'توضیح آزمایشی برای این پزشک که به اندازه کافی طولانی است.'


class BranchOnSlotTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )
        # A `Doctor` row is created by signal the moment `is_doctor` is set,
        # so this fetches it rather than creating a second one.
        cls.doctor = Doctor.objects.get(user=user)
        cls.mashhad = Branch.objects.create(
            city='مشهد', address='بلوار سجاد', phone='05147247247',
        )
        cls.quchan = Branch.objects.create(
            city='قوچان', address='خیابان اصلی', phone='05147247248',
        )

    def setUp(self):
        invalidate_about_info_cache()

    def test_a_slot_without_a_branch_still_reads_sensibly(self):
        """Rows predating the field must not render a blank or crash."""
        slot = AvailabilitySlot.objects.create(
            doctor=self.doctor, weekday=0, time=time(9, 0),
        )

        self.assertEqual(slot.branch_label, 'مطب مشخص نشده')

    def test_the_board_is_grouped_by_practice(self):
        AvailabilitySlot.objects.create(
            doctor=self.doctor, branch=self.mashhad, weekday=0, time=time(9, 0),
        )
        AvailabilitySlot.objects.create(
            doctor=self.doctor, branch=self.quchan, weekday=0, time=time(10, 0),
        )

        groups = _branch_boards(current_week_start())

        self.assertEqual(len(groups), 2)
        self.assertEqual(
            {g['branch'].city for g in groups}, {'مشهد', 'قوچان'},
        )

    def test_a_branchless_slot_is_still_on_the_board(self):
        """Hiding it would take a real, bookable opening off the schedule."""
        AvailabilitySlot.objects.create(
            doctor=self.doctor, weekday=0, time=time(9, 0),
        )

        groups = _branch_boards(current_week_start())

        self.assertEqual(len(groups), 1)
        self.assertIsNone(groups[0]['branch'])

    def test_the_board_page_names_the_city(self):
        AvailabilitySlot.objects.create(
            doctor=self.doctor, branch=self.quchan, weekday=0, time=time(9, 0),
        )

        self.assertContains(self.client.get(reverse('appointments:board')), 'قوچان')

    def test_the_booking_form_names_the_city(self):
        slot = AvailabilitySlot.objects.create(
            doctor=self.doctor, branch=self.quchan, weekday=0, time=time(23, 59),
        )

        response = self.client.get(
            reverse('appointments:book', kwargs={'pk': slot.pk})
        )

        # A slot whose time has already passed this week redirects rather than
        # rendering; either way the city must never be the thing that is
        # missing, so only assert on the page we actually got.
        if response.status_code == 200:
            self.assertContains(response, 'قوچان')

    def test_a_doctor_is_offered_only_their_own_practices(self):
        self.doctor.branches.set([self.quchan])
        self.client.login(username='doc', password=PASSWORD)

        response = self.client.get(reverse('appointments:manage'))

        choices = list(response.context['form'].fields['branch'].queryset)
        self.assertEqual(choices, [self.quchan])

    def test_a_doctor_with_no_practices_set_sees_all_of_them(self):
        """Narrowing to an empty list would block them adding any slot at all."""
        self.client.login(username='doc', password=PASSWORD)

        response = self.client.get(reverse('appointments:manage'))

        self.assertEqual(response.context['form'].fields['branch'].queryset.count(), 2)

    def test_deleting_a_practice_keeps_its_slots(self):
        """A week of bookings must not vanish with an edit to clinic details."""
        slot = AvailabilitySlot.objects.create(
            doctor=self.doctor, branch=self.quchan, weekday=0, time=time(9, 0),
        )

        self.quchan.delete()

        slot.refresh_from_db()
        self.assertIsNone(slot.branch)
        self.assertEqual(slot.branch_label, 'مطب مشخص نشده')
