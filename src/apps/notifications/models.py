from django.db import models

from .phones import parse_numbers


class ContactGroup(models.Model):
    """
    A named, reusable list of numbers — "بیماران ایمپلنت", "لیست تخفیف عید".

    Numbers live in one text column rather than a separate row per contact:
    the list is pasted and edited wholesale, never queried per-number, so a
    join table would add migrations and admin screens for no benefit. They are
    normalised and de-duplicated on save, which means every consumer can trust
    the stored value without re-parsing it.
    """
    name = models.CharField(max_length=120, unique=True, verbose_name="نام گروه")
    description = models.CharField(
        max_length=250, blank=True, default='', verbose_name="توضیح",
    )
    numbers = models.TextField(
        verbose_name="شماره‌ها",
        help_text="با فاصله، کاما یا خط جدید جدا کنید",
    )
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='contact_groups',
        verbose_name="ایجادکننده",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "گروه مخاطبان"
        verbose_name_plural = "گروه‌های مخاطبان"

    def __str__(self):
        return f'{self.name} ({self.member_count} شماره)'

    def save(self, *args, **kwargs):
        # Normalise here so the stored value is always canonical, whether it
        # arrived from the staff form, the admin, or a fixture.
        valid, _invalid = parse_numbers(self.numbers)
        self.numbers = '\n'.join(valid)
        super().save(*args, **kwargs)

    @property
    def number_list(self):
        return [line for line in self.numbers.splitlines() if line]

    @property
    def member_count(self):
        return len(self.number_list)


class NotificationLog(models.Model):
    """
    Audit trail for every outbound SMS batch.

    Exists so "the patient says the reminder never arrived" is answerable:
    without a record there is no way to tell a provider failure from a number
    that was never queued. Also the only place the real cost of a bulk run is
    visible after the fact.
    """

    class Kind(models.TextChoices):
        CONTACT_MESSAGE = 'contact_message', 'پیام تماس جدید'
        APPOINTMENT = 'appointment', 'نوبت جدید'
        BULK = 'bulk', 'ارسال گروهی'

    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار'
        SENT = 'sent', 'ارسال شد'
        FAILED = 'failed', 'ناموفق'
        PARTIAL = 'partial', 'ارسال ناقص'

    kind = models.CharField(max_length=32, choices=Kind.choices, verbose_name="نوع")
    status = models.CharField(
        max_length=12, choices=Status.choices,
        default=Status.PENDING, verbose_name="وضعیت",
    )
    message = models.TextField(verbose_name="متن پیام")

    recipient_count = models.PositiveIntegerField(default=0, verbose_name="تعداد گیرنده")
    sent_count = models.PositiveIntegerField(default=0, verbose_name="ارسال‌شده")
    failed_count = models.PositiveIntegerField(default=0, verbose_name="ناموفق")

    # Kept for support questions ("who exactly did we text?"). Stored as plain
    # text rather than a relation because recipients are often one-off numbers
    # typed by staff, not rows in any table.
    recipients = models.TextField(blank=True, default='', verbose_name="گیرندگان")
    error = models.TextField(blank=True, default='', verbose_name="خطا")

    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notification_logs',
        verbose_name="ایجادکننده",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "گزارش اعلان"
        verbose_name_plural = "گزارش اعلان‌ها"
        indexes = [models.Index(fields=['-created_at', 'kind'])]

    def __str__(self):
        return (
            f'{self.get_kind_display()} — {self.get_status_display()} '
            f'({self.sent_count}/{self.recipient_count})'
        )


class PushSubscription(models.Model):
    """
    One browser's permission to show this staff member a notification.

    A subscription belongs to a *browser*, not to a person: the same doctor
    signing in on a phone and a laptop produces two rows, and both should ring.
    The endpoint URL the push service hands us is globally unique, so it is the
    natural key — re-subscribing the same browser updates the row instead of
    piling up duplicates that would each deliver the same alert.

    `p256dh` and `auth` are the browser's own encryption keys. The push service
    (Google, Mozilla, Apple) only relays ciphertext; it cannot read the message
    body, which matters here because the alert names a patient.
    """
    user = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
        verbose_name="کاربر",
    )
    endpoint = models.URLField(max_length=500, unique=True, verbose_name="آدرس مقصد")
    p256dh = models.CharField(max_length=255, verbose_name="کلید عمومی مرورگر")
    auth = models.CharField(max_length=255, verbose_name="کلید احراز")

    # Only for the staff-facing list, so someone can tell "my phone" from "the
    # reception PC" when revoking one.
    user_agent = models.CharField(
        max_length=300, blank=True, default='', verbose_name="مرورگر",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت")
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name="آخرین ارسال")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "اشتراک اعلان"
        verbose_name_plural = "اشتراک‌های اعلان"
        indexes = [models.Index(fields=['user', '-created_at'])]

    def __str__(self):
        return f'{self.user} — {self.short_endpoint}'

    @property
    def short_endpoint(self):
        """Enough of the endpoint to tell two rows apart, without the token."""
        return self.endpoint[:40] + '…' if len(self.endpoint) > 40 else self.endpoint

    def as_subscription_info(self):
        """The shape pywebpush expects."""
        return {
            'endpoint': self.endpoint,
            'keys': {'p256dh': self.p256dh, 'auth': self.auth},
        }
