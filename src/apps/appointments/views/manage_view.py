"""Clinic side: the recurring slot template, and this week's bookings."""
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from utils.http.mixins import (
    DoctorOrSuperuserRequiredMixin,
    RateLimitMixin,
    get_doctor_profile,
    user_owns,
)

from ..forms import AvailabilitySlotForm
from ..models import Appointment, AvailabilitySlot
from ..weeks import current_week_start
from .common import _booked_slot_ids


class SlotManageView(DoctorOrSuperuserRequiredMixin, RateLimitMixin, View):
    """
    Staff-side schedule editor.

    A doctor sees and edits only their own template; a superuser sees every
    doctor's — the same rule :func:`utils.http.mixins.user_owns` applies elsewhere.
    """
    template_name = 'appointments/manage.html'
    form_class = AvailabilitySlotForm

    def _own_doctor(self, request):
        """None for a superuser, meaning "all doctors"."""
        if request.user.is_superuser:
            return None
        doctor = get_doctor_profile(request.user)
        if doctor is None:
            raise Http404('پروفایل پزشک یافت نشد')
        return doctor

    def _context(self, request, form=None):
        doctor = self._own_doctor(request)
        slots = AvailabilitySlot.objects.select_related('doctor__user', 'branch')
        if doctor is not None:
            slots = slots.filter(doctor=doctor)

        week_start = current_week_start()
        return {
            'form': form if form is not None else self.form_class(doctor=doctor),
            'slots': slots,
            'taken_slot_ids': _booked_slot_ids(week_start),
            'week_start': week_start,
            'is_superuser': request.user.is_superuser,
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self._context(request))

    def post(self, request, *args, **kwargs):
        doctor = self._own_doctor(request)
        form = self.form_class(request.POST, doctor=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, 'زمان نوبت‌دهی اضافه شد')
            return redirect('appointments:manage')
        return render(request, self.template_name, self._context(request, form))


class SlotDeleteView(DoctorOrSuperuserRequiredMixin, RateLimitMixin, View):
    """Remove a recurring opening."""

    def post(self, request, *args, **kwargs):
        slot = get_object_or_404(AvailabilitySlot, pk=kwargs['pk'])
        if not user_owns(request.user, slot.doctor):
            raise Http404('صفحه مورد نظر یافت نشد')
        slot.delete()
        messages.success(request, 'زمان نوبت‌دهی حذف شد')
        return redirect('appointments:manage')


class AppointmentListView(DoctorOrSuperuserRequiredMixin, View):
    """This week's bookings, for the front desk."""
    template_name = 'appointments/list.html'

    def get(self, request, *args, **kwargs):
        week_start = current_week_start()
        bookings = (
            Appointment.objects
            .filter(week_start=week_start, status=Appointment.Status.BOOKED)
            .select_related('slot__doctor__user', 'slot__branch')
        )
        if not request.user.is_superuser:
            doctor = get_doctor_profile(request.user)
            if doctor is None:
                raise Http404('پروفایل پزشک یافت نشد')
            bookings = bookings.filter(slot__doctor=doctor)

        return render(request, self.template_name, {
            'bookings': bookings,
            'week_start': week_start,
        })


class AppointmentCancelView(DoctorOrSuperuserRequiredMixin, RateLimitMixin, View):
    """
    Free a slot back up.

    Marks the row cancelled rather than deleting it: the partial unique
    constraint only covers `booked`, so the slot reopens immediately while the
    record of who had taken it survives.
    """

    def post(self, request, *args, **kwargs):
        booking = get_object_or_404(
            Appointment.objects.select_related('slot__doctor'), pk=kwargs['pk'],
        )
        if not user_owns(request.user, booking.slot.doctor):
            raise Http404('صفحه مورد نظر یافت نشد')

        booking.status = Appointment.Status.CANCELLED
        booking.save(update_fields=['status'])
        messages.success(request, 'نوبت لغو شد و زمان آن آزاد گردید')
        return redirect('appointments:list')
