import jdatetime
from utils.common_imports import models, ValidationError, transaction, IntegrityError
from utils.validators import validate_image, validate_length
from core.models import Category
from dashboard.models import Doctor
from django.utils.text import slugify
from googletrans import Translator  # add google translate
from functools import partial
from django_ckeditor_5.fields import CKEditor5Field  # add ckeditor


class BlogPost(models.Model):
    """
    Model for the blogs
    """
    writer = models.ForeignKey(
        Doctor,  
        on_delete=models.SET_NULL,
        related_name='blog_posts',
        null=True,
    )
    categories = models.ManyToManyField(
        Category, 
        related_name='blog_posts',
    )
    title = models.CharField(unique=True, max_length=200)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
    )
    content = CKEditor5Field(
        validators=[partial(validate_length, min_length=50, max_length=20000)]
    )
    image = models.ImageField(
        upload_to='blog_images',
        validators=[validate_image]
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = 'وبلاگ'
        verbose_name_plural = 'وبلاگ ها'
        ordering = ['-updated_at']

    def save(self, *args, **kwargs):
        """
        Override the save method to include custom validation and slug generation.
        """
        self.full_clean()  # Validate the model fields
        with transaction.atomic():
            # Generate a unique slug if it doesn't exist or if the title has changed
            if not self.slug or (self.pk is None or self.title != BlogPost.objects.get(pk=self.pk).title):
                self.slug = self._generate_unique_slug()
            try:
                super().save(*args, **kwargs)  
            except IntegrityError:
                raise ValidationError("عنوان تکراری است. لطفاً عنوان دیگری انتخاب کنید")

    def _generate_unique_slug(self):
        """
        Generate a unique slug based on the title.
        
        Returns:
            str: Unique slug
        """
        try:
            translator = Translator()
            english_title = translator.translate(self.title, src='fa', dest='en').text
        except Exception as e:
            # Raise a validation error to be handled at the view level
            raise ValidationError("خطایی رخ داده است. لطفاً بعداً تلاش کنید")
        
        base_slug = slugify(english_title)[:150]  # Limit initial length
        unique_slug = base_slug
        counter = 1
        
        # Ensure the slug is unique
        while BlogPost.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1
            if len(unique_slug) > 200:
                unique_slug = f"{base_slug[:195]}-{counter}"
        return unique_slug

    @property
    def get_updated_at_jalali(self):
        """
        Convert the updated_at date to Jalali format.
        
        Returns:
            str: Jalali date in YYYY/MM format
        """
        return jdatetime.datetime.fromgregorian(datetime=self.updated_at).strftime("%Y/%m")

    def __str__(self):
        """
        String representation of the blog post.
        
        Returns:
            str: Title and writer of the blog post
        """
        return f"{self.title[:50]} - {self.writer or 'بدون نویسنده'}"