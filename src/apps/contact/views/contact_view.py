"""The public contact form, and the alerts a submission fires."""
import logging

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from apps.notifications.models import NotificationLog
from apps.notifications.tasks import notify_staff_task, push_staff_task
from utils.http.mixins import RateLimitMixin

from ..forms import ContactMessageForm

logger = logging.getLogger(__name__)


class ContactView(RateLimitMixin, View):
    """View to handle contact form submissions and display contact information."""
    template_name = 'contact/contact.html'
    form_class = ContactMessageForm

    def _get_page_data(self, request):
        # `clinic` + `clinic_hours` are exposed globally via
        # core.context_processors.clinic_info, so this view only needs to
        # supply the form. The cache here is kept as a no-op for BC.
        return {}

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'form': self.form_class(request=request),
        })

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request=request)
        if form.is_valid():
            contact_message = form.save()
            self._notify(contact_message)
            messages.success(request, 'پیام شما با موفقیت ارسال شد')
            return redirect('contact:contact')
        return render(request, self.template_name, {'form': form})

    def _notify(self, contact_message):
        """
        Alert the clinic that someone wrote in.

        Queued so the visitor is not left waiting on an SMS panel, and any
        queueing failure is swallowed — the message is already saved, and
        losing the alert must not look to the visitor like a failed submit.
        """
        text = (
            'پیام جدید از سایت\n'
            f'{contact_message.name} — {contact_message.phone}\n'
            f'{contact_message.message[:120]}'
        )
        try:
            notify_staff_task.delay(text, NotificationLog.Kind.CONTACT_MESSAGE)
        except Exception:
            logger.exception('Failed to queue contact-message alert')

        # A browser notification as well as the SMS. They answer different
        # questions: the push is instant and free but only reaches a device
        # that is subscribed; the SMS costs money and arrives regardless.
        # Queued separately so one broker hiccup cannot swallow both, and
        # swallowed for the same reason as above — the message is saved, and
        # a failed alert must not look to the visitor like a failed submit.
        try:
            push_staff_task.delay(
                'پیام جدید از سایت',
                f'{contact_message.name} — {contact_message.message[:80]}',
                url='/contact/messages/',
                tag='contact-message',
            )
        except Exception:
            logger.exception('Failed to queue contact-message push')

