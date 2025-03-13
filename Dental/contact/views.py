# Project-specific imports from common_imports
from utils.common_imports import View, render, redirect, get_object_or_404, messages  
from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

# Imports from local models
from .models import WorkingHours, ContactMessage  

# Imports from other apps in the project
from core.models import Clinic  

# Imports from local forms
from .forms import WorkingHoursForm, ContactMessageForm  

class ContactView(RateLimitMixin, View):
    template_name = 'contact/contact.html'
    form_class = ContactMessageForm

    def dispatch(self, request, *args, **kwargs):
        self.clinic = Clinic.objects.filter(is_primary=True).first()
        self.workinghours = WorkingHours.objects.all()
        return super().dispatch(request, *args, **kwargs)

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
        # else:
        #     messages.error(request, 'لطفاً اطلاعات را به درستی وارد کنید')
        return render(request, self.template_name, context)
    
class ContactMessagesView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    template_name = 'contact/contact_messages.html'
        
    def get(self, request, *args, **kwargs):
        filter_status = request.GET.get('filter', 'all')  
        messages_list = ContactMessage.objects.all()

        # فیلتر پیام‌ها بر اساس وضعیت خوانده‌شده
        if filter_status == 'read':
            messages_list = messages_list.filter(is_read=True)
        elif filter_status == 'unread':
            messages_list = messages_list.filter(is_read=False)
        context = {'messages_list': messages_list, 'filter_status': filter_status}
        return render(request, self.template_name, context)

class MarkAsReadView(DoctorOrSuperuserRequiredMixin, View):
    
    def post(self, request, *args, **kwargs):
        message = get_object_or_404(ContactMessage, id=kwargs['pk'])
        message.is_read = True
        message.save(update_fields=['is_read'])
        return redirect('contact:messages')
    
class MarkAllAsReadView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """علامت‌گذاری همه پیام‌های خوانده‌نشده به عنوان خوانده‌شده"""

    def post(self, request, *args, **kwargs):
        updated = ContactMessage.objects.filter(is_read=False).update(is_read=True)
        messages.success(request, f"پیام با موفقیت علامت‌گذاری شدند {updated}")
        return redirect('contact:messages')

class DetailWorkingHoursView(DoctorOrSuperuserRequiredMixin, View):
    template_name = 'contact/detail_working_hours.html'
        
    def get(self, request, *args, **kwargs):
        working_hours = get_object_or_404(WorkingHours, id=kwargs['pk'])
        context = {'working_hours': working_hours}
        return render(request, self.template_name, context)

class AddWorkingHoursView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
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
        # else:
        #     messages.error(request, 'خطایی پیش آمده لطفا اطلاعات را بررسی کنید')
        return render(request, self.template_name, {'form': form})
        
class UpdateWorkingHoursView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    template_name = 'contact/update_working_hours.html'
    form_class = WorkingHoursForm

    def dispatch(self, request, *args, **kwargs):
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
        # else:
        #     messages.error(request, 'مشکلی در بروزرسانی ساعات کاری رخ داد لطفا اطلاعات را درست وارد کنید.')
        return render(request, self.template_name, context)
    
class DeleteWorkingHoursView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    template_name = 'contact/delete_working_hours.html'

    def dispatch(self, request, *args, **kwargs):
        self.working_hours = get_object_or_404(WorkingHours, id=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {'working_hours': self.working_hours,}
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        self.working_hours.delete()
        messages.success(request, "ساعات کاری با موفقیت حذف شد")
        return redirect('core:manage')