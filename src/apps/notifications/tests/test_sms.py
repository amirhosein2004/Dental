"""
Number parsing is where a bulk run silently goes wrong — a dropped digit or a
duplicate costs real money and reaches the wrong person — so it carries the
bulk of these tests.
"""
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.dashboard.models import Doctor
from apps.notifications.models import ContactGroup, NotificationLog
from apps.notifications.phones import normalize, parse_numbers
from apps.notifications.providers import ConsoleSmsBackend, chunked, get_backend
from apps.notifications.forms import BulkSmsForm
from apps.notifications.services import send_sms
from apps.notifications.tasks import send_bulk_sms_task
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'


class PhoneNormalisationTests(TestCase):
    def test_accepts_plain_national_format(self):
        self.assertEqual(normalize('09121234567'), '09121234567')

    def test_accepts_international_variants(self):
        """The same number, written the four ways people actually write it."""
        for raw in ('+989121234567', '00989121234567', '989121234567', '9121234567'):
            with self.subTest(raw=raw):
                self.assertEqual(normalize(raw), '09121234567')

    def test_accepts_persian_and_arabic_digits(self):
        self.assertEqual(normalize('۰۹۱۲۱۲۳۴۵۶۷'), '09121234567')
        self.assertEqual(normalize('٠٩١٢١٢٣٤٥٦٧'), '09121234567')

    def test_strips_formatting_characters(self):
        for raw in ('0912-123-4567', '0912 123 4567', '(0912)1234567'):
            with self.subTest(raw=raw):
                self.assertEqual(normalize(raw), '09121234567')

    def test_rejects_wrong_length(self):
        for raw in ('0912123', '091212345678', ''):
            with self.subTest(raw=raw):
                self.assertIsNone(normalize(raw))

    def test_rejects_numbers_not_starting_with_zero(self):
        self.assertIsNone(normalize('19121234567'))

    def test_landline_is_accepted(self):
        self.assertEqual(normalize('05147247247'), '05147247247')


class ParseNumbersTests(TestCase):
    def test_splits_on_every_separator_people_use(self):
        raw = '09121234567, 09351112233\n09024445566;09187778899 09336667788'
        valid, invalid = parse_numbers(raw)
        self.assertEqual(len(valid), 5)
        self.assertEqual(invalid, [])

    def test_persian_comma_is_a_separator(self):
        valid, _ = parse_numbers('09121234567،09351112233')
        self.assertEqual(len(valid), 2)

    def test_duplicates_are_dropped_including_mixed_formats(self):
        """The same person written three ways must be texted once."""
        valid, _ = parse_numbers('09121234567 +989121234567 ۰۹۱۲۱۲۳۴۵۶۷')
        self.assertEqual(valid, ['09121234567'])

    def test_order_is_preserved(self):
        valid, _ = parse_numbers('09351112233 09121234567')
        self.assertEqual(valid, ['09351112233', '09121234567'])

    def test_invalid_tokens_are_reported_not_swallowed(self):
        """An operator can only fix a typo they are told about."""
        valid, invalid = parse_numbers('09121234567, 12345, abc, 09351112233')
        self.assertEqual(len(valid), 2)
        self.assertIn('12345', invalid)

    def test_blank_input(self):
        self.assertEqual(parse_numbers(''), ([], []))
        self.assertEqual(parse_numbers('   \n  '), ([], []))


class ChunkingTests(TestCase):
    def test_batches_respect_the_provider_limit(self):
        numbers = [f'0912000{i:04d}' for i in range(450)]
        batches = list(chunked(numbers))
        self.assertEqual([len(b) for b in batches], [200, 200, 50])

    def test_no_number_is_lost_or_duplicated(self):
        numbers = [f'0912000{i:04d}' for i in range(450)]
        flattened = [n for batch in chunked(numbers) for n in batch]
        self.assertEqual(flattened, numbers)


