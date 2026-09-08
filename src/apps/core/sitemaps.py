"""
Sitemaps.

A sitemap does not improve ranking on its own — the claim that it does is one
of the more durable myths about it. What it does is make discovery
deterministic. Without one, a crawler finds a page only by following a link to
it, so anything reachable in one place (a service linked from a single card
grid, a doctor linked from one hub page) waits on that one link being
crawled. With one, every URL is declared up front along with when it last
changed, and a re-crawl after an edit takes days instead of weeks.

`lastmod` is the part worth getting right: a sitemap that reports today's date
for every URL on every request teaches the crawler to ignore the field, which
costs exactly the benefit the file was added for. Every entry below reports
the row's own `updated_at`.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.blog.models import BlogPost
from apps.dashboard.models import Doctor
from apps.service.models import Service


class StaticViewSitemap(Sitemap):
    """
    The pages that are not rows in a table.

    Deliberately excludes everything behind a login — the dashboard, the
    appointment board's staff views, the auth flow. Those also carry a
    `noindex` tag; the two are complementary. A sitemap entry is a request to
    crawl, a `noindex` is an instruction not to *index*, and a page that
    should not be indexed should not be requested for crawling either.
    """
    protocol = 'https'
    changefreq = 'weekly'

    def items(self):
        return [
            ('home:home', 1.0),
            ('service:service_list', 0.9),
            ('doctors:doctor_list', 0.9),
            ('about:about', 0.7),
            ('pricing:pricing_list', 0.8),
            ('gallery:gallery_list', 0.6),
            ('blog:blog_list', 0.7),
            ('contact:contact', 0.7),
            ('appointments:board', 0.8),
        ]

    def location(self, item):
        return reverse(item[0])

    def priority(self, item):
        return item[1]


class ServiceSitemap(Sitemap):
    protocol = 'https'
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        return Service.objects.all()

    def lastmod(self, obj):
        return obj.updated_at


class DoctorSitemap(Sitemap):
    """
    The profile pages — the highest-priority rows on the site, because a
    search for a doctor's own name is the query this site is most able to win
    and currently most likely to lose to a directory listing.
    """
    protocol = 'https'
    changefreq = 'monthly'
    priority = 0.9

    def items(self):
        return Doctor.objects.filter(is_published=True, user__is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class BlogSitemap(Sitemap):
    protocol = 'https'
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return BlogPost.objects.all()

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {
    'static': StaticViewSitemap,
    'services': ServiceSitemap,
    'doctors': DoctorSitemap,
    'blog': BlogSitemap,
}
