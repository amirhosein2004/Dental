"""
The staff inbox.

Everything here is behind `DoctorOrSuperuserRequiredMixin`, which answers 404
rather than 403 on purpose: a staff URL should not confirm its own existence
to whoever is knocking. The other half is the cleanup endpoint, which deletes
patient messages in bulk and therefore needs its bounds pinned.
"""
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from apps.contact.models import ContactMessage
from apps.contact.views.messages_view import CLEANUP_MAX_DAYS, CLEANUP_MIN_DAYS
from apps.dashboard.models import Doctor
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'


class InboxAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )
        cls.patient = CustomUser.objects.create_user(
            username='patient', email='p@x.test', first_name='ز', last_name='م',
            password=PASSWORD,
        )
        ContactMessage.objects.create(
            name='زهرا', phone='09121112233',
            message='سلام، برای مشاوره تماس گرفتم.',
        )

    def test_anonymous_gets_404_not_403(self):
        response = self.client.get(reverse('contact:messages'))
        self.assertEqual(response.status_code, 404)

    def test_a_signed_in_patient_also_gets_404(self):
        """Being logged in is not the same as being staff."""
        self.client.login(username='patient', password=PASSWORD)
        self.assertEqual(self.client.get(reverse('contact:messages')).status_code, 404)

    def test_a_doctor_can_read_the_inbox(self):
        self.client.login(username='doc', password=PASSWORD)
        response = self.client.get(reverse('contact:messages'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'زهرا')

    def test_the_inbox_is_not_indexed(self):
        """Patient names and numbers must never reach a search engine."""
        self.client.login(username='doc', password=PASSWORD)
        self.assertContains(self.client.get(reverse('contact:messages')), 'noindex')


class InboxFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )
        cls.unread = ContactMessage.objects.create(
            name='خوانده‌نشده', phone='09121112233',
            message='این پیام هنوز خوانده نشده است.',
        )
        cls.read = ContactMessage.objects.create(
            name='خوانده‌شده', phone='09121112234',
            message='این پیام قبلاً خوانده شده است.', is_read=True,
        )

    def setUp(self):
        self.client.login(username='doc', password=PASSWORD)

    def _names(self, query=''):
        response = self.client.get(reverse('contact:messages') + query)
        return [m.name for m in response.context['messages_list']]

    def test_default_shows_everything(self):
        self.assertCountEqual(self._names(), ['خوانده‌نشده', 'خوانده‌شده'])

    def test_unread_filter(self):
        self.assertEqual(self._names('?filter=unread'), ['خوانده‌نشده'])

    def test_read_filter(self):
        self.assertEqual(self._names('?filter=read'), ['خوانده‌شده'])

    def test_an_unknown_filter_falls_back_to_everything(self):
        """A hand-typed query string must not blank the page."""
        self.assertCountEqual(self._names('?filter=nonsense'), ['خوانده‌نشده', 'خوانده‌شده'])


class MarkReadTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )

    def setUp(self):
        self.client.login(username='doc', password=PASSWORD)
        self.first = ContactMessage.objects.create(
            name='یک', phone='09121112233',
            message='پیام آزمایشی شماره یک برای تست.',
        )
        self.second = ContactMessage.objects.create(
            name='دو', phone='09121112234',
            message='پیام آزمایشی شماره دو برای تست.',
        )

    def test_marking_one_leaves_the_others_alone(self):
        self.client.post(
            reverse('contact:mark_as_read', kwargs={'pk': self.first.pk}),
        )

        self.first.refresh_from_db()
        self.second.refresh_from_db()
        self.assertTrue(self.first.is_read)
        self.assertFalse(self.second.is_read)

    def test_mark_all_read(self):
        self.client.post(reverse('contact:mark_all_read'))

        self.assertFalse(ContactMessage.objects.filter(is_read=False).exists())

    def test_marking_read_requires_staff(self):
        self.client.logout()
        self.client.post(
            reverse('contact:mark_as_read', kwargs={'pk': self.first.pk}),
        )

        self.first.refresh_from_db()
        self.assertFalse(self.first.is_read)

    def test_a_get_does_not_change_anything(self):
        """
        Marking read is a write. Allowing it over GET would let a prefetching
        browser — or an <img> tag in any page — empty the inbox.
        """
        self.client.get(
            reverse('contact:mark_as_read', kwargs={'pk': self.first.pk}),
        )

        self.first.refresh_from_db()
        self.assertFalse(self.first.is_read)


class CleanupTests(TestCase):
    """
    Deletes patient messages in bulk. The day count arrives from a form field,
    so its bounds are the only thing between a typo and an empty inbox.
    """

    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )

    def setUp(self):
        self.client.login(username='doc', password=PASSWORD)
        patcher = patch('apps.contact.views.messages_view.delete_old_messages.delay')
        self.task = patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_valid_day_count_is_queued(self):
        self.client.post(reverse('contact:cleanup_old'), {'days': '180'})

        self.task.assert_called_once_with(180)

    def test_too_few_days_is_refused(self):
        """`?days=0` would delete the message that arrived this morning."""
        self.client.post(reverse('contact:cleanup_old'), {'days': str(CLEANUP_MIN_DAYS - 1)})

        self.task.assert_not_called()

    def test_too_many_days_is_refused(self):
        self.client.post(reverse('contact:cleanup_old'), {'days': str(CLEANUP_MAX_DAYS + 1)})

        self.task.assert_not_called()

    def test_a_negative_day_count_is_refused(self):
        self.client.post(reverse('contact:cleanup_old'), {'days': '-30'})

        self.task.assert_not_called()

    def test_junk_input_is_refused_without_raising(self):
        for value in ('abc', '', '12.5', '1e9'):
            with self.subTest(days=value):
                response = self.client.post(reverse('contact:cleanup_old'), {'days': value})
                self.assertEqual(response.status_code, 302)
        self.task.assert_not_called()

    def test_cleanup_requires_staff(self):
        self.client.logout()
        self.client.post(reverse('contact:cleanup_old'), {'days': '180'})

        self.task.assert_not_called()
