from utils.common_imports import models
from core.models import Category
from dashboard.models import Doctor
from utils.validators import validate_image

class Gallery(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        related_name='doctor_galleries',
        null=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='category_galleries',
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "گالری"
        verbose_name_plural = "گالری‌ها"
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"category: {self.category.name if self.category else 'بدون دسته‌بندی'} | gallery: {self.id}"
    
def gallery_image_upload_path(instance, filename):
    return f'gallery_images/{instance.gallery.id}/{filename}'

class Image(models.Model):
    gallery = models.ForeignKey(
        Gallery,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(
        upload_to=gallery_image_upload_path, 
        validators=[validate_image]
        )

    class Meta:
        ordering = ['id']
        verbose_name = "تصویر"
        verbose_name_plural = "تصاویر"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for Gallery {self.gallery.id}"