from utils.common_imports import models, ValidationError, transaction, IntegrityError
from utils.validators import validate_image, validate_length
from django.utils.text import slugify
from googletrans import Translator  # Importing Google Translate

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
        with transaction.atomic():
            # Generate a new slug if it doesn't exist or if the title has changed
            if not self.slug or (self.pk is None or self.title != Service.objects.get(pk=self.pk).title):
                self.slug = self._generate_unique_slug()
            try:
                super().save(*args, **kwargs)
            except IntegrityError:
                raise ValidationError("عنوان تکراری است. لطفاً عنوان دیگری انتخاب کنید")

    def _generate_unique_slug(self):
        """
        Generate a unique slug for the service based on the title.
        """
        try:
            translator = Translator()
            english_title = translator.translate(self.title, src='fa', dest='en').text
        except Exception as e:
            # Raise a validation error if translation fails
            raise ValidationError("خطایی رخ داده است. لطفاً بعداً تلاش کنید")
        
        base_slug = slugify(english_title)[:150]  # Limit initial length
        unique_slug = base_slug
        counter = 1
        
        # Ensure the slug is unique by appending a counter if necessary
        while Service.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1
        return unique_slug

    def __str__(self):
        return self.title[:50]
