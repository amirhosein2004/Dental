"""
Pricing: the public tariff list, and the staff screens for items and the
categories they group into.

The grouping is the interesting part. Items whose category is deleted must not
disappear from the page — a tariff nobody can see is a tariff nobody charges.
"""
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from apps.pricing.models import PricingCategory, PricingItem
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'


class PublicListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.implants = PricingCategory.objects.create(name='ایمپلنت', order=1)
        cls.ortho = PricingCategory.objects.create(name='ارتودنسی', order=2)
        PricingItem.objects.create(category=cls.implants, title='ایمپلنت کره‌ای', price=25_000_000)
        PricingItem.objects.create(category=cls.ortho, title='ارتودنسی ثابت', price=40_000_000)

    def setUp(self):
        cache.clear()

    def test_the_list_renders_when_empty(self):
        PricingItem.objects.all().delete()
        PricingCategory.objects.all().delete()

        response = self.client.get(reverse('pricing:pricing_list'))
        self.assertEqual(response.status_code, 200)

    def test_items_are_grouped_by_category(self):
        response = self.client.get(reverse('pricing:pricing_list'))
        groups = response.context['pricing_groups']

        names = [g['category'].name for g in groups if g['category']]
        self.assertEqual(names, ['ایمپلنت', 'ارتودنسی'], 'groups are not in `order`')

    def test_an_uncategorised_item_still_appears(self):
        """
        The FK is nullable. An item with no category has to land in a group of
        its own rather than vanishing from the page.
        """
        PricingItem.objects.create(category=None, title='کشیدن دندان', price=1_500_000)

        response = self.client.get(reverse('pricing:pricing_list'))
        titles = [
            item.title for group in response.context['pricing_groups']
            for item in group['items']
        ]
        self.assertIn('کشیدن دندان', titles)

    def test_deleting_a_category_keeps_its_items_visible(self):
        self.ortho.delete()

        response = self.client.get(reverse('pricing:pricing_list'))
        titles = [
            item.title for group in response.context['pricing_groups']
            for item in group['items']
        ]
        self.assertIn('ارتودنسی ثابت', titles, 'an item was lost with its category')

    def test_a_new_item_is_not_hidden_by_the_cache(self):
        self.client.get(reverse('pricing:pricing_list'))      # warm

        PricingItem.objects.create(category=self.implants, title='ایمپلنت سوئیسی', price=55_000_000)

        self.assertContains(self.client.get(reverse('pricing:pricing_list')), 'ایمپلنت سوئیسی')


class StaffAccessTests(TestCase):
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
        self.category = PricingCategory.objects.create(name='ایمپلنت', order=1)
        self.item = PricingItem.objects.create(
            category=self.category, title='ایمپلنت کره‌ای', price=25_000_000,
        )

    def _staff_urls(self):
        return [
            reverse('pricing:add_pricing_item'),
            reverse('pricing:update_pricing_item', kwargs={'pk': self.item.pk}),
            reverse('pricing:delete_pricing_item', kwargs={'pk': self.item.pk}),
            reverse('pricing:pricing_category_list'),
            reverse('pricing:add_pricing_category'),
            reverse('pricing:update_pricing_category', kwargs={'pk': self.category.pk}),
            reverse('pricing:delete_pricing_category', kwargs={'pk': self.category.pk}),
        ]

    def test_anonymous_gets_404_on_every_staff_screen(self):
        for url in self._staff_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_a_signed_in_patient_also_gets_404(self):
        self.client.login(username='patient', password=PASSWORD)
        for url in self._staff_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_a_doctor_can_add_a_tariff(self):
        self.client.login(username='doc', password=PASSWORD)
        self.client.post(reverse('pricing:add_pricing_item'), {
            'category': self.category.pk, 'title': 'لمینت سرامیکی', 'price': '12000000',
        })

        self.assertTrue(PricingItem.objects.filter(title='لمینت سرامیکی').exists())

    def test_a_doctor_can_delete_a_tariff(self):
        self.client.login(username='doc', password=PASSWORD)
        self.client.post(reverse('pricing:delete_pricing_item', kwargs={'pk': self.item.pk}))

        self.assertFalse(PricingItem.objects.filter(pk=self.item.pk).exists())

    def test_a_visitor_cannot_delete_a_tariff(self):
        self.client.post(reverse('pricing:delete_pricing_item', kwargs={'pk': self.item.pk}))

        self.assertTrue(PricingItem.objects.filter(pk=self.item.pk).exists())

    def test_a_visitor_cannot_delete_a_category(self):
        self.client.post(
            reverse('pricing:delete_pricing_category', kwargs={'pk': self.category.pk}),
        )

        self.assertTrue(PricingCategory.objects.filter(pk=self.category.pk).exists())


class PriceValidationTests(TestCase):
    """A tariff is money. Nonsense in this field ends up on a printed invoice."""

    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )
        cls.category = PricingCategory.objects.create(name='ایمپلنت', order=1)

    def setUp(self):
        cache.clear()
        self.client.login(username='doc', password=PASSWORD)

    def test_a_negative_price_is_refused(self):
        self.client.post(reverse('pricing:add_pricing_item'), {
            'category': self.category.pk, 'title': 'منفی', 'price': '-5000',
        })

        self.assertFalse(PricingItem.objects.filter(title='منفی').exists())

    def test_a_non_numeric_price_is_refused(self):
        self.client.post(reverse('pricing:add_pricing_item'), {
            'category': self.category.pk, 'title': 'حروف', 'price': 'رایگان',
        })

        self.assertFalse(PricingItem.objects.filter(title='حروف').exists())

    def test_a_duplicate_category_name_is_refused(self):
        self.client.post(reverse('pricing:add_pricing_category'), {
            'name': 'ایمپلنت', 'order': '5',
        })

        self.assertEqual(PricingCategory.objects.filter(name='ایمپلنت').count(), 1)
