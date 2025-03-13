# Project-specific imports from common_imports
from utils.common_imports import View, render  
from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin
# Imports from local models
from core.models import Category, Clinic  
from dashboard.models import Doctor  
from service.models import Service  
from contact.models import WorkingHours, ContactMessage  



class ManageView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    template_name = 'core/manage.html'
         
    def get(self, request, *args, **kwargs):
        clinics = Clinic.objects.all()
        doctors = Doctor.objects.all()
        services = Service.objects.all()
        working_hours = WorkingHours.objects.all()
        categories = Category.objects.all()
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
