from utils.common_imports import models, get_user_model
from utils.validators import validate_url, validate_text

User = get_user_model()

class Doctor(models.Model):
    """
    Model representing a doctor with user information and social media links.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        help_text="The user associated with this doctor."
    )
    description = models.TextField(
        default="توضیحات پزشک هنوز ثبت نشده است",
        validators=[validate_text],
        help_text="Description of the doctor."
    )
    twitter = models.URLField(
        max_length=200,
        blank=True,
        default='',
        validators=[validate_url],
        help_text="Twitter profile URL of the doctor."
    )
    instagram = models.URLField(
        max_length=200,
        blank=True,
        default='',
        validators=[validate_url],
        help_text="Instagram profile URL of the doctor."
    )
    telegram = models.URLField(
        max_length=200,
        blank=True,
        default='',
        validators=[validate_url],
        help_text="Telegram profile URL of the doctor."
    )
    linkedin = models.URLField(
        max_length=200,
        blank=True,
        default='',
        validators=[validate_url],
        help_text="LinkedIn profile URL of the doctor."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when the doctor record was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when the doctor record was last updated."
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "پزشک"
        verbose_name_plural = "پزشکان"

    def save(self, *args, **kwargs):
        """
        Override the save method to perform full_clean before saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.user:
            full_name = self.user.get_full_name.strip()
            return full_name if full_name else "نام پزشک مشخص نیست"
        return "بدون نام"
