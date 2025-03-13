from utils.common_imports import render, View
from core.models import Clinic  
from service.models import Service  
from dashboard.models import Doctor  

class AboutView(View):
    template_name = 'about/about.html'

    def get(self, request, *args, **kwargs):

        clinic = Clinic.objects.filter(is_primary=True).first()
        doctors = Doctor.objects.select_related('user').all()
        services = Service.objects.all()[:5]
        context = {
            'clinic': clinic,
            'doctors': doctors,
            'services': services,
        }

        return render(request, self.template_name, context)