from utils.common_imports import View, render, redirect, get_object_or_404, messages, cache
from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin
from .models import ContactMessage  
from core.models import WorkingHours
from core.models import Clinic  
from .forms import ContactMessageForm 
from utils.cache import get_cache_key 

class ContactView(RateLimitMixin, View):
    """View to handle contact form submissions and display contact information."""
    template_name = 'contact/contact.html'
    form_class = ContactMessageForm

    def get(self, request, *args, **kwargs):
        
        # cache data and queries
        cache_key = get_cache_key(request, cache_view='contactview_data')
        cached_data = cache.get(cache_key)

        if cached_data is None:
            cached_data = {
                'clinic': Clinic.objects.filter(is_primary=True).first(),
                'workinghours': WorkingHours.objects.all(),
            }
            cache.set(cache_key, cached_data, 86400)

        form = self.form_class()
        context = {
            'clinic': cached_data['clinic'],
            'workinghours': cached_data['workinghours'],
            'form': form, 
        }

        return render(request, self.template_name, context)    
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        context = {
            'clinic': Clinic.objects.filter(is_primary=True).first(),
            'workinghours': WorkingHours.objects.all(),
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
