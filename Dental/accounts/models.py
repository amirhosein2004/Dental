# Standard library imports
import secrets
# Project-specific imports from common_imports
from utils.common_imports import models, get_user_model, RegexValidator, transaction

# Third-party imports
from django.utils.timezone import now, timedelta  

User = get_user_model()
class OTP(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='otp',
    )
    code = models.CharField(max_length=6, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "کد OTP"
        verbose_name_plural = "کدهای OTP"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @transaction.atomic
    def generate_otp(self):
        """تولید و جایگزینی کد OTP جدید"""
        self.code = str(secrets.randbelow(1000000)).zfill(6)
        self.created_at = now()
        self.save()

    def is_valid(self):
        """بررسی اعتبار کد (۲ دقیقه)"""
        return (now() - self.created_at) <= timedelta(minutes=2)
    
    def __str__(self):
        return f"OTP برای {self.user.username if self.user else 'کاربر نامشخص'} - {self.code}"
    