"""
The FAQ block on the treatment form.

``ServiceFAQ`` existed from the start but had no UI outside the Django admin,
so the questions that make a treatment page match how patients actually search
("ایمپلنت چقدر طول می‌کشد") could not be written by the person who knows the
answer.
"""
import io

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage

from apps.service.models import Service, ServiceFAQ
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'
DESCRIPTION = 'توضیح آزمایشی برای این خدمت که به اندازه کافی طولانی است.'


def tiny_jpeg(name='x.jpg'):
    buf = io.BytesIO()
    PILImage.new('RGB', (10, 10), (10, 120, 110)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


def faq_management(total=2, initial=0):
    return {
        'faqs-TOTAL_FORMS': total,
        'faqs-INITIAL_FORMS': initial,
        'faqs-MIN_NUM_FORMS': 0,
        'faqs-MAX_NUM_FORMS': 1000,
    }


class ServiceFormFieldTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )

    def setUp(self):
        cache.clear()
        self.client.login(username='doc', password=PASSWORD)

    def test_the_body_text_can_be_written_from_the_staff_form(self):
        """`content` is what the page ranks on; the form used to omit it."""
        payload = {
            'title': 'لمینت', 'description': DESCRIPTION, 'image': tiny_jpeg(),
            'content': '<p>متن کامل خدمت لمینت.</p>',
            'meta_title': '', 'meta_description': '', 'order': 0,
        }
        payload.update(faq_management(total=0))

        self.client.post(reverse('service:add_service'), payload)

        self.assertIn('متن کامل خدمت لمینت', Service.objects.get(title='لمینت').content)

    def test_a_submit_without_the_faq_block_still_saves_the_treatment(self):
        """The questions are an optional add-on, not a precondition."""
        self.client.post(reverse('service:add_service'), {
            'title': 'ارتودنسی', 'description': DESCRIPTION, 'image': tiny_jpeg(),
        })

        self.assertTrue(Service.objects.filter(title='ارتودنسی').exists())


class ServiceFAQFormsetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )

    def setUp(self):
        cache.clear()
        self.client.login(username='doc', password=PASSWORD)
        self.service = Service.objects.create(
            title='ایمپلنت', description=DESCRIPTION, image=tiny_jpeg(),
        )

    def _update(self, extra):
        payload = {
            'title': self.service.title,
            'description': self.service.description,
            'content': '',
            'meta_title': '', 'meta_description': '', 'order': 0,
        }
        payload.update(extra)
        return self.client.post(
            reverse('service:update_service', kwargs={'pk': self.service.pk}),
            payload,
        )

    def test_a_question_can_be_added(self):
        data = faq_management(total=1)
        data.update({
            'faqs-0-id': '',
            'faqs-0-question': 'ایمپلنت چقدر طول می‌کشد؟',
            'faqs-0-answer': 'بین سه تا شش ماه.',
            'faqs-0-order': 0,
        })

        self._update(data)

        self.assertEqual(self.service.faqs.count(), 1)

    def test_an_empty_order_box_is_accepted(self):
        data = faq_management(total=1)
        data.update({
            'faqs-0-id': '',
            'faqs-0-question': 'دردناک است؟',
            'faqs-0-answer': 'با بی‌حسی موضعی، خیر.',
            'faqs-0-order': '',
        })

        self._update(data)

        self.assertEqual(self.service.faqs.get().order, 0)

    def test_a_question_can_be_deleted(self):
        faq = ServiceFAQ.objects.create(
            service=self.service, question='قدیمی؟', answer='بله.',
        )
        data = faq_management(total=1, initial=1)
        data.update({
            'faqs-0-id': faq.pk,
            'faqs-0-question': faq.question,
            'faqs-0-answer': faq.answer,
            'faqs-0-order': 0,
            'faqs-0-DELETE': 'on',
        })

        self._update(data)

        self.assertFalse(ServiceFAQ.objects.filter(pk=faq.pk).exists())

    def test_blank_rows_are_ignored(self):
        """
        The "افزودن سؤال" button can add a row the writer then changes their
        mind about. Removing it clears the inputs rather than detaching the
        node — a gap in the ``faqs-N-`` indexes reads to Django as a tampered
        ManagementForm — so a submitted blank row has to be dropped silently.
        """
        data = faq_management(total=2)
        data.update({
            'faqs-0-id': '', 'faqs-0-question': '', 'faqs-0-answer': '', 'faqs-0-order': '',
            'faqs-1-id': '', 'faqs-1-question': '', 'faqs-1-answer': '', 'faqs-1-order': '',
        })

        self._update(data)

        self.assertEqual(self.service.faqs.count(), 0)


class FAQHubTests(TestCase):
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

    def setUp(self):
        cache.clear()

    def test_anonymous_gets_404(self):
        self.assertEqual(self.client.get(reverse('service:faq_hub')).status_code, 404)

    def test_a_signed_in_patient_also_gets_404(self):
        self.client.login(username='patient', password=PASSWORD)

        self.assertEqual(self.client.get(reverse('service:faq_hub')).status_code, 404)

    def test_the_treatment_form_opens_with_no_blank_rows(self):
        """
        `extra=0`. The block used to open with two empty question boxes on
        every treatment, which read as two questions the form required.
        """
        self.client.login(username='doc', password=PASSWORD)

        response = self.client.get(reverse('service:add_service'))

        self.assertEqual(len(response.context['faq_formset'].forms), 0)

    def test_a_doctor_sees_which_treatment_has_no_questions(self):
        Service.objects.create(
            title='ایمپلنت', description=DESCRIPTION, image=tiny_jpeg(),
        )
        self.client.login(username='doc', password=PASSWORD)

        response = self.client.get(reverse('service:faq_hub'))

        self.assertContains(response, 'هنوز سؤالی ندارد')


