from django.views import View
from django.shortcuts import render
from django.contrib import messages
from django.http import Http404
from about.models import Clinic, Doctor, Service
from contact.models import WorkingHours

class AboutView(View):
    template_name = 'about/about.html'

    def get(self, request, *args, **kwargs):
        clinic = Clinic.objects.first()
        doctors = Doctor.objects.all()
        services = Service.objects.all()
        context = {
            'clinic': clinic,
            'doctors': doctors,
            'services': services,
        }
        return render(request, self.template_name, context)
    
class EditAboutView(View):
    template_name = 'about/edit_about.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")

    def get(self, request, *args, **kwargs):
        clinics = Clinic.objects.all()
        doctors = Doctor.objects.all()
        services = Service.objects.all()
        working_hours = WorkingHours.objects.all()
        context = {
            'clinics': clinics,
            'doctors': doctors,
            'services': services,
            'working_hours': working_hours
        }
        return render(request, self.template_name, context)