"""Public gallery: the masonry list and its "load more" endpoint."""
from django.core.cache import cache
from django.db.models import Count
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views import View

from utils.http.cache import get_cache_key
from utils.http.mixins import RateLimitMixin

from apps.core.models import Category
from apps.dashboard.models import Doctor
from django.shortcuts import render

from ..filters import GalleryFilter
from .common import (
    GALLERY_PAGE_SIZE,
    _galleries_queryset,
    _page,
    _with_masonry_spans,
)


class GalleryView(RateLimitMixin, View):
    """Public gallery list with filtering + response cache.

    Cache is bypassed for authenticated users because the rendered HTML
    embeds user-scoped navbar controls (management pills, per-tile admin
    buttons). Serving a shared cached response would hide them from staff.
    """
    template_name = 'gallery/gallery.html'

    def _render(self, request):
        gallery_filter = GalleryFilter(request.GET, queryset=_galleries_queryset())
        page, has_more = _page(gallery_filter.qs, 0, GALLERY_PAGE_SIZE)
        return render(request, self.template_name, {
            'galleries': _with_masonry_spans(page),
            # Headline stat: the whole (filtered) set, not just this page.
            # `galleries|length` used to be shown there, which under-reported
            # the collection as soon as paging existed.
            'total_galleries': (
                gallery_filter.qs
                .annotate(_image_count=Count('images'))
                .filter(_image_count__gt=0)
                .count()
            ),
            # `next_offset` counts every row consumed from the queryset, not the
            # tiles that survived the empty-gallery filter, otherwise paging
            # would re-request rows it already skipped.
            'next_offset': len(page),
            'has_more': has_more,
            'filter': gallery_filter,
            'categories': Category.objects.all(),
            'doctors': Doctor.objects.all(),
        })

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return self._render(request)

        cache_key = get_cache_key(
            request, cache_view='galleryview', group='gallery', public=True,
            vary_on=('category',),  # the only GalleryFilter field
        )
        cached_response = cache.get(cache_key)
        if cached_response:
            return cached_response

        response = self._render(request)
        cache.set(cache_key, response, 86400)
        return response


class LoadMoreGalleriesView(View):
    """
    AJAX endpoint for the "load more" button.

    Returns server-rendered tile HTML. The previous JSON contract made the
    browser rebuild the tile markup, which still emitted the pre-redesign
    Bootstrap layout and targeted a `.row.g-4` container that no longer exists
    — so the button appeared to do nothing. Sharing `_gallery_tile.html` keeps
    appended tiles identical to the first page, admin controls included.
    """

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return JsonResponse({'error': 'Invalid request'}, status=400)

        try:
            offset = max(int(request.GET.get('offset', 0)), 0)
        except (TypeError, ValueError):
            offset = 0

        gallery_filter = GalleryFilter(request.GET, queryset=_galleries_queryset())
        page, has_more = _page(gallery_filter.qs, offset, GALLERY_PAGE_SIZE)
        tiles = _with_masonry_spans(page, offset=offset)

        html = ''.join(
            render_to_string(
                'gallery/_gallery_tile.html',
                {'gallery': gallery, 'span': gallery.masonry_span},
                request=request,
            )
            for gallery in tiles
        )
        return JsonResponse({
            'html': html,
            # `consumed` advances the offset past skipped empty galleries so the
            # next click doesn't re-fetch them; `count` drives the "nothing new"
            # end state.
            'consumed': len(page),
            'count': len(tiles),
            'has_more': has_more,
        })


# Ceiling on files accepted in one upload. Django caps the size of an
# individual file but places no limit on how many arrive together, so a single
# multipart POST could hand the bucket thousands of images — each one paid for,
# and each one validated and written before anything noticed. Staff-only, but a
# mis-selected folder is a normal accident, not an attack.
