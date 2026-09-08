"""Queryset and paging helpers shared by the public and authoring views."""
from ..models import BlogPost


BLOG_LIST_PAGE_SIZE = 3


def _blogs_queryset():
    return (
        BlogPost.objects
        .select_related('writer__user')
        .prefetch_related('categories')
    )


def _page(queryset, offset, size):
    """
    Slice one page and report whether anything follows it.

    Fetches one row past the page and trims it, instead of inferring
    ``has_more`` from a full page. With `count == size` the caller could not
    tell "exactly one page left" from "more to come", so a total that is an
    exact multiple of the page size produced one dead click that appended
    nothing before the button finally hid itself.
    """
    window = list(queryset[offset:offset + size + 1])
    return window[:size], len(window) > size


