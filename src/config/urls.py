from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView

from apps.core.sitemaps import SITEMAPS
from apps.core.views.robots_view import RobotsTxtView
from apps.notifications.views.push_view import service_worker, web_app_manifest
from utils.security.math_captcha import refresh_challenge, render_challenge_image

urlpatterns = [
    # Admin interface
    path(settings.SECURE_ADMIN_PANEL, admin.site.urls),

    # Home page and related routes
    path('', include('apps.home.urls')),
    
    # Blog-related routes
    path('blog/', include('apps.blog.urls')),
    
    # About page
    path('about/', include('apps.about.urls')),
    
    # Service page and details
    path('service/', include('apps.service.urls')),
    
    # Core functionality of the site
    path('core/', include('apps.core.urls')),
    
    # Gallery pages
    path('gallery/', include('apps.gallery.urls')),
    
    # Contact form and information
    path('contact/', include('apps.contact.urls')),
    
    # Dashboard (likely for admin or user-specific content)
    path('dashboard/', include('apps.dashboard.urls')),
    
    # Authentication (login, logout, register, etc.)
    path('auth/', include('apps.accounts.urls')),
    
    # Pricing and tariffs
    path('pricing/', include('apps.pricing.urls')),

    # Online appointment booking
    path('appointments/', include('apps.appointments.urls')),

    # Public CV page per doctor. Kept at the root rather than under
    # /dashboard/ because a patient searching a doctor's name should land on
    # a short, readable URL — and because /dashboard/ is disallowed to
    # crawlers, which would take these pages with it.
    path('doctors/', include('apps.doctors.urls')),

    # Staff SMS tools + delivery logs
    path('notifications/', include('apps.notifications.urls')),

    # CKEditor 5 URL
    path('ckeditor_5/', include('django_ckeditor_5.urls')),

    # Push service worker. Root path on purpose: a worker's scope cannot
    # reach above the directory it is served from, so one under /static/ could
    # never receive a push for the site.
    path('sw.js', service_worker, name='service_worker'),

    # Web app manifest, also at the root: its `scope` defaults to the serving
    # directory, and an installed app scoped to /static/ would fall out of
    # standalone mode on the first real navigation. iOS additionally refuses
    # Web Push unless the site was installed as a standalone web app.
    path('manifest.webmanifest', web_app_manifest, name='web_app_manifest'),

    # Precached by the service worker at install time and shown only when a
    # navigation fails with no network. A real URL rather than an inline
    # string so it inherits the site's own styling.
    path('offline/', TemplateView.as_view(template_name='offline.html'), name='offline'),

    # Session-backed math captcha image endpoint + refresh (JSON, POST-only)
    path('math-captcha/<str:token>/image.png', render_challenge_image, name='math_captcha_image'),
    path('math-captcha/refresh/', refresh_challenge, name='math_captcha_refresh'),

    # Crawl surface. Both must be at the root — a crawler looks for
    # /robots.txt and nowhere else, and a sitemap may only declare URLs at or
    # below its own directory.
    #
    # Cached for a day: the file is rebuilt from four querysets and is
    # requested by bots that would otherwise run them on every visit. Editing
    # a page does not need to show up here within the hour.
    path('sitemap.xml', cache_page(86400)(sitemap), {'sitemaps': SITEMAPS},
         name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', RobotsTxtView.as_view(), name='robots_txt'),
]

# Serve static and media files during development
if settings.DEBUG:
    import debug_toolbar
    from django.views.generic import TemplateView
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
        # Preview error pages while DEBUG is on (Django hides them otherwise).
        path('_preview/404/', TemplateView.as_view(template_name='404.html'), name='_preview_404'),
        path('_preview/403/', TemplateView.as_view(template_name='403.html'), name='_preview_403'),
        path('_preview/500/', TemplateView.as_view(template_name='500.html'), name='_preview_500'),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
