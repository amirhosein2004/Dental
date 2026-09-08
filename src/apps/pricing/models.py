from django.core.validators import MinValueValidator
from django.db import models


class PricingCategory(models.Model):
    """
    Grouping bucket for :class:`PricingItem` (e.g. "ایمپلنت", "عصب‌کشی").
    Managed by staff via the pricing UI.
    """
    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="نام دسته",
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="ترتیب نمایش",
        help_text="عدد کوچک‌تر بالاتر نمایش داده می‌شود",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "دسته‌بندی تعرفه"
        verbose_name_plural = "دسته‌بندی‌های تعرفه"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PricingItem(models.Model):
    """
    Model representing a pricing item for dental services.
    """
    category = models.ForeignKey(
        PricingCategory,
        on_delete=models.SET_NULL,
        related_name='items',
        null=True,
        blank=True,
        verbose_name="دسته‌بندی",
    )
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
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.price:,} تومان"
