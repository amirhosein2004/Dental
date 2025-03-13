import jdatetime
from utils.common_imports import models, ValidationError, transaction, IntegrityError
from utils.validators import validate_image, validate_slug, validate_title, validate_content
from core.models import Category
from dashboard.models import Doctor
from django.utils.text import slugify
from googletrans import Translator  # اضافه کردن گوگل ترنسلیت

class BlogPost(models.Model):
    """مدل پست وبلاگ"""
    
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
    title = models.CharField(
        unique=True,
        max_length=200,
        validators=[validate_title]
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        null=True,
        validators=[validate_slug]
    )
    content = models.TextField(
        validators=[validate_content]
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
        self.full_clean()
        with transaction.atomic():
            if not self.slug or (self.pk is None or self.title != BlogPost.objects.get(pk=self.pk).title):
                self.slug = self._generate_unique_slug()
            try:
                super().save(*args, **kwargs)
            except IntegrityError:
                raise ValidationError("عنوان تکراری است. لطفاً عنوان دیگری انتخاب کنید")

    def _generate_unique_slug(self):
        """
        تولید اسلاگ یکتا بر اساس عنوان
        
        Returns:
            str: اسلاگ یکتا
        """
        try:
            translator = Translator()
            english_title = translator.translate(self.title, src='fa', dest='en').text
        except Exception as e:
            # با استفاده از ValidationError می‌توانیم خطا را به سطح ویو منتقل کنیم.
            raise ValidationError("خطایی رخ داده است. لطفاً بعداً تلاش کنید")
        
        base_slug = slugify(english_title)[:150]  # محدود کردن طول اولیه
        unique_slug = base_slug
        counter = 1
        
        while BlogPost.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1
            if len(unique_slug) > 200:
                unique_slug = f"{base_slug[:195]}-{counter}"
        return unique_slug

    @property
    def get_updated_at_jalali(self):
        """
        تبدیل تاریخ به‌روزرسانی به فرمت شمسی
        
        Returns:
            str: تاریخ شمسی در فرمت YYYY/MM
        """
        return jdatetime.datetime.fromgregorian(datetime=self.updated_at).strftime("%Y/%m")

    def __str__(self):
        """نمایش رشته‌ای پست"""
        return f"{self.title[:50]} - {self.writer or 'بدون نویسنده'}"