from utils.common_imports import admin, path, include, settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin interface
    path(settings.SECURE_ADMIN_PANEL, admin.site.urls),

    # Home page and related routes
    path('', include('home.urls')),
    
    # Blog-related routes
    path('blog/', include('blog.urls')),
    
    # About page
    path('about/', include('about.urls')),
    
    # Service page and details
    path('service/', include('service.urls')),
    
    # Core functionality of the site
    path('core/', include('core.urls')),
    
    # Gallery pages
    path('gallery/', include('gallery.urls')),
    
    # Contact form and information
    path('contact/', include('contact.urls')),
    
    # Dashboard (likely for admin or user-specific content)
    path('dashboard/', include('dashboard.urls')),
    
    # Authentication (login, logout, register, etc.)
    path('auth/', include('accounts.urls')),

    # CKEditor 5 URL
    path('ckeditor_5/', include('django_ckeditor_5.urls')),
]

# Serve static and media files during development
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)