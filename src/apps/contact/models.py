import jdatetime

from django.db import models

from utils.data.validators import validate_phone, validate_length

class ContactMessage(models.Model):
    """
    Model to represent a contact message.
    """
    name = models.CharField(max_length=100)
    # 11 chars matches the validator (Iranian numbers: 11 digits, mobile/landline).
    phone = models.CharField(max_length=11, validators=[validate_phone])
    message = models.TextField(validators=[validate_length])
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']  
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"

    def save(self, *args, **kwargs):
        """
        Override save method to perform full clean before saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def get_created_at_jalali(self):
        """
        Convert Gregorian date to Jalali (Persian) date.
        """
        if not self.created_at:
            return "نامشخص"
        return jdatetime.datetime.fromgregorian(datetime=self.created_at).strftime("%Y/%m/%d - %H:%M")

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"