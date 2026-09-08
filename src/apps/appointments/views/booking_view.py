"""Public: the weekly board, and booking one slot on it."""
import logging

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.dashboard.models import Doctor
from apps.notifications.models import NotificationLog
from apps.notifications.tasks import notify_staff_task
from utils.http.mixins import RateLimitMixin

from ..forms import AppointmentForm
from ..models import AvailabilitySlot
from ..weeks import current_week_start, slot_date
from .common import _branch_boards, _week_board

logger = logging.getLogger(__name__)


class AppointmentBoardView(View):
    """Public weekly board — what is open right now."""
    template_name = 'appointments/board.html'

    def get(self, request, *args, **kwargs):
        week_start = current_week_start()
        boards = _branch_boards(week_start)
        return render(request, self.template_name, {
            # Grouped by practice — a visitor has to know which city a slot is
            # in before they book it, not after.
            'branch_boards': boards,
            # Kept so a template (or a caller) that wants the ungrouped week
            # still has it; the board page itself renders `branch_boards`.
            'board': _week_board(week_start),
            'week_start': week_start,
            'doctors': Doctor.objects.select_related('user').all(),
        })


class BookAppointmentView(RateLimitMixin, View):
    """
    Public booking form for one slot.

    Rate-limited: the form collects a national code and a phone number, so an
    unthrottled endpoint would be a convenient way to spam the schedule.
    """
    template_name = 'appointments/book.html'
    form_class = AppointmentForm
    rate_limit = '6/m'

    def dispatch(self, request, *args, **kwargs):
        self.slot = get_object_or_404(
            AvailabilitySlot.objects.select_related('doctor__user', 'branch'),
            pk=kwargs['pk'], is_active=True,
        )
        self.week_start = current_week_start()
        return super().dispatch(request, *args, **kwargs)

    def _blocked_reason(self):
        if self.slot.has_passed(self.week_start):
            return 'زمان این نوبت در هفته‌ی جاری گذشته است'
        if self.slot.booking_for(self.week_start):
            return 'این نوبت قبلاً رزرو شده است'
        return None

    def _context(self, form):
        return {
            'form': form,
            'slot': self.slot,
            'slot_date': slot_date(self.week_start, self.slot.weekday),
            'week_start': self.week_start,
        }

    def get(self, request, *args, **kwargs):
        reason = self._blocked_reason()
        if reason:
            messages.error(request, reason)
            return redirect('appointments:board')
        return render(request, self.template_name, self._context(self.form_class()))

    def post(self, request, *args, **kwargs):
        reason = self._blocked_reason()
        if reason:
            messages.error(request, reason)
            return redirect('appointments:board')

        form = self.form_class(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._context(form))

        appointment = form.save(commit=False)
        appointment.slot = self.slot
        appointment.week_start = self.week_start

        try:
            # The check above is advisory: between it and this write another
            # visitor may have taken the slot. The unique constraint is the
            # real arbiter, so handle its failure rather than trusting the read.
            with transaction.atomic():
                appointment.save()
        except IntegrityError:
            messages.error(request, 'متأسفانه همین لحظه این نوبت توسط فرد دیگری رزرو شد')
            return redirect('appointments:board')

        self._notify(appointment)
        messages.success(
            request,
            f'نوبت شما در {self.slot.branch_label} برای {self.slot.weekday_label}'
            f' ساعت {self.slot.time:%H:%M} ثبت شد',
        )
        return redirect('appointments:board')

    def _notify(self, appointment):
        """
        Tell the clinic which slot just filled.

        Queued, and queueing failures are swallowed: the booking is already
        committed and must not appear to fail because the broker is down.
        """
        text = (
            'نوبت جدید\n'
            f'{appointment.full_name} — {appointment.phone}\n'
            f'{appointment.slot.weekday_label} {appointment.jalali_date}'
            f' ساعت {appointment.slot.time:%H:%M}\n'
            f'پزشک: {appointment.slot.doctor}\n'
            f'مطب: {appointment.slot.branch_label}'
        )
        try:
            notify_staff_task.delay(text, NotificationLog.Kind.APPOINTMENT)
        except Exception:
            logger.exception('Failed to queue appointment alert')


