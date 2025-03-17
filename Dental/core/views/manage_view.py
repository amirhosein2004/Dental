from utils.common_imports import View, render, method_decorator, cache_page
from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin
from core.models import Category, Clinic  
from dashboard.models import Doctor  
from service.models import Service  
from contact.models import WorkingHours, ContactMessage  
from utils.cache import get_cache_key


class ManageView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    ManageView handles the display of various management-related data for the dental clinic.
    It ensures that only doctors or superusers can access this view and applies rate limiting.
    """
    template_name = 'core/manage.html'
         
    @method_decorator(lambda func: cache_page(28800, key_prefix=lambda request: get_cache_key(request, cache_view='manageview'))(func))  # Cache for 8 hours
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to the manage view.
        
        Retrieves all instances of Clinic, Doctor, Service, WorkingHours, Category, and ContactMessage
        and passes them to the template for rendering.
        
        Args:
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        
        Returns:
            HttpResponse: The rendered template with the context data.
        """
        # Retrieve all clinics
        clinics = Clinic.objects.all()
        # Retrieve all doctors
        doctors = Doctor.objects.all()
        # Retrieve all services
        services = Service.objects.all()
        # Retrieve all working hours
        working_hours = WorkingHours.objects.all()
        # Retrieve all categories
        categories = Category.objects.all()
        # Retrieve all contact messages
        messages_list = ContactMessage.objects.all()
        
        context = {
            'clinics': clinics,
            'doctors': doctors,
            'services': services,
            'working_hours': working_hours, 
            'categories': categories,
            'messages_list': messages_list
        }
        
        return render(request, self.template_name, context)
