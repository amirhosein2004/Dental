"""
What the treatment pages say about the practices.

The detail page ended its introduction with "ارائه در مشهد و قوچان" — true of
every treatment on the site, so it distinguished nothing, and it named cities
without an address or a number so there was nothing to act on. It now carries
each practice with its own address, numbers and hours.
"""
import io

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage

from apps.about.models import Branch
from apps.service.models import Service

DESCRIPTION = 'توضیح آزمایشی برای این خدمت که به اندازه کافی طولانی است.'


def tiny_jpeg(name='x.jpg'):
    buf = io.BytesIO()
    PILImage.new('RGB', (10, 10), (10, 120, 110)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


class TreatmentBranchTests(TestCase):
    def setUp(self):
        cache.clear()
        self.service = Service.objects.create(
            title='ایمپلنت', description=DESCRIPTION, image=tiny_jpeg(),
        )
        Branch.objects.create(
            city='مشهد', address='بلوار وکیل‌آباد', phone='05138000000',
            hours='شنبه تا چهارشنبه: ۹ تا ۱۳', order=1,
        )
        Branch.objects.create(
            city='قوچان', address='خیابان گوهرشاد', phone='05147247247',
            hours='شنبه تا چهارشنبه: ۱۶ تا ۲۰', order=2,
        )
        self.html = self.client.get(self.service.get_absolute_url()).content.decode()

    def test_both_practices_are_on_the_treatment_page(self):
        self.assertIn('بلوار وکیل‌آباد', self.html)
        self.assertIn('خیابان گوهرشاد', self.html)
        self.assertIn('tel:05138000000', self.html)
        self.assertIn('tel:05147247247', self.html)

    def test_each_practice_carries_its_own_hours(self):
        self.assertIn('شنبه تا چهارشنبه: ۹ تا ۱۳', self.html)
        self.assertIn('شنبه تا چهارشنبه: ۱۶ تا ۲۰', self.html)

    def test_the_cities_are_no_longer_announced_as_a_bare_line(self):
        self.assertNotIn('ارائه در', self.html)


class TreatmentCatalogueTests(TestCase):
    """
    The catalogue lists treatments, not people.

    It grew a "who performs these" band of doctor cards, which is the same
    section the home page already carries — two copies of the team, and on
    the page whose job is the treatment list it pushed the treatments up
    the page for no new information.
    """

    def setUp(self):
        cache.clear()

    def test_the_team_band_is_not_repeated_here(self):
        html = self.client.get(reverse('service:service_list')).content.decode()

        self.assertNotIn('svc-team', html)
