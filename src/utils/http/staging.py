"""
Staging-only response middleware.

Staging is reachable from the internet — testers need to open it from their
phones — which means a crawler can reach it too. Two things follow from that,
and both are handled here rather than in a template: a template change only
covers pages that extend the base, while a response header covers every
response including JSON, images and error pages.
"""


class NoIndexMiddleware:
    """
    Tell every crawler to ignore this host, on every response.

    `X-Robots-Tag` rather than a meta tag: the header applies to responses that
    have no HTML to put a tag in, and it cannot be missed by a page that
    forgot to extend the base template. Without it, staging competes with the
    live site in search results and leaks whatever draft content is on it.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
        return response
