"""The public "about us" page."""
from django.core.cache import cache
from django.shortcuts import render
from django.views import View

from apps.dashboard.models import Doctor
from apps.service.models import Service
from utils.http.cache import get_cache_key

from ..models import About


class AboutView(View):
    """Public 'About Us' page — clinic profile + doctors + service preview."""

    template_name = 'about/about.html'

    def get(self, request, *args, **kwargs):
        # No vary_on: the about page reads nothing from the query string.
        cache_key = get_cache_key(
            request, cache_view='aboutview_data', group='about', public=True,
        )
        cached_data = cache.get(cache_key)

        if cached_data is None:
            cached_data = {
                'about': About.objects.first(),
                'doctors': Doctor.objects.select_related('user').all(),
                'services': Service.objects.all()[:4],
            }
            cache.set(cache_key, cached_data, 86400)

        return render(request, self.template_name, cached_data)