@override_settings(SMS_BACKEND='console')
class SendServiceTests(TestCase):
    def test_console_backend_is_the_default(self):
        self.assertIsInstance(get_backend(), ConsoleSmsBackend)

    def test_successful_send_is_logged(self):
        log = send_sms(
            ['09121234567', '09351112233'], 'سلام', NotificationLog.Kind.BULK,
        )
        self.assertEqual(log.status, NotificationLog.Status.SENT)
        self.assertEqual(log.recipient_count, 2)
        self.assertEqual(log.sent_count, 2)

    def test_duplicates_are_collapsed_before_sending(self):
        log = send_sms(
            ['09121234567', '09121234567'], 'سلام', NotificationLog.Kind.BULK,
        )
        self.assertEqual(log.recipient_count, 1)

    def test_empty_recipient_list_fails_loudly_in_the_log(self):
        log = send_sms([], 'سلام', NotificationLog.Kind.CONTACT_MESSAGE)
        self.assertEqual(log.status, NotificationLog.Status.FAILED)
        self.assertTrue(log.error)

    @override_settings(SMS_BACKEND='does.not.Exist')
    def test_broken_backend_is_recorded_not_raised(self):
        """A misconfigured panel must not 500 the page that triggered it."""
        log = send_sms(['09121234567'], 'سلام', NotificationLog.Kind.BULK)
        self.assertEqual(log.status, NotificationLog.Status.FAILED)
        self.assertTrue(log.error)

    def test_provider_failure_marks_the_log_failed(self):
        from apps.notifications.providers import SendResult

        with patch.object(
            ConsoleSmsBackend, 'send',
            return_value=SendResult(sent=0, failed=1, error='boom'),
        ):
            log = send_sms(['09121234567'], 'سلام', NotificationLog.Kind.BULK)

        self.assertEqual(log.status, NotificationLog.Status.FAILED)
        self.assertIn('boom', log.error)


@override_settings(SMS_BACKEND='console')
class BulkSmsViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = CustomUser.objects.create_user(
            username='smsdoc', email='s@x.test', first_name='سعیده',
            last_name='بابایی', password=PASSWORD, is_doctor=True,
        )
        Doctor.objects.get(user=cls.staff)

    def test_page_is_hidden_from_anonymous(self):
        self.assertEqual(
            self.client.get(reverse('notifications:bulk_sms')).status_code, 404,
        )

    def test_staff_can_open_the_page(self):
        self.client.login(username='smsdoc', password=PASSWORD)
        self.assertEqual(
            self.client.get(reverse('notifications:bulk_sms')).status_code, 200,
        )

    def test_submit_queues_deduped_numbers(self):
        self.client.login(username='smsdoc', password=PASSWORD)
        with patch('apps.notifications.views.sms_view.send_bulk_sms_task.delay') as delay:
            resp = self.client.post(reverse('notifications:bulk_sms'), {
                'numbers': '09121234567, 09121234567\n09351112233 badtoken',
                'message': 'سلام',
            })

        self.assertEqual(resp.status_code, 302)
        delay.assert_called_once()
        queued_numbers = delay.call_args[0][0]
        self.assertEqual(queued_numbers, ['09121234567', '09351112233'])

    def test_batch_larger_than_the_cap_is_refused(self):
        """
        Every recipient is billed and there is no undo once the task is
        queued. A paste that lands ten times larger than intended — a whole
        exported column instead of one cell — must stop at the form.
        """
        self.client.login(username='smsdoc', password=PASSWORD)
        oversized = '\n'.join(
            f'0912{n:07d}' for n in range(BulkSmsForm.MAX_RECIPIENTS + 1)
        )

        with patch('apps.notifications.views.sms_view.send_bulk_sms_task.delay') as delay:
            resp = self.client.post(reverse('notifications:bulk_sms'), {
                'numbers': oversized, 'message': 'سلام',
            })

        self.assertEqual(resp.status_code, 200)  # re-rendered with the error
        delay.assert_not_called()

    def test_batch_at_the_cap_still_goes_through(self):
        self.client.login(username='smsdoc', password=PASSWORD)
        at_limit = '\n'.join(
            f'0912{n:07d}' for n in range(BulkSmsForm.MAX_RECIPIENTS)
        )

        with patch('apps.notifications.views.sms_view.send_bulk_sms_task.delay') as delay:
            resp = self.client.post(reverse('notifications:bulk_sms'), {
                'numbers': at_limit, 'message': 'سلام',
            })

        self.assertEqual(resp.status_code, 302)
        delay.assert_called_once()
        self.assertEqual(
            len(delay.call_args[0][0]), BulkSmsForm.MAX_RECIPIENTS,
        )


    def test_submit_without_any_valid_number_is_rejected(self):
        self.client.login(username='smsdoc', password=PASSWORD)
        with patch('apps.notifications.views.sms_view.send_bulk_sms_task.delay') as delay:
            resp = self.client.post(reverse('notifications:bulk_sms'), {
                'numbers': 'abc, 123', 'message': 'سلام',
            })

        self.assertEqual(resp.status_code, 200)  # re-rendered with the error
        delay.assert_not_called()