class FAQHubCreateTests(TestCase):
    """
    Writing a question from the FAQ panel instead of from a treatment form.

    A ``ServiceFAQ`` cannot exist without a treatment, so the form asks which
    one; picking it is what puts the answer on that treatment's page. The
    question still gets no page of its own — a site-wide FAQ page would
    compete with these very treatment pages for the same searches.
    """

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

    def setUp(self):
        cache.clear()
        self.service = Service.objects.create(
            title='ایمپلنت', description=DESCRIPTION, image=tiny_jpeg(),
        )

    def _payload(self, **overrides):
        data = {
            'service': self.service.pk,
            'question': 'ایمپلنت چقدر طول می‌کشد؟',
            'answer': 'بین سه تا شش ماه.',
            'order': '',
        }
        data.update(overrides)
        return data

    def test_a_doctor_can_write_a_question_from_the_panel(self):
        self.client.login(username='doc', password=PASSWORD)

        self.client.post(reverse('service:faq_hub'), self._payload())

        self.assertEqual(self.service.faqs.count(), 1)

    def test_the_question_lands_on_the_chosen_treatment(self):
        other = Service.objects.create(
            title='ارتودنسی', description=DESCRIPTION, image=tiny_jpeg('y.jpg'),
        )
        self.client.login(username='doc', password=PASSWORD)

        self.client.post(reverse('service:faq_hub'), self._payload(service=other.pk))

        self.assertEqual(self.service.faqs.count(), 0)
        self.assertEqual(other.faqs.count(), 1)

    def test_an_empty_order_box_is_accepted(self):
        self.client.login(username='doc', password=PASSWORD)

        self.client.post(reverse('service:faq_hub'), self._payload())

        self.assertEqual(self.service.faqs.get().order, 0)

    def test_a_question_without_a_treatment_is_rejected(self):
        self.client.login(username='doc', password=PASSWORD)

        response = self.client.post(reverse('service:faq_hub'), self._payload(service=''))

        self.assertEqual(ServiceFAQ.objects.count(), 0)
        self.assertIn('service', response.context['form'].errors)

    def test_a_new_question_reaches_the_public_treatment_page(self):
        """The detail page caches for a day; the write has to bust it."""
        self.client.get(self.service.get_absolute_url())      # warm
        self.client.login(username='doc', password=PASSWORD)

        self.client.post(reverse('service:faq_hub'), self._payload())

        self.assertContains(
            self.client.get(self.service.get_absolute_url()),
            'ایمپلنت چقدر طول می‌کشد؟',
        )

    def test_a_signed_in_patient_cannot_write_one(self):
        self.client.login(username='patient', password=PASSWORD)

        self.client.post(reverse('service:faq_hub'), self._payload())

        self.assertEqual(ServiceFAQ.objects.count(), 0)

    def test_an_anonymous_visitor_cannot_write_one(self):
        self.client.post(reverse('service:faq_hub'), self._payload())

        self.assertEqual(ServiceFAQ.objects.count(), 0)


class ServiceDescriptionTests(TestCase):
    """
    The card blurb is rich text now.

    It was a plain 500-character box whose cap counted the stored string — so
    bolding three words spent about 30 characters of ``<strong>`` the writer
    could not see. It is edited in a small editor, measured on the text a
    reader actually reads, and sanitised on the way in because the treatment
    page renders it with ``|safe``.
    """

    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )

    def setUp(self):
        cache.clear()
        self.client.login(username='doc', password=PASSWORD)

    def _add(self, description):
        payload = {
            'title': 'لمینت', 'description': description, 'image': tiny_jpeg(),
            'content': '', 'meta_title': '', 'meta_description': '', 'order': 0,
        }
        payload.update(faq_management(total=0))
        return self.client.post(reverse('service:add_service'), payload)

    def test_formatting_is_kept(self):
        self._add('<p>' + DESCRIPTION + ' <strong>مهم</strong></p>')

        self.assertIn('<strong>مهم</strong>', Service.objects.get(title='لمینت').description)

    def test_a_script_tag_is_stripped(self):
        """The treatment page renders this with `|safe`."""
        self._add('<p>' + DESCRIPTION + '</p><script>alert(1)</script>')

        self.assertNotIn('<script', Service.objects.get(title='لمینت').description)

    def test_the_cap_counts_the_text_not_the_markup(self):
        """A blurb that fits in 1500 characters of prose must be accepted."""
        self._add('<p><strong>' + ('ا' * 1400) + '</strong></p>')

        self.assertTrue(Service.objects.filter(title='لمینت').exists())

    def test_prose_past_the_cap_is_still_rejected(self):
        self._add('<p>' + ('ا' * 1600) + '</p>')

        self.assertFalse(Service.objects.filter(title='لمینت').exists())

    def test_the_meta_description_carries_no_markup(self):
        """Google prints this string; a `<strong>` in it is printed too."""
        service = Service.objects.create(
            title='ونیر', description='<p>' + DESCRIPTION + '</p>', image=tiny_jpeg(),
        )

        self.assertNotIn('<', service.seo_description)


class RemoveServiceTemplateTests(TestCase):
    """
    ``RemoveServiceView`` named a template that did not exist, so a GET on the
    delete URL answered TemplateDoesNotExist rather than a confirmation page.
    """

    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )

    def setUp(self):
        cache.clear()
        self.service = Service.objects.create(
            title='ایمپلنت', description=DESCRIPTION, image=tiny_jpeg(),
        )

    def test_the_confirmation_page_renders(self):
        self.client.login(username='doc', password=PASSWORD)

        response = self.client.get(
            reverse('service:remove_service', kwargs={'pk': self.service.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ایمپلنت')
