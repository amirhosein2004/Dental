from utils.common_imports import View, render, redirect, messages, get_object_or_404
from core.forms import ClinicForm
from core.models import Clinic
from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

class DetailClinicView(DoctorOrSuperuserRequiredMixin, View):
    """
    View to display the details of a specific clinic.
    """
    template_name = 'core/detail_clinic.html'
              
    def get(self, request, *args, **kwargs):
        clinic = get_object_or_404(Clinic, pk=kwargs['pk'])
        context = {'clinic': clinic}
        return render(request, self.template_name, context)

class AddClinicView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle the addition of a new clinic.
    """
    template_name = 'core/add_clinic.html'
    form_class = ClinicForm
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {'form': form}
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        context = {'form': form}
        if form.is_valid():
            form.save()
            messages.success(request, 'کلینیک با موفقیت اضافه شد')
            return redirect('core:manage')
        
        return render(request, self.template_name, context)

class UpdateClinicView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle the update of an existing clinic.
    """
    template_name = 'core/update_clinic.html'
    form_class = ClinicForm

    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to get the clinic object before handling the request.
        """
        self.clinic = get_object_or_404(Clinic, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs) 
        
    def get(self, request, *args, **kwargs):
        form = self.form_class(instance=self.clinic)
        context = {
            'form': form,
            'clinic': self.clinic,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES, instance=self.clinic)
        context = {
            'form': form,
            'clinic': self.clinic,
        }
        if form.is_valid():
            form.save()
            messages.success(request, 'کلینیک با موفقیت بروز رسانی شد')
            return redirect('core:manage')

        return render(request, self.template_name, context)

class DeleteClinicView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle the deletion of an existing clinic.
    """
    template_name = 'core/delete_clinic.html'
        
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to get the clinic object before handling the request.
        """
        self.clinic = get_object_or_404(Clinic, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {'clinic': self.clinic,}
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        self.clinic.delete()
        messages.success(request, 'کلینیک با موفقیت حذف شد')
        return redirect('core:manage')