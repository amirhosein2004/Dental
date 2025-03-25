from utils.common_imports import View, render, redirect, messages, get_object_or_404
from core.forms import ClinicForm
from core.models import Clinic
from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

class ClinicView(DoctorOrSuperuserRequiredMixin, View):
    """
    View to display a list of all clinics.
    """
    template_name = 'core/clinic.html'
    
    def get(self, request, *args, **kwargs):
        clinics = Clinic.objects.all()
        context = {'clinics': clinics}
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
            return redirect('core:clinic')
        
        return render(request, self.template_name, context)

class UpdateClinicView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle the update of an existing clinic.
    """
    template_name = 'core/clinic.html'
    form_class = ClinicForm

    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to get the clinic object before handling the request.
        """
        self.clinic = get_object_or_404(Clinic, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs) 
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display the clinic list.
        """
        clinics = Clinic.objects.all()
        context = {'clinics': clinics, 'edit_clinic_id': self.clinic.id}  # edit_clinic_id is for display errors in form update 
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES, instance=self.clinic)
        clinics = Clinic.objects.all()   # برای نشان دادن کلینیک ها نیاز است وگرنه خالی میبینیم
        context = {
            'form': form,
            'clinics': clinics,
            'edit_clinic_id': self.clinic.pk  # مشخص کردن کلینیک در حال ویرایش
        }
        if form.is_valid():
            form.save()
            messages.success(request, 'کلینیک با موفقیت بروز رسانی شد')
            return redirect('core:clinic')

        return render(request, self.template_name, context)

class DeleteClinicView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle the deletion of an existing clinic.
    """
    template_name = 'core/delete_clinic.html'
    
    def post(self, request, *args, **kwargs):
        get_object_or_404(Clinic, pk=kwargs['pk']).delete()
        messages.success(request, 'کلینیک با موفقیت حذف شد')
        return redirect('core:manage')