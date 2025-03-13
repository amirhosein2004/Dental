from utils.common_imports import models, get_user_model
from utils.validators import validate_url, validate_text

User = get_user_model()

class Doctor(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )
    description = models.TextField(
        default="توضیحات پزشک هنوز ثبت نشده است",
        validators=[validate_text]
        )
    twitter = models.URLField(
        max_length=200,
        blank=True,
        default='',
        validators=[validate_url]
    )
    instagram = models.URLField(
        max_length=200,
        blank=True,
        default='',
        validators=[validate_url]
    )
    telegram = models.URLField(
        max_length=200,
        blank=True,
        default='',
        validators=[validate_url]
    )
    linkedin = models.URLField(
        max_length=200,
        blank=True,
        default='',
        validators=[validate_url]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "پزشک"
        verbose_name_plural = "پزشکان"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.user:
            full_name = self.user.get_full_name.strip()
            return full_name if full_name else "نام پزشک مشخص نیست"
        return "بدون نام"
        
