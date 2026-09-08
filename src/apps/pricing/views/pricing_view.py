"""Public tariff list, grouped by category, with a response cache."""
from django.core.cache import cache
from django.shortcuts import render
from django.views import View

from utils.http.cache import get_cache_key
from utils.http.mixins import RateLimitMixin

from ..models import PricingCategory, PricingItem


def _grouped_pricing_items():
    """
    Return a list of ``{'category': PricingCategory | None, 'items': [...]}``
    ordered by category ``order``. Items without a category land in a final
    "بدون دسته" group so nothing goes missing from the UI.
    """
    categories = list(PricingCategory.objects.prefetch_related('items').all())
    groups = []
    for category in categories:
        items = list(category.items.all().order_by('title'))
        if items:
            groups.append({'category': category, 'items': items})

    uncategorised = list(PricingItem.objects.filter(category__isnull=True).order_by('title'))
    if uncategorised:
        groups.append({'category': None, 'items': uncategorised})

    return groups


class PricingListView(RateLimitMixin, View):
    """Public pricing list, grouped by category, with a response-level cache.

    Cache is bypassed for authenticated users because the rendered HTML
    embeds user-scoped navbar controls (management pills, logout button).
    Serving a shared cached response would hide them from staff.
    """
    template_name = 'pricing/pricing_list.html'

    def get(self, request, *args, **kwargs):
        def render_page():
            return render(request, self.template_name, {
                'pricing_groups': _grouped_pricing_items(),
                'pricing_categories': PricingCategory.objects.all(),
            })

        if request.user.is_authenticated:
            return render_page()

        # No vary_on: the pricing page reads nothing from the query string.
        cache_key = get_cache_key(
            request, cache_view='pricinglistview', group='pricing', public=True,
        )
        cached_response = cache.get(cache_key)
        if cached_response:
            return cached_response

        response = render_page()
        cache.set(cache_key, response, 3600)
        return response


