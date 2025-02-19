from django.views import View
from django.shortcuts import render
from django.contrib import messages
from django.http import Http404
from core.models import Clinic
from service.models import Service
from dashboard.models import Doctor

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