from django.views import View
from django.shortcuts import render, redirect
from django.http import Http404
from django.contrib import messages
from core.models import Category, Clinic
from dashboard.models import Doctor
from service.models import Service
from contact.models import WorkingHours, ContactMessage


class ManageView(View):
    template_name = 'core/manage.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
    
    def get(self, request, *args, **kwargs):
        clinic = Clinic.objects.first()
        doctors = Doctor.objects.all()
        services = Service.objects.all()
        working_hours = WorkingHours.objects.all()
        categories = Category.objects.all()
        messages_list = ContactMessage.objects.all()
        context = {
            'clinic': clinic,
            'doctors': doctors,
            'services': services,
            'working_hours': working_hours, 
            'categories': categories,
            'messages_list': messages_list
        }
        return render(request, self.template_name, context)
