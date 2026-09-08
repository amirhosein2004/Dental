import jdatetime
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.dashboard.models import Doctor
from utils.data.validators import validate_national_code, validate_phone

from .weeks import (
    WEEKDAY_LABELS,
    WEEKDAYS,
    current_week_start,
    slot_date,
    slot_datetime,
)


class AvailabilitySlot(models.Model):
    """
    One recurring opening in a doctor's weekly template — "Saturday, 20:00".

    Deliberately *not* tied to a calendar date. The same row is bookable again
    every week, which is what makes the schedule reset on its own: bookings
    carry the week they belong to (see :class:`Appointment`), so when the week
    turns over the slot is free again with no cleanup job involved.
    """
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='availability_slots',
        verbose_name="پزشک",
    )
    # Which practice this opening is at.
    #
    # The practice has two locations in different cities, and the board used to
    # say only "Saturday 20:00 — Dr X": a patient in Quchan could book a slot
    # in Mashhad without ever being told, and the front desk could not tell
    # which city a booking belonged to either.
    #
    # SET_NULL rather than CASCADE: deleting a branch is an edit to the
    # clinic's own details, and it must not silently take a week of bookings
    # with it. A slot with no branch still works — it renders as
    # "مطب مشخص نشده" — which is also what every pre-existing row becomes.
    branch = models.ForeignKey(
        'about.Branch',
        on_delete=models.SET_NULL,
        related_name='availability_slots',
        null=True,
        blank=True,
        verbose_name="مطب",
        help_text="مطبی که این نوبت در آن انجام می‌شود",
    )
    weekday = models.PositiveSmallIntegerField(
        choices=WEEKDAYS,
        verbose_name="روز هفته",
    )
    time = models.TimeField(verbose_name="ساعت")
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
        help_text="غیرفعال کردن، نوبت‌های ثبت‌شده را حذف نمی‌کند",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['weekday', 'time']
        verbose_name = "زمان نوبت‌دهی"
        verbose_name_plural = "زمان‌های نوبت‌دهی"
        constraints = [
            # A doctor cannot be in two places at once; this also stops the
            # obvious double-entry when staff add the same opening twice.
            models.UniqueConstraint(
                fields=['doctor', 'weekday', 'time'],
                name='unique_doctor_weekday_time',
            ),
        ]

    def __str__(self):
        return (
            f'{self.doctor} — {self.branch_label} — '
            f'{self.get_weekday_display()} ساعت {self.time:%H:%M}'
        )

    @property
    def weekday_label(self):
        return WEEKDAY_LABELS.get(self.weekday, '')

    @property
    def branch_label(self):
        """Never empty: rows predating the branch field must still read sensibly."""
        return self.branch.display_title if self.branch else 'مطب مشخص نشده'

    def booking_for(self, week_start=None):
        """The active booking occupying this slot in the given week, or None."""
        week_start = week_start or current_week_start()
        return self.appointments.filter(
            week_start=week_start, status=Appointment.Status.BOOKED
        ).first()

    def has_passed(self, week_start=None, now=None):
        """
        True when this week's occurrence is already in the past.

        Without it, a visitor could still "book" Saturday 09:00 on Sunday.
        """
        week_start = week_start or current_week_start()
        now = now or timezone.localtime().replace(tzinfo=None)
        return slot_datetime(week_start, self.weekday, self.time) <= now


class Appointment(models.Model):
    """
    A patient's claim on one :class:`AvailabilitySlot` for one specific week.

    `week_start` is the Saturday opening that week. Combined with the unique
    constraint below it produces the whole "resets every week" behaviour: two
    people cannot hold the same slot in the same week, and next week is a
    different `week_start`, so the slot is open again.
    """

    class Status(models.TextChoices):
        BOOKED = 'booked', 'رزرو شده'
        CANCELLED = 'cancelled', 'لغو شده'

    slot = models.ForeignKey(
        AvailabilitySlot,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name="زمان نوبت",
    )
    week_start = models.DateField(
        verbose_name="شروع هفته",
        help_text="شنبه‌ی هفته‌ای که این نوبت به آن تعلق دارد",
    )

    full_name = models.CharField(max_length=120, verbose_name="نام و نام خانوادگی")
    national_code = models.CharField(
        max_length=10,
        validators=[validate_national_code],
        verbose_name="کد ملی",
    )
    phone = models.CharField(
        max_length=11,
        validators=[validate_phone],
        verbose_name="شماره تماس",
    )
    note = models.TextField(blank=True, default='', verbose_name="توضیحات")

    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.BOOKED,
        verbose_name="وضعیت",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-week_start', 'slot__weekday', 'slot__time']
        verbose_name = "نوبت"
        verbose_name_plural = "نوبت‌ها"
        constraints = [
            # The real double-booking guard. Two visitors submitting the same
            # slot at the same moment both pass a "is it free?" read, so the
            # database has to be the arbiter — the loser gets IntegrityError,
            # which the view turns into a friendly message. Scoped to `booked`
            # so a cancelled row does not block re-booking the slot.
            models.UniqueConstraint(
                fields=['slot', 'week_start'],
                condition=models.Q(status='booked'),
                name='unique_active_booking_per_slot_week',
            ),
        ]
        indexes = [
            models.Index(fields=['week_start', 'status']),
        ]

    def __str__(self):
        return f'{self.full_name} — {self.slot}'

    def clean(self):
        super().clean()
        # Bookings are only ever for the live week; a stale form or a crafted
        # POST must not reserve a past or future week.
        if self.week_start and self.week_start != current_week_start():
            raise ValidationError({'week_start': 'فقط برای هفته‌ی جاری می‌توان نوبت گرفت'})

    @property
    def appointment_date(self):
        return slot_date(self.week_start, self.slot.weekday)

    @property
    def jalali_date(self):
        return jdatetime.date.fromgregorian(date=self.appointment_date).strftime('%Y/%m/%d')
