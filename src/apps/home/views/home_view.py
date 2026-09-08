from django.core.cache import cache
from django.shortcuts import render
from django.views import View

from apps.about.models import About
from apps.blog.models import BlogPost
from apps.dashboard.models import Doctor
from apps.gallery.models import Gallery
from apps.service.models import Service
from utils.http.cache import get_cache_key


class HomeView(View):

    template_name = 'home/home.html'

    # Preview rows per teaser section. Kept uniform at 3 so the blog, gallery
    # and service strips read as one rhythm; the grids are all
    # `auto-fill minmax(300px, 1fr)`, so 3 lays out cleanly.
    PREVIEW_SIZE = 3

    def get(self, request, *args, **kwargs):

        # cache data and queries
        # No vary_on: the home page reads nothing from the query string.
        cache_key = get_cache_key(
            request, cache_view='homeview_data', group='home', public=True,
        )
        cached_data = cache.get(cache_key)

        if cached_data is None:
            limit = self.PREVIEW_SIZE
            cached_data = {
                'doctors': Doctor.objects.select_related('user').all(),
                'services': Service.objects.all()[:limit],
                'about': About.objects.first(),
                'blogs': BlogPost.objects.prefetch_related('categories').all()[:limit],
                'galleries': (
                    Gallery.objects
                    .select_related('category', 'doctor__user')
                    .prefetch_related('images')[:limit]
                ),
            }
            cache.set(cache_key, cached_data, 86400)

        return render(request, self.template_name, cached_data)

