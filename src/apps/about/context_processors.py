from django.core.cache import cache

from .models import About, Branch


_CACHE_KEY = 'about_info_v2'
_CACHE_TTL = 60 * 60 * 6  # 6h; invalidated by about.signals on writes


def about_info(request):
    """
    Expose the About singleton + every Branch to all templates so footer /
    contact / about consumers render address, phone, email and opening hours
    without a per-view query.

    `branches` is here rather than in a per-view context because the footer
    lists both practices on every page of the site. Two locations in the
    footer sitewide is deliberate: consistent name/address/phone repeated on
    every page is what ties the website to each Business Profile listing, and
    a visitor who lands on a blog post should not have to navigate to find out
    which cities the practice is in.
    """
    data = cache.get(_CACHE_KEY)
    if data is None:
        branches = list(Branch.objects.all())
        data = {
            'about': About.objects.first(),
            'branches': branches,
            # Whatever needs exactly one branch — the single call button in
            # the shared CTA block, the `og:` tags — takes the first by
            # display order, so staff pick it by reordering rather than by a
            # separate "main practice" flag that no visitor ever sees.
            # `Branch.get_primary` re-queries; the list is already loaded here.
            'primary_branch': branches[0] if branches else None,
        }
        cache.set(_CACHE_KEY, data, _CACHE_TTL)
    return data


def invalidate_about_info_cache():
    cache.delete(_CACHE_KEY)
