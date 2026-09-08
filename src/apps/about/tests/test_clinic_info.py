"""
Clinic contact details, and the site-wide promise that every page offers the
same three ways to reach the clinic.

The details themselves live on ``Branch``, one row per practice. ``About``
used to carry an address and a phone number of its own, which meant the site
could only describe one location while rendering it as if it described the
practice as a whole — so a visitor in Quchan read the Mashhad number.
"""
from io import BytesIO

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage

from apps.about.models import About, Branch


def tiny_jpeg(name='clinic.jpg'):
    buf = BytesIO()
    PILImage.new('RGB', (10, 10), (13, 148, 136)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


def make_about(**overrides):
    data = {
        'name': 'مطب دکتر بابایی و بهمدی',
        'email': 'info@sbdental.ir',
        'description': 'مطب تخصصی دندانپزشکی با بیش از ده سال سابقه در خدمت شما.',
        'image': tiny_jpeg(),
    }
    data.update(overrides)
    return About.objects.create(**data)


def make_branch(**overrides):
    data = {
        'city': 'قوچان',
        'address': 'قوچان، خیابان گوهرشاد',
        'phone': '05147247247',
    }
    data.update(overrides)
    return Branch.objects.create(**data)


class PhoneListTests(TestCase):
    def setUp(self):
        cache.clear()  # `about_info` is cached per-process

    def test_primary_only_when_no_extras(self):
        self.assertEqual(make_branch().phone_list, ['05147247247'])

    def test_extras_are_normalised_and_appended(self):
        branch = make_branch(extra_phones='09121234567, +989351112233\n۰۹۰۲۴۴۴۵۵۶۶')

        self.assertEqual(
            branch.phone_list,
            ['05147247247', '09121234567', '09351112233', '09024445566'],
        )

    def test_primary_is_never_duplicated_in_extras(self):
        """Staff will paste the main line into the extras box sooner or later."""
        branch = make_branch(extra_phones='05147247247, 09121234567')

        self.assertEqual(branch.phone_list, ['05147247247', '09121234567'])

    def test_duplicate_extras_are_collapsed(self):
        branch = make_branch(extra_phones='09121234567\n09121234567\n+989121234567')

        self.assertEqual(branch.phone_list, ['05147247247', '09121234567'])

    def test_invalid_extras_are_dropped(self):
        branch = make_branch(extra_phones='09121234567, badtoken, 123')

        self.assertEqual(branch.phone_list, ['05147247247', '09121234567'])

    def test_blank_extras_are_fine(self):
        self.assertEqual(make_branch(extra_phones='').extra_phone_list, [])


class HoursTests(TestCase):
    """
    Opening hours belong to a practice, not to the site.

    There was one shared free-text row for the whole clinic. Two practices in
    two cities do not keep the same hours, so whichever city it did not
    describe was being told the wrong thing — worse than being told nothing.
    """

    def setUp(self):
        cache.clear()

    def test_each_line_is_its_own_entry(self):
        branch = make_branch(hours='شنبه تا چهارشنبه: ۹ تا ۱۳\n\nجمعه: تعطیل')

        self.assertEqual(branch.hours_list, ['شنبه تا چهارشنبه: ۹ تا ۱۳', 'جمعه: تعطیل'])

    def test_a_practice_with_no_hours_reads_as_empty_not_broken(self):
        self.assertEqual(make_branch().hours_list, [])

    def test_each_practices_hours_reach_the_footer(self):
        make_about()
        make_branch(city='مشهد', hours='شنبه تا چهارشنبه: ۹ تا ۱۳')
        make_branch(city='قوچان', phone='05147247248', hours='شنبه تا چهارشنبه: ۱۶ تا ۲۰')

        html = self.client.get(reverse('home:home')).content.decode()

        self.assertIn('شنبه تا چهارشنبه: ۹ تا ۱۳', html)
        self.assertIn('شنبه تا چهارشنبه: ۱۶ تا ۲۰', html)


class ContactSurfaceTests(TestCase):
    """Numbers must actually reach the pages a visitor looks at."""

    def setUp(self):
        cache.clear()
        self.about = make_about()
        self.branch = make_branch(extra_phones='09121234567\n09351112233')

    def test_contact_page_lists_every_number(self):
        html = self.client.get(reverse('contact:contact')).content.decode()
        for number in self.branch.phone_list:
            with self.subTest(number=number):
                self.assertIn(f'tel:{number}', html)

    def test_footer_lists_every_number(self):
        html = self.client.get(reverse('home:home')).content.decode()
        for number in self.branch.phone_list:
            with self.subTest(number=number):
                self.assertIn(f'tel:{number}', html)


class CtaContactActionTests(TestCase):
    """
    The "get in touch" action in the shared CTA block.

    It printed one number — whichever practice sorted first — on nine pages,
    with nothing on the button saying where it rang, so a visitor in Quchan
    pressed it and reached Mashhad. Making it a dropdown of numbers only
    moved the problem: it asked the reader to choose a city from two strings
    of digits. It is now a link to the contact page, which names each
    practice with its address, hours, map and numbers.
    """

    def setUp(self):
        cache.clear()
        make_about()

    def test_the_cta_row_carries_no_phone_number(self):
        make_branch(city='مشهد', phone='05138000000', order=1)
        make_branch(city='قوچان', phone='05147247247', order=2)

        html = self.client.get(reverse('home:home')).content.decode()
        cta = html[html.index('cta-actions'):]

        self.assertNotIn('cta-call', html)
        self.assertNotIn('tel:', cta.split('</div>')[0])

    def test_every_page_still_offers_the_two_actions(self):
        make_branch()

        for name in ('home:home', 'about:about', 'service:service_list'):
            with self.subTest(page=name):
                html = self.client.get(reverse(name)).content.decode()
                self.assertIn(reverse('contact:contact'), html)
                self.assertIn(reverse('appointments:board'), html)

    def test_the_numbers_are_still_reachable_from_every_page(self):
        """
        The CTA stopped printing them, so the footer is now the only
        site-wide place carrying them — it has to keep doing it.
        """
        branch = make_branch(extra_phones='09121234567')

        html = self.client.get(reverse('home:home')).content.decode()

        for number in branch.phone_list:
            with self.subTest(number=number):
                self.assertIn(f'tel:{number}', html)

    def test_no_practices_leaves_both_actions_standing(self):
        html = self.client.get(reverse('home:home')).content.decode()

        self.assertIn(reverse('appointments:board'), html)
        self.assertIn(reverse('contact:contact'), html)


class CtaActionsTests(TestCase):
    """
    Every public page must offer the same three actions: call, book, message.

    Before this, each page ended with its own hand-written block — "رزرو نوبت"
    linked to the message form on some pages, the phone number was hard-coded
    on others, and no page offered all three.
    """

    PUBLIC_PAGES = [
        'home:home',
        'about:about',
        'service:service_list',
        'pricing:pricing_list',
        'gallery:gallery_list',
        'blog:blog_list',
    ]

    def setUp(self):
        cache.clear()
        self.about = make_about()
        self.branch = make_branch()

    def test_every_public_page_links_to_booking(self):
        booking = reverse('appointments:board')
        for name in self.PUBLIC_PAGES:
            with self.subTest(page=name):
                html = self.client.get(reverse(name)).content.decode()
                self.assertIn(booking, html)

    def test_every_public_page_offers_the_phone_and_message_route(self):
        contact = reverse('contact:contact')
        for name in self.PUBLIC_PAGES:
            with self.subTest(page=name):
                html = self.client.get(reverse(name)).content.decode()
                self.assertIn(f'tel:{self.branch.phone}', html)
                self.assertIn(contact, html)

    def test_no_hardcoded_phone_numbers_in_templates(self):
        """
        A number baked into a template silently goes stale the day the clinic
        changes lines, and there is nothing in the admin to fix it.
        """
        import re
        from pathlib import Path

        from django.conf import settings

        # Any Iranian-looking 11-digit literal inside a tel: link.
        pattern = re.compile(r'tel:0\d{10}')
        offenders = []
        for path in Path(settings.BASE_DIR).rglob('*.html'):
            if 'venv' in path.parts or 'site-packages' in path.parts:
                continue
            for lineno, line in enumerate(
                path.read_text(encoding='utf-8').splitlines(), start=1
            ):
                if pattern.search(line):
                    rel = path.relative_to(settings.BASE_DIR).as_posix()
                    offenders.append(f'{rel}:{lineno}')

        self.assertEqual(
            offenders, [],
            'Hard-coded phone number in a template — read it from the branch '
            'instead so staff can change it from the panel:\n  '
            + '\n  '.join(offenders),
        )
