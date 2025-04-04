from utils.common_imports import View, render, cache
from dashboard.models import Doctor
from service.models import Service
from core.models import Clinic, Banner
from blog.models import BlogPost
from gallery.models import Gallery
from utils.cache import get_cache_key


class HomeView(View):

    template_name = 'home/home.html'

    def get(self, request, *args, **kwargs):
        cache_key = get_cache_key(request, cache_view='homeview')
        cached_data = cache.get(cache_key)  # بررسی کش قبل از اجرای کوئری‌ها
        if cached_data:
            return cached_data
        
        banners = Banner.objects.all()[:5]
        doctors = Doctor.objects.select_related('user').all()
        services = Service.objects.all()[:2]
        clinic = Clinic.objects.filter(is_primary=True).first()
        blogs  = BlogPost.objects.prefetch_related('categories').all()[:3]
        galleries = Gallery.objects.prefetch_related('images').all()[:2]
        context = {
            'banners': banners,
            'doctors': doctors,
            'services': services,
            'clinic': clinic,
            'blogs': blogs,
            'galleries': galleries
        }
        
        response = render(request, self.template_name, context)
        cache.set(cache_key, response, 86400)  # ذخیره کش برای 24 ساعت
        return response

