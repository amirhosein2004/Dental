from django.db import models
from .managers import WorkingHoursManager
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
    day = models.IntegerField(choices=DAYS_OF_WEEK, help_text="روز هفته")
    
    # بازه صبح
    morning_start = models.IntegerField(null=True, blank=True, verbose_name="شروع صبح")
    morning_end = models.IntegerField(null=True, blank=True, verbose_name="پایان صبح")
    
    # بازه عصر
    evening_start = models.IntegerField(null=True, blank=True, verbose_name="شروع عصر")
    evening_end = models.IntegerField(null=True, blank=True, verbose_name="پایان عصر")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['day'], name='unique_day')
        ]
        ordering = ['day']
        verbose_name = "ساعت کاری"
        verbose_name_plural = "ساعات کاری"

    # objects = WorkingHoursManager()

    def __str__(self):
        day_name = dict(DAYS_OF_WEEK).get(self.day, "نامشخص")
        return f"{day_name}: صبح {self.morning_start} تا {self.morning_end} | عصر {self.evening_start} تا {self.evening_end}"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام")
    phone = models.CharField(max_length=20, verbose_name="شماره تماس")
    message = models.TextField(verbose_name="پیام")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ارسال")
    is_read = models.BooleanField(default=False, verbose_name="خوانده شده؟")

    def get_created_at_jalali(self):
        """ تبدیل تاریخ میلادی به شمسی """
        return jdatetime.datetime.fromgregorian(datetime=self.created_at).strftime("%Y/%m/%d - %H:%M")

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"