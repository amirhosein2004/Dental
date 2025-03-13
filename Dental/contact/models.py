# Project-specific imports from common_imports
from utils.common_imports import models, RegexValidator
from utils.validators import validate_phone, validate_text, validate_hour

# Third-party imports
import jdatetime  


DAYS_OF_WEEK = (
    (0, "شنبه"),
    (1, "یک‌شنبه"),
    (2, "دو‌شنبه"),
    (3, "سه‌شنبه"),
    (4, "چهارشنبه"),
    (5, "پنج‌شنبه"),
    (6, "جمعه"),
)  

class WorkingHours(models.Model):
    day = models.IntegerField(
        choices=DAYS_OF_WEEK,
        help_text="روز هفته",
    )
    morning_start = models.IntegerField(
        null=True, blank=True,
        validators=[validate_hour],
        help_text="ساعت شروع شیفت صبح (0-23)"
    )
    morning_end = models.IntegerField(
        null=True, blank=True,
        validators=[validate_hour],
        help_text="ساعت پایان شیفت صبح (0-23)"
    )
    evening_start = models.IntegerField(
        null=True, blank=True,
        validators=[validate_hour],
        help_text="ساعت شروع شیفت عصر (0-23)"
    )
    evening_end = models.IntegerField(
        null=True, blank=True,
        validators=[validate_hour],
        help_text="ساعت پایان شیفت عصر (0-23)"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['day'], name='unique_day')
        ]
        ordering = ['day']
        verbose_name = "ساعت کاری"
        verbose_name_plural = "ساعات کاری"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        day_name = dict(DAYS_OF_WEEK).get(self.day, "نامشخص")
        morning = f"{self.morning_start or '-'} تا {self.morning_end or '-'}" if self.morning_start and self.morning_end else "تعطیل"
        evening = f"{self.evening_start or '-'} تا {self.evening_end or '-'}" if self.evening_start and self.evening_end else "تعطیل"
        return f"{day_name}: صبح {morning} | عصر {evening}"

class ContactMessage(models.Model):
    name = models.CharField(
        max_length=100,
        validators=[RegexValidator(
        regex=r'^[a-zA-Z0-9\u0600-\u06FF\s\.,!?():;"\'\-]+$',
        message="متن فقط می‌تواند شامل حروف، اعداد و علائم نگارشی رایج باشد"
    )]
        )
    phone = models.CharField(
        max_length=20,
        validators=[validate_phone]
    )
    message = models.TextField(
        validators=[validate_text]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']  
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def get_created_at_jalali(self):
        """ تبدیل تاریخ میلادی به شمسی """
        if not self.created_at:
            return "نامشخص"
        return jdatetime.datetime.fromgregorian(datetime=self.created_at).strftime("%Y/%m/%d - %H:%M")

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"