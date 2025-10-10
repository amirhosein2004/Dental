from utils.common_imports import models
from django.core.validators import MinValueValidator


class PricingItem(models.Model):
    """
    Model representing a pricing item for dental services.
    """
    title = models.CharField(
        max_length=500,
        verbose_name="عنوان خدمت"
    )
    price = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="قیمت (تومان)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name = "تعرفه خدمت"
        verbose_name_plural = "تعرفه‌های خدمات"

    def save(self, *args, **kwargs):
        """
        Override the save method to perform full_clean before saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.price:,} تومان"
