from utils.common_imports import models
from utils.validators import validate_image, validate_length

class Service(models.Model):
    """
    Model representing a service with title, slug, description, and image.
    """
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(
        max_length=150,
        unique=True,
        blank=True,
    )
    description = models.TextField(
        validators=[validate_length]
    )
    image = models.ImageField(
        upload_to='service_images/',
        validators=[validate_image]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  
        verbose_name = "خدمت"
        verbose_name_plural = "خدمات"

    def save(self, *args, **kwargs):
        """
        Override the save method to add custom validation and slug generation.
        """
        self.full_clean()  # Validate the model
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title[:50]