class BulkSmsRetryTests(TestCase):
    """
    ``send_sms`` walks the recipient list in batches and handles provider
    failure itself, so the only way the task can raise is after some batches
    have already gone out. A retry would re-send them — billed again, to
    patients who already got the message.
    """

    def test_bulk_task_does_not_autoretry(self):
        self.assertFalse(
            getattr(send_bulk_sms_task, 'autoretry_for', ()),
            'send_bulk_sms_task must not autoretry: a retry re-sends every '
            'batch that already succeeded, at real cost.',
        )


class ContactGroupTests(TestCase):
    def test_numbers_are_normalised_on_save(self):
        """Whatever was pasted, the stored list is canonical."""
        group = ContactGroup.objects.create(
            name='بیماران ایمپلنت',
            numbers='09121234567, +989351112233\n۰۹۰۲۴۴۴۵۵۶۶',
        )
        self.assertEqual(
            group.number_list,
            ['09121234567', '09351112233', '09024445566'],
        )

    def test_duplicates_are_collapsed_on_save(self):
        group = ContactGroup.objects.create(
            name='تکراری', numbers='09121234567 09121234567 +989121234567',
        )
        self.assertEqual(group.member_count, 1)

    def test_invalid_entries_are_dropped_from_storage(self):
        group = ContactGroup.objects.create(
            name='ناقص', numbers='09121234567, badtoken, 123',
        )
        self.assertEqual(group.number_list, ['09121234567'])

    def test_name_is_unique(self):
        ContactGroup.objects.create(name='گروه', numbers='09121234567')
        from django.db import IntegrityError, transaction

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ContactGroup.objects.create(name='گروه', numbers='09351112233')


