from functools import partial

import jdatetime
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field

from apps.core.models import Category
from apps.dashboard.models import Doctor
from utils.security.sanitize import sanitize_html
from utils.data.validators import validate_image, validate_length


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
        # Persian titles slugify to Persian text; the default validator only
        # accepts ASCII, which would reject every real post on this site.
        allow_unicode=True,
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
        Override save to run full_clean and surface unique-constraint collisions
        (title or slug) as ValidationErrors rather than raw IntegrityErrors.
        Slug is supplied by the user via the form.
        """
        # Sanitise before validating, so the length validator measures what
        # will actually be stored. This lives on the model rather than the
        # form because `content` is rendered with `|safe`: the admin, a
        # management command and a fixture load all have to go through the
        # same filter, and only `save` catches all of them.
        self.content = sanitize_html(self.content)

        self.full_clean()
        try:
            super().save(*args, **kwargs)
        except IntegrityError:
            raise ValidationError("عنوان یا slug تکراری است. لطفاً مقدار دیگری انتخاب کنید")

    def get_absolute_url(self):
        """
        The post's canonical address.

        Templates already built this URL with `{% url %}`, so the method looks
        redundant — until something outside a template needs it. The sitemap
        does, and Django's Sitemap calls `get_absolute_url()` by name: without
        this the blog section of /sitemap.xml raised AttributeError and took
        the whole file down with it, including the service and doctor URLs
        that had nothing wrong with them.
        """
        return reverse('blog:blog_detail', kwargs={'slug': self.slug})

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