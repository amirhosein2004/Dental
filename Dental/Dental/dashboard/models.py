from utils.common_imports import models, get_user_model
from utils.validators import validate_length

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
        validators=[validate_length]
    )
    twitter = models.URLField(max_length=200, blank=True, default='')
    instagram = models.URLField(max_length=200, blank=True, default='')
    telegram = models.URLField(max_length=200, blank=True, default='')
    linkedin = models.URLField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