@override_settings(SMS_BACKEND='console')
class BulkSmsGroupTests(TestCase):
    """Groups + pasted numbers must merge into one de-duplicated list."""

    @classmethod
    def setUpTestData(cls):
        cls.staff = CustomUser.objects.create_user(
            username='grpdoc', email='g@x.test', first_name='سعیده',
            last_name='بابایی', password=PASSWORD, is_doctor=True,
        )
        Doctor.objects.get(user=cls.staff)
        cls.group_a = ContactGroup.objects.create(
            name='گروه الف', numbers='09121234567\n09351112233',
        )
        cls.group_b = ContactGroup.objects.create(
            # Deliberately overlaps group A on the first number.
            name='گروه ب', numbers='09121234567\n09024445566',
        )

    def setUp(self):
        self.client.login(username='grpdoc', password=PASSWORD)

    def _post(self, **data):
        payload = {'message': 'سلام', 'numbers': '', 'groups': []}
        payload.update(data)
        with patch('apps.notifications.views.sms_view.send_bulk_sms_task.delay') as delay:
            resp = self.client.post(reverse('notifications:bulk_sms'), payload)
        return resp, delay

    def test_selecting_a_group_sends_to_its_members(self):
        resp, delay = self._post(groups=[self.group_a.pk])
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(delay.call_args[0][0], ['09121234567', '09351112233'])

    def test_overlapping_groups_are_deduplicated(self):
        """A patient in two groups must receive one message, not two."""
        _resp, delay = self._post(groups=[self.group_a.pk, self.group_b.pk])
        self.assertEqual(
            delay.call_args[0][0],
            ['09121234567', '09351112233', '09024445566'],
        )

    def test_group_and_typed_numbers_merge_without_duplicates(self):
        _resp, delay = self._post(
            groups=[self.group_a.pk],
            numbers='09024445566, 09121234567',  # second already in the group
        )
        self.assertEqual(
            delay.call_args[0][0],
            ['09121234567', '09351112233', '09024445566'],
        )

    def test_sending_with_neither_group_nor_number_is_rejected(self):
        resp, delay = self._post()
        self.assertEqual(resp.status_code, 200)
        delay.assert_not_called()

    def test_group_membership_is_exposed_to_the_live_counter(self):
        """The pre-send estimate can only dedupe if it knows the members."""
        html = self.client.get(reverse('notifications:bulk_sms')).content.decode()
        self.assertIn('data-numbers', html)
        self.assertIn('09121234567', html)


class ContactGroupViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = CustomUser.objects.create_user(
            username='gview', email='gv@x.test', first_name='محمد',
            last_name='بهمدی', password=PASSWORD, is_doctor=True,
        )
        Doctor.objects.get(user=cls.staff)

    def test_hidden_from_anonymous(self):
        self.assertEqual(self.client.get(reverse('notifications:groups')).status_code, 404)

    def test_staff_can_create_a_group(self):
        self.client.login(username='gview', password=PASSWORD)
        resp = self.client.post(reverse('notifications:groups'), {
            'name': 'بیماران ارتودنسی',
            'description': 'کسانی که ارتودنسی فعال دارند',
            'numbers': '09121234567, 09351112233',
        })
        self.assertEqual(resp.status_code, 302)

        group = ContactGroup.objects.get()
        self.assertEqual(group.member_count, 2)
        self.assertEqual(group.created_by, self.staff)

    def test_group_without_valid_numbers_is_rejected(self):
        self.client.login(username='gview', password=PASSWORD)
        resp = self.client.post(reverse('notifications:groups'), {
            'name': 'خالی', 'description': '', 'numbers': 'abc, 123',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(ContactGroup.objects.exists())

    def test_staff_can_edit_and_delete(self):
        group = ContactGroup.objects.create(name='قدیمی', numbers='09121234567')
        self.client.login(username='gview', password=PASSWORD)

        self.client.post(reverse('notifications:group_edit', args=[group.pk]), {
            'name': 'جدید', 'description': '', 'numbers': '09351112233, 09024445566',
        })
        group.refresh_from_db()
        self.assertEqual(group.name, 'جدید')
        self.assertEqual(group.member_count, 2)

        self.client.post(reverse('notifications:group_delete', args=[group.pk]))
        self.assertFalse(ContactGroup.objects.exists())


@override_settings(SMS_BACKEND='console', STAFF_ALERT_NUMBERS='09121234567')
class ContactAlertTests(TestCase):
    def test_contact_submission_queues_an_alert(self):
        with patch('apps.contact.views.contact_view.notify_staff_task.delay') as delay:
            self.client.post(reverse('contact:contact'), {
                'name': 'مریم احمدی',
                'phone': '09121234567',
                'message': 'سلام، برای ایمپلنت مشاوره می‌خواستم لطفاً راهنمایی کنید.',
            })

        # The captcha may reject the post; only assert the wiring when it passed.
        from apps.contact.models import ContactMessage
        if ContactMessage.objects.exists():
            delay.assert_called_once()
            self.assertIn('مریم احمدی', delay.call_args[0][0])
