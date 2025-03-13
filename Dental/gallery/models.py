from utils.common_imports import models
from core.models import Category
from dashboard.models import Doctor
from utils.validators import validate_image

class Gallery(models.Model):
    """
    Model representing a gallery which can be associated with a doctor and a category.
    """
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
        """
        Override the save method to perform full_clean before saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"category: {self.category.name if self.category else 'بدون دسته‌بندی'} | gallery: {self.id}"
    
def gallery_image_upload_path(instance, filename):
    """
    Generate the upload path for gallery images.
    
    Args:
        instance: The instance of the Image model.
        filename: The original filename of the uploaded image.
    
    Returns:
        str: The upload path for the image.
    """
    return f'gallery_images/{instance.gallery.id}/{filename}'

class Image(models.Model):
    """
    Model representing an image associated with a gallery.
    """
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
        """
        Override the save method to perform full_clean before saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for Gallery {self.gallery.id}"