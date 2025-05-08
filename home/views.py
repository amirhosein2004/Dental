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

        # cache data and queries
        cache_key = get_cache_key(request, cache_view='homeview_data')
        cached_data = cache.get(cache_key)

        if cached_data is None:
            cached_data = {
                'banners': Banner.objects.all()[:5],
                'doctors': Doctor.objects.select_related('user').all(),
                'services': Service.objects.all()[:2],
                'clinic': Clinic.objects.filter(is_primary=True).first(),
                'blogs': BlogPost.objects.prefetch_related('categories').all()[:3],
                'galleries': Gallery.objects.prefetch_related('images').all()[:2],
            }    
            cache.set(cache_key, cached_data, 86400)
        
        context = {
            'banners': cached_data['banners'],
            'doctors': cached_data['doctors'],
            'services': cached_data['services'],
            'clinic': cached_data['clinic'],
            'blogs': cached_data['blogs'],
            'galleries': cached_data['galleries']
        }
        
        return render(request, self.template_name, context)

