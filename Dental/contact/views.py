from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import Http404
from .models import WorkingHours, ContactMessage
from core.models import Clinic
from .forms import WorkingHoursForm, ContactMessageForm

class ContactView(View):
    template_name = 'contact/contact.html'
    form_class = ContactMessageForm

    def get(self, request, *args, **kwargs):
        clinic = Clinic.objects.first()
        workinghours = WorkingHours.objects.all()
        form = self.form_class()
        contex = {
            'clinic': clinic,
            'workinghours': workinghours,
            'form': form, 
        }
        return render(request, self.template_name, contex)    
    
    def post(self, request, *args, **kwargs):
        clinic = Clinic.objects.first()
        workinghours = WorkingHours.objects.all()
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'پیام شما با موفقیت ارسال شد.')
            return redirect('contact:contact')
        else:
            messages.error(request, 'لطفاً اطلاعات را به درستی وارد کنید.')
        context = {
            'clinic': clinic,
            'workinghours': workinghours,
            'form': form,
        }
        return render(request, self.template_name, context)
    
class ContactMessagesView(View):
    template_name = 'contact/contact_messages.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
    
    def get(self, request, *args, **kwargs):
        filter_status = request.GET.get('filter', 'all')  
        messagesـlist = ContactMessage.objects.all().order_by('-created_at')

        # فیلتر پیام‌ها بر اساس وضعیت خوانده‌شده
        if filter_status == 'read':
            messagesـlist = messagesـlist.filter(is_read=True)
        elif filter_status == 'unread':
            messagesـlist = messagesـlist.filter(is_read=False)

        return render(request, self.template_name, {'messagesـlist': messagesـlist, 'filter_status': filter_status})

class MarkAsReadView(View):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
    
    def get(self, request, *args, **kwargs):
        message = get_object_or_404(ContactMessage, id=kwargs['pk'])
        message.is_read = True
        message.save()
        return redirect('contact:messages')
    
class MarkAllAsReadView(View):
    """علامت‌گذاری همه پیام‌های خوانده‌نشده به عنوان خوانده‌شده"""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")

    def get(self, request, *args, **kwargs):
        ContactMessage.objects.filter(is_read=False).update(is_read=True)
        return redirect('contact:messages') 

class DetailWorkingHoursView(View):
    template_name = 'contact/detail_working_hours.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
        
    def get(self, request, *args, **kwargs):
        working_hours = WorkingHours.objects.get(pk=kwargs['pk'])
        context = {
            'working_hours': working_hours,
        }
        return render(request, self.template_name, context)

class AddWorkingHoursView(View):
    template_name = 'contact/add_working_hours.html'
    form_class = WorkingHoursForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {
            'form': form,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'ساعات کاری با موفقیت اضافه شد.')
            return redirect('core:manage')

        messages.error(request, 'روز را قبلا وارد کرد اید.')
        return render(request, self.template_name, {'form': form})
    
class UpdateWorkingHoursView(View):
    template_name = 'contact/update_working_hours.html'
    form_class = WorkingHoursForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
        
    def get(self, request, *args, **kwargs):
        working_hours = WorkingHours.objects.get(pk=kwargs['pk'])
        form = self.form_class(instance=working_hours)
        context = {
            'form': form,
            'working_hours': working_hours
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        working_hours = WorkingHours.objects.get(pk=kwargs['pk'])
        form = self.form_class(request.POST, instance=working_hours)
        if form.is_valid():
            form.save()
            messages.success(request, ' working hours updated successfully.')
            return redirect('core:manage')
        context = {
            'form': form,
            'working_hours': working_hours
        }
        return render(request, self.template_name, context)
    
class DeleteWorkingHoursView(View):
    template_name = 'contact/delete_working_hours.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")

    def get(self, request, *args, **kwargs):
        working_hours = WorkingHours.objects.get(pk=kwargs['pk'])
        context = {
            'working_hours': working_hours,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        working_hours = WorkingHours.objects.get(pk=kwargs['pk'])
        working_hours.delete()
        messages.success(request, 'working hours deleted successfully.')
        return redirect('core:manage')