"""
Values every page's ``<head>`` needs.

These are cheap to compute and needed by the base template on every response,
so they are context processors rather than something each view has to
remember to add — a view that forgot would emit a page with no canonical URL,
and the omission is invisible until a duplicate shows up in search results
months later.
"""
from django.conf import settings
from django.core.cache import cache

_SERVICES_CACHE_KEY = 'ld_services_v1'
_SERVICES_TTL = 60 * 60 * 6  # 6h; invalidated by core.signals on Service writes


def _ld_services():
    """
    Titles and URLs of every treatment, for the `availableService` list in the
    site-wide JSON-LD. Cached because the block renders on every page and the
    list changes a few times a year.
    """
    services = cache.get(_SERVICES_CACHE_KEY)
    if services is None:
        from apps.service.models import Service

        services = list(Service.objects.only('title', 'slug'))
        cache.set(_SERVICES_CACHE_KEY, services, _SERVICES_TTL)
    return services


def invalidate_ld_services_cache():
    cache.delete(_SERVICES_CACHE_KEY)


def seo(request):
    """
    Canonical URL, site name and site origin.

    ``canonical_url`` is built from ``request.path`` rather than
    ``build_absolute_uri()`` with no argument, which would include the query
    string. That difference is the entire point: ``/blog/``,
    ``/blog/?page=1`` and ``/blog/?utm_source=instagram`` are one page to a
    reader and three pages to a crawler, and the ranking that page earned
    would be divided between them. Pointing all three at one address collapses
    them back into one.

    A page that genuinely is a separate address — page 2 of a list, a filtered
    view worth indexing on its own — overrides the ``canonical`` block in the
    base template instead.
    """
    return {
        'canonical_url': request.build_absolute_uri(request.path),
        'SITE_NAME': settings.SITE_NAME,
        'SITE_URL': settings.SITE_URL,
        'ld_services': _ld_services(),
    }
