from utils.common_imports import render, View , cache
from core.models import Clinic  
from service.models import Service  
from dashboard.models import Doctor  
from utils.cache import get_cache_key

class AboutView(View):
    """View for displaying the 'About' page, showing clinic, doctors, and services."""

    template_name = 'about/about.html'  

    def get(self, request, *args, **kwargs):
        
        # cache data and queries
        cache_key = get_cache_key(request, cache_view='aboutview_data')
        cached_data = cache.get(cache_key)

        if cached_data is None:
            cached_data = {
                'clinic': Clinic.objects.filter(is_primary=True).first(),
                'doctors': Doctor.objects.select_related('user').all(),
                'services': Service.objects.all()[:4],
            }    
            cache.set(cache_key, cached_data, 86400)

        context = {    # If the cache key exists, the cached_data was previously stored under that key and is now being retrieved from it.
            'clinic': cached_data['clinic'],
            'doctors': cached_data['doctors'],
            'services': cached_data['services'],
        }
        
        return render(request, self.template_name, context)


