from utils.common_imports import models, ValidationError, transaction, IntegrityError
from utils.validators import validate_image, validate_text, validate_title, validate_slug
from django.utils.text import slugify
from googletrans import Translator  # اضافه کردن گوگل ترنسلیت

class Service(models.Model):
    title = models.CharField(
        max_length=200,
        unique=True,
        validators=[validate_title]
    )
    slug = models.SlugField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        validators=[validate_slug]
    )
    description = models.TextField(
        validators=[validate_text]
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
        self.full_clean()
        with transaction.atomic():
            if not self.slug or (self.pk is None or self.title != Service.objects.get(pk=self.pk).title):
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
        
        while Service.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1
        return unique_slug

    def __str__(self):
        return self.title[:50]
    
