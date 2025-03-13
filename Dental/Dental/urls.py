"""
URL configuration for the Dental project.

This module routes URL paths to their corresponding views in the Dental project.
It includes the default Django admin interface, and URL configurations for various apps,
such as home, blog, about, service, core, gallery, contact, dashboard, and accounts (authentication).

For more information on URL routing, see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/

Examples:

Function-based views:
    1. Import: from my_app import views
    2. URL pattern: path('', views.home, name='home')

Class-based views:
    1. Import: from other_app.views import Home
    2. URL pattern: path('', Home.as_view(), name='home')

Including another URL configuration:
    1. Import include: from django.urls import include, path
    2. URL pattern: path('blog/', include('blog.urls'))
"""
from utils.common_imports import admin, path, include, settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
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
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)