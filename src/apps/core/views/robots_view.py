"""
robots.txt.

Served by a view rather than a static file for one reason: the sitemap line
has to carry an absolute URL, and the host is different on develop and
production. A static file would hardcode one of the three, and the two hosts
it got wrong would advertise a sitemap that does not exist.
"""
from django.http import HttpResponse
from django.views import View


# Everything that requires a login, plus the endpoints that exist to be called
# by JavaScript rather than visited. Crawling these wastes the site's crawl
# budget on pages that would only ever return a redirect to the login form.
DISALLOWED = (
    '/dashboard/',
    '/auth/',
    '/notifications/',
    '/core/manage/',
    '/core/category/',
    '/math-captcha/',
    '/ckeditor_5/',
    '/service/add/',
    '/service/update/',
    '/service/remove/',
    '/blog/create/',
    '/blog/update/',
    '/blog/delete/',
    '/contact/messages/',
    '/appointments/manage/',
    '/appointments/list/',
    '/about/edit/',
    '/about/hours/',
    '/pricing/add/',
    '/pricing/update/',
    '/offline/',
)


class RobotsTxtView(View):
    """
    Plain-text crawl rules for every user agent.

    Note what this file is *not*: it does not keep a page out of the search
    results. A URL disallowed here can still be indexed from an external link,
    just without its content — which is why every private template also
    carries a `noindex` meta tag. `Disallow` saves crawl budget; `noindex`
    controls indexing. They are separate mechanisms and this project uses
    both.
    """

    def get(self, request, *args, **kwargs):
        lines = ['User-agent: *']
        lines += [f'Disallow: {path}' for path in DISALLOWED]

        # The admin lives at a secret path, and it is deliberately absent
        # from both this file and the sitemap. Naming it here — even to
        # disallow it — would publish it to anyone who reads robots.txt, which
        # is the first file an attacker fetches. Not even a comment: the
        # comment would be the giveaway.
        lines.append('')
        lines.append(f'Sitemap: {request.build_absolute_uri("/sitemap.xml")}')
        lines.append('')

        return HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')
