# Standard library imports
import secrets

# Project-specific imports from common_imports
from utils.common_imports import models, get_user_model, RegexValidator, transaction

# Third-party imports
from django.utils.timezone import now, timedelta  

# Get the user model
User = get_user_model()

class OTP(models.Model):
    """
    Model to store OTP code for a user.
    """
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
        """
        Override save method to perform full_clean before saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    @transaction.atomic
    def generate_otp(self):
        """
        Generate and replace the OTP code with a new one.
        """
        self.code = str(secrets.randbelow(1000000)).zfill(6)
        self.created_at = now()
        self.save()

    def is_valid(self):
        """
        Check if the OTP code is valid (within 2 minutes).
        """
        return (now() - self.created_at) <= timedelta(minutes=2)
    
    def __str__(self):
        """
        String representation of the OTP object.
        """
        return f"OTP برای {self.user.username if self.user else 'کاربر نامشخص'} - {self.code}"