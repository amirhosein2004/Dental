"""Public blog: the cached list, its "load more" endpoint, and one article."""
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views import View

from utils.http.cache import get_cache_key

from ..filters import BlogPostFilter
from .common import BLOG_LIST_PAGE_SIZE, _blogs_queryset, _page


class BlogView(View):
    """Public blog list with filtering and a response-level cache.

    Cache is bypassed for authenticated users because the rendered HTML
    embeds user-scoped navbar controls; serving a shared cached response
    would hide the management pills from staff.
    """
    filter_class = BlogPostFilter
    template_name = 'blog/blog.html'

    def _render(self, request):
        blog_filter = self.filter_class(request.GET, queryset=_blogs_queryset().all())
        blogs, has_more = _page(blog_filter.qs, 0, BLOG_LIST_PAGE_SIZE)
        return render(request, self.template_name, {
            'blogs': blogs,
            'next_offset': len(blogs),
            'has_more': has_more,
            'filter': blog_filter,
        })

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return self._render(request)

        cache_key = get_cache_key(
            request, cache_view='blogview', group='blog', public=True,
            # The BlogPostFilter fields — anything else in the query string
            # does not change this response, so it must not fork the key.
            vary_on=('writer', 'category', 'title'),
        )
        cached_response = cache.get(cache_key)
        if cached_response:
            return cached_response

        response = self._render(request)
        cache.set(cache_key, response, 86400)
        return response


class LoadMoreBlogsView(View):
    """
    AJAX endpoint for the "load more" button.

    Returns server-rendered card HTML rather than raw JSON fields. The previous
    JSON contract forced the browser to re-implement the card markup, which
    silently drifted from `_blog_card.html` and rendered unstyled Bootstrap
    leftovers. Sharing the partial keeps the appended cards identical to the
    first page — including the per-user edit/delete controls.
    """
    filter_class = BlogPostFilter

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return JsonResponse({'error': 'Invalid request'}, status=400)

        try:
            offset = max(int(request.GET.get('offset', 0)), 0)
        except (TypeError, ValueError):
            offset = 0

        blog_filter = self.filter_class(request.GET, queryset=_blogs_queryset())
        more_blogs, has_more = _page(blog_filter.qs, offset, BLOG_LIST_PAGE_SIZE)

        html = ''.join(
            render_to_string(
                'blog/_blog_card.html',
                {'blog': blog, 'feature': False},
                request=request,
            )
            for blog in more_blogs
        )
        return JsonResponse({
            'html': html,
            'count': len(more_blogs),
            'has_more': has_more,
        })


class BlogDetailView(View):
    template_name = 'blog/blog_detail.html'

    def get(self, request, *args, **kwargs):
        blog = get_object_or_404(_blogs_queryset(), slug=kwargs['slug'])
        return render(request, self.template_name, {'blog': blog})


