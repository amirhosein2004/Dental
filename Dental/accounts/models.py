from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
import random

User = get_user_model()
class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_otp(self):
        """حذف OTPهای منقضی‌شده و ایجاد کد جدید"""
        OTP.objects.filter(created_at__lt=now() - timedelta(minutes=5)).delete()  # حذف کدهای قدیمی
        self.code = str(random.randint(100000, 999999))
        self.created_at = now()
        self.save()

    def is_valid(self):
        """بررسی اعتبار کد (۵ دقیقه)"""
        return (now() - self.created_at).seconds < 300