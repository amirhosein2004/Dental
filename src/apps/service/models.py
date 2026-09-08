from django.db import models
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

from utils.security.sanitize import sanitize_html
from utils.data.validators import validate_image, validate_rich_length


class Service(models.Model):
    """
    One treatment the practice offers, with a page of its own.

    Every service used to render as a card on a single `/service/` page. A
    page can only be the best answer to one question, so that one page was
    competing with itself for "ایمپلنت", "ارتودنسی" and everything else at
    once, and winning none of them. Splitting them gives each treatment a URL,
    a heading and a body that match one search.

    This is not the same move as a page per city, which was considered and
    rejected: separate treatments are genuinely different subjects, whereas
    the same treatment described twice with the city swapped is a doorway
    page.
    """
    title = models.CharField(max_length=200, unique=True, verbose_name="عنوان")
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        # Persian titles slugify to Persian text; the ASCII-only default
        # validator would reject every real service on this site.
        allow_unicode=True,
        verbose_name="نشانی صفحه",
        help_text="خالی بگذارید تا از عنوان ساخته شود",
    )
    description = CKEditor5Field(
        config_name='simple',
        validators=[validate_rich_length],
        verbose_name="توضیح کوتاه",
        help_text=(
            "متنی که در کارت خدمت و بالای صفحه‌ی خدمت دیده می‌شود؛ "
            "می‌توانید بخشی از آن را پررنگ یا فهرست کنید"
        ),
    )
    content = CKEditor5Field(
        blank=True,
        default='',
        verbose_name="متن کامل",
        help_text="توضیح کامل خدمت؛ همین متن است که در گوگل رتبه می‌گیرد",
    )
    image = models.ImageField(
        upload_to='service_images/',
        validators=[validate_image],
        verbose_name="تصویر",
    )
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name="عنوان متا",
        help_text="خالی بگذارید تا از عنوان خدمت ساخته شود",
    )
    meta_description = models.CharField(
        max_length=300,
        blank=True,
        default='',
        verbose_name="توضیح متا",
        help_text="خالی بگذارید تا از توضیح کوتاه ساخته شود",
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="ترتیب نمایش",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "خدمت"
        verbose_name_plural = "خدمات"

    def save(self, *args, **kwargs):
        """
        Override the save method to add custom validation and slug generation.
        """
        if not self.slug:
            self.slug = self._build_slug()

        # Both rich-text fields are rendered with `|safe`, so they are
        # filtered here rather than in the form: the admin, a fixture load and
        # a management command all reach the database through `save` and none
        # of them through a form.
        if self.content:
            self.content = sanitize_html(self.content)
        if self.description:
            self.description = sanitize_html(self.description)

        self.full_clean()  # Validate the model
        super().save(*args, **kwargs)

    def _build_slug(self):
        base = slugify(self.title, allow_unicode=True) or 'service'
        slug, n = base, 2
        while Service.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            slug = f'{base}-{n}'
            n += 1
        return slug

    def get_absolute_url(self):
        return reverse('service:service_detail', kwargs={'slug': self.slug})

    @property
    def seo_title(self):
        return self.meta_title or self.title

    @property
    def seo_description(self):
        """
        A description is never left empty — Google writes its own snippet from
        whatever text it finds first when one is missing, which on this site
        would be the navigation.
        """
        if self.meta_description:
            return self.meta_description
        # `description` is markup now; a meta description carrying `<strong>`
        # is what Google prints in the result.
        return strip_tags(self.description)[:297].strip()

    def __str__(self):
        return self.title[:50]


class ServiceFAQ(models.Model):
    """
    A question a patient actually asks about one treatment.

    These sit on the treatment's own page rather than on a site-wide FAQ page.
    A standalone FAQ page would compete with these very services for the same
    queries — the site would be bidding against itself — and it answers no
    single search intent, so it rarely ranks for anything.

    Worth setting expectations: Google cut FAQ rich results for most sites in
    2023, so the visible star-and-accordion result is unlikely. The value is
    that the question text itself matches how people search ("ایمپلنت چقدر
    طول می‌کشد") — which is a different and more durable benefit.
    """
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='faqs',
        verbose_name="خدمت",
    )
    question = models.CharField(max_length=300, verbose_name="سؤال")
    answer = models.TextField(verbose_name="پاسخ")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "سؤال متداول خدمت"
        verbose_name_plural = "سؤالات متداول خدمات"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.question[:60]
