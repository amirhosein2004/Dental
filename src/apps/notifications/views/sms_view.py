from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from utils.http.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

from ..forms import BulkSmsForm, ContactGroupForm
from ..models import ContactGroup, NotificationLog
from ..tasks import send_bulk_sms_task


class BulkSmsView(DoctorOrSuperuserRequiredMixin, RateLimitMixin, View):
    """
    Paste numbers, write a message, send.

    Rate-limited hard: each submit can cost real money, and an accidental
    double-click should not send the batch twice.
    """
    template_name = 'notifications/bulk_sms.html'
    form_class = BulkSmsForm
    rate_limit = '5/m'

    def _context(self, form=None):
        return {
            'form': form if form is not None else self.form_class(),
            'recent': NotificationLog.objects.all()[:15],
            'groups': ContactGroup.objects.all(),
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self._context())

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._context(form))

        numbers = form.cleaned_data['parsed_numbers']
        invalid = form.cleaned_data['invalid_tokens']

        send_bulk_sms_task.delay(
            numbers, form.cleaned_data['message'], request.user.pk,
        )

        messages.success(request, f'ارسال به {len(numbers)} شماره در صف قرار گرفت')
        if invalid:
            # Surfaced rather than silently dropped: a mistyped number is the
            # operator's to fix, and they can only fix what they can see.
            preview = '، '.join(invalid[:5])
            more = f' و {len(invalid) - 5} مورد دیگر' if len(invalid) > 5 else ''
            messages.warning(
                request,
                f'{len(invalid)} شماره نامعتبر نادیده گرفته شد: {preview}{more}',
            )

        return redirect('notifications:bulk_sms')


class NotificationLogView(DoctorOrSuperuserRequiredMixin, View):
    """Delivery history — the answer to "did that message actually go out?"."""
    template_name = 'notifications/logs.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'logs': NotificationLog.objects.all()[:100],
        })


class ContactGroupListView(DoctorOrSuperuserRequiredMixin, RateLimitMixin, View):
    """Saved recipient lists, plus the create form."""
    template_name = 'notifications/groups.html'
    form_class = ContactGroupForm

    def _context(self, form=None):
        return {
            'form': form if form is not None else self.form_class(),
            'groups': ContactGroup.objects.all(),
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self._context())

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._context(form))

        group = form.save(commit=False)
        group.created_by = request.user
        group.save()

        messages.success(request, f'گروه «{group.name}» با {group.member_count} شماره ساخته شد')
        self._warn_invalid(request, form)
        return redirect('notifications:groups')

    @staticmethod
    def _warn_invalid(request, form):
        invalid = getattr(form, 'invalid_tokens', None)
        if not invalid:
            return
        preview = '، '.join(invalid[:5])
        more = f' و {len(invalid) - 5} مورد دیگر' if len(invalid) > 5 else ''
        messages.warning(
            request, f'{len(invalid)} مورد نامعتبر نادیده گرفته شد: {preview}{more}',
        )


class ContactGroupEditView(DoctorOrSuperuserRequiredMixin, RateLimitMixin, View):
    """Edit one saved list."""
    template_name = 'notifications/group_edit.html'
    form_class = ContactGroupForm

    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(ContactGroup, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'form': self.form_class(instance=self.group),
            'group': self.group,
        })

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, instance=self.group)
        if not form.is_valid():
            return render(request, self.template_name, {
                'form': form, 'group': self.group,
            })

        group = form.save()
        messages.success(request, f'گروه «{group.name}» به‌روزرسانی شد')
        ContactGroupListView._warn_invalid(request, form)
        return redirect('notifications:groups')


class ContactGroupDeleteView(DoctorOrSuperuserRequiredMixin, RateLimitMixin, View):
    def post(self, request, *args, **kwargs):
        group = get_object_or_404(ContactGroup, pk=kwargs['pk'])
        name = group.name
        group.delete()
        messages.success(request, f'گروه «{name}» حذف شد')
        return redirect('notifications:groups')
