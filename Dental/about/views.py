from utils.common_imports import render, View , cache_page, method_decorator
from core.models import Clinic  
from service.models import Service  
from dashboard.models import Doctor  
from utils.cache import get_cache_key

class AboutView(View):
    """View for displaying the 'About' page, showing clinic, doctors, and services."""

    template_name = 'about/about.html'  

    # method decorator for class-based views for caching
    @method_decorator(lambda func: cache_page(600, key_prefix=lambda request: get_cache_key(request, cache_view='aboutview'))(func))  
    def get(self, request, *args, **kwargs):
        context = {
            'clinic': Clinic.objects.filter(is_primary=True).first(),
            'doctors': Doctor.objects.select_related('user').all(),
            'services': Service.objects.all()[:4],
        }
        return render(request, self.template_name, context)

