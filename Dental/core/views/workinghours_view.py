from utils.common_imports import View, render, redirect, get_object_or_404, messages
from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

from core.models import WorkingHours
from core.forms import WorkingHoursForm 


class WorkingHoursView(DoctorOrSuperuserRequiredMixin, View):
    """
    View to display a list of all workinghours.
    """
    template_name = 'core/workinghours.html'
    
    def get(self, request, *args, **kwargs):
        workinghours = WorkingHours.objects.all()
        context = {'workinghours': workinghours}
        return render(request, self.template_name, context)

class AddWorkingHoursView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """View to add new working hours."""
    template_name = 'core/add_working_hours.html'
    form_class = WorkingHoursForm
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'ساعت کاری با موفقیت اضافه شد')
            return redirect('core:workinghours')

        return render(request, self.template_name, {'form': form})
        
class UpdateWorkingHoursView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """View to update existing working hours."""
    template_name = 'core/workinghours.html'
    form_class = WorkingHoursForm

    def dispatch(self, request, *args, **kwargs):
        """Fetch the working hours object before handling the request."""
        self.working_hours = get_object_or_404(WorkingHours, id=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
        
    def get(self, request, *args, **kwargs):
        form = self.form_class(instance=self.working_hours)
        workinghours = WorkingHours.objects.all()
        context = {
            'form': form,
            'edit_workinghour_id': self.working_hours.pk,
            'workinghours': workinghours
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, instance=self.working_hours)
        workinghours = WorkingHours.objects.all()
        context = {
            'form': form,
            'edit_workinghour_id': self.working_hours.pk,
            'workinghours': workinghours
        }
        if form.is_valid():
            form.save()
            messages.success(request, ' ساعات کاری با موفقیت بروز شد')
            return redirect('core:workinghours')

        return render(request, self.template_name, context)
    
class DeleteWorkingHoursView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """View to delete existing working hours."""
    
    def post(self, request, *args, **kwargs):
        get_object_or_404(WorkingHours, id=kwargs['pk']).delete()
        messages.success(request, "ساعات کاری با موفقیت حذف شد")
        return redirect('core:workinghours')