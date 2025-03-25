from utils.common_imports import View, render, redirect, get_object_or_404, messages, method_decorator, cache_page
from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

from .models import WorkingHours, ContactMessage  
from core.models import Clinic  
from .forms import WorkingHoursForm, ContactMessageForm 
from utils.cache import get_cache_key 

class ContactView(RateLimitMixin, View):
    """View to handle contact form submissions and display contact information."""
    template_name = 'contact/contact.html'
    form_class = ContactMessageForm

    def dispatch(self, request, *args, **kwargs):
        """Fetch clinic and working hours before handling the request."""
        self.clinic = Clinic.objects.filter(is_primary=True).first()
        self.workinghours = WorkingHours.objects.all()
        return super().dispatch(request, *args, **kwargs)

    @method_decorator(lambda func: cache_page(86400, key_prefix=lambda request: get_cache_key(request, cache_view='contactview'))(func))  # Cache for 24 hours
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {
            'clinic': self.clinic,
            'workinghours': self.workinghours,
            'form': form, 
        }
        return render(request, self.template_name, context)    
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        context = {
            'clinic': self.clinic,
            'workinghours': self.workinghours,
            'form': form,
        }
        if form.is_valid():
            form.save()
            messages.success(request, 'پیام شما با موفقیت ارسال شد')
            return redirect('contact:contact')

        return render(request, self.template_name, context)
    
class ContactMessagesView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """View to display contact messages with filtering options."""
    template_name = 'contact/contact_messages.html'
        
    def get(self, request, *args, **kwargs):
        filter_status = request.GET.get('filter', 'all')  
        messages_list = ContactMessage.objects.all()

        # Filter messages based on read status
        if filter_status == 'read':
            messages_list = messages_list.filter(is_read=True)
        elif filter_status == 'unread':
            messages_list = messages_list.filter(is_read=False)
        context = {'messages_list': messages_list, 'filter_status': filter_status}
        return render(request, self.template_name, context)

class MarkAsReadView(DoctorOrSuperuserRequiredMixin, View):
    """View to mark a specific contact message as read."""
    
    def post(self, request, *args, **kwargs):
        message = get_object_or_404(ContactMessage, id=kwargs['pk'])
        message.is_read = True
        message.save(update_fields=['is_read'])
        return redirect('contact:messages')
    
class MarkAllAsReadView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """View to mark all unread contact messages as read."""

    def post(self, request, *args, **kwargs):
        updated = ContactMessage.objects.filter(is_read=False).update(is_read=True)
        messages.success(request, f"پیام با موفقیت علامت‌گذاری شدند {updated}")
        return redirect('contact:messages')

class DetailWorkingHoursView(DoctorOrSuperuserRequiredMixin, View):
    """View to display details of specific working hours."""
    template_name = 'contact/detail_working_hours.html'
    
    def get(self, request, *args, **kwargs):
        working_hours = get_object_or_404(WorkingHours, id=kwargs['pk'])
        context = {'working_hours': working_hours}
        return render(request, self.template_name, context)

class AddWorkingHoursView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """View to add new working hours."""
    template_name = 'contact/add_working_hours.html'
    form_class = WorkingHoursForm
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'ساعت کاری با موفقیت اضافه شد')
            return redirect('core:manage')

        return render(request, self.template_name, {'form': form})
        
class UpdateWorkingHoursView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """View to update existing working hours."""
    template_name = 'contact/update_working_hours.html'
    form_class = WorkingHoursForm

    def dispatch(self, request, *args, **kwargs):
        """Fetch the working hours object before handling the request."""
        self.working_hours = get_object_or_404(WorkingHours, id=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
        
    def get(self, request, *args, **kwargs):
        form = self.form_class(instance=self.working_hours)
        context = {
            'form': form,
            'working_hours': self.working_hours
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, instance=self.working_hours)
        context = {
            'form': form,
            'working_hours': self.working_hours
        }
        if form.is_valid():
            form.save()
            messages.success(request, ' ساعات کاری با موفقیت بروز شد')
            return redirect('core:manage')

        return render(request, self.template_name, context)
    
class DeleteWorkingHoursView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """View to delete existing working hours."""
    template_name = 'contact/delete_working_hours.html'

    def dispatch(self, request, *args, **kwargs):
        """Fetch the working hours object before handling the request."""
        self.working_hours = get_object_or_404(WorkingHours, id=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {'working_hours': self.working_hours,}
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        self.working_hours.delete()
        messages.success(request, "ساعات کاری با موفقیت حذف شد")
        return redirect('core:manage')