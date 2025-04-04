from utils.common_imports import render, View , cache
from core.models import Clinic  
from service.models import Service  
from dashboard.models import Doctor  
from utils.cache import get_cache_key

class AboutView(View):
    """View for displaying the 'About' page, showing clinic, doctors, and services."""

    template_name = 'about/about.html'  

    def get(self, request, *args, **kwargs):
        cache_key = get_cache_key(request, cache_view='aboutview')
        cached_data = cache.get(cache_key)  # بررسی کش قبل از اجرای کوئری‌ها
        if cached_data:
            return cached_data
        
        context = {
            'clinic': Clinic.objects.filter(is_primary=True).first(),
            'doctors': Doctor.objects.select_related('user').all(),
            'services': Service.objects.all()[:4],
        }
        
        response = render(request, self.template_name, context)
        cache.set(cache_key, response, 86400)  # ذخیره کش برای 24 ساعت
        return response

