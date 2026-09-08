"""The staff inbox: filtering, marking read, and manual cleanup."""
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from utils.http.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

from ..models import ContactMessage
from ..tasks import delete_old_messages

CLEANUP_MIN_DAYS = 7
CLEANUP_MAX_DAYS = 3650


class ContactMessagesView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """View to display contact messages with filtering options."""
    template_name = 'contact/contact_messages.html'

    FILTER_QUERY_MAP = {
        'read': {'is_read': True},
        'unread': {'is_read': False},
    }

    def get(self, request, *args, **kwargs):
        filter_status = request.GET.get('filter', 'all')
        messages_list = ContactMessage.objects.all()
        if filter_status in self.FILTER_QUERY_MAP:
            messages_list = messages_list.filter(**self.FILTER_QUERY_MAP[filter_status])

        return render(request, self.template_name, {
            'messages_list': messages_list,
            'filter_status': filter_status,
            # Public half of the VAPID pair. Safe to embed — it is what the
            # browser signs its subscription against, and it is meaningless
            # without the private key that never leaves the server.
            'vapid_public_key': settings.VAPID_PUBLIC_KEY,
        })


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
        messages.success(request, f"{updated} پیام با موفقیت علامت‌گذاری شدند")
        return redirect('contact:messages')


class CleanupOldMessagesView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    Manually triggered cleanup: delete contact messages older than a chosen
    number of days. Runs asynchronously through Celery.
    """
    rate_limit = '3/m'

    def post(self, request, *args, **kwargs):
        raw_days = request.POST.get('days', '180')
        try:
            days = int(raw_days)
        except (TypeError, ValueError):
            messages.error(request, "تعداد روز معتبر نیست")
            return redirect('contact:messages')

        if not (CLEANUP_MIN_DAYS <= days <= CLEANUP_MAX_DAYS):
            messages.error(
                request,
                f"تعداد روز باید بین {CLEANUP_MIN_DAYS} و {CLEANUP_MAX_DAYS} باشد",
            )
            return redirect('contact:messages')

        delete_old_messages.delay(days)
        messages.success(
            request,
            f"درخواست حذف پیام‌های قدیمی‌تر از {days} روز ثبت شد و در پس‌زمینه اجرا می‌شود",
        )
        return redirect('contact:messages')
