from utils.common_imports import models, transaction, RegexValidator
from utils.validators import validate_phone, validate_image, validate_text

class Category(models.Model):
    name = models.CharField(
        max_length=150, unique=True,
        validators=[RegexValidator(
        regex=r'^[a-zA-Z0-9\u0600-\u06FF\s\.,!?():;"\'\-]+$',
        message="نام فقط می‌تواند شامل حروف، اعداد و علائم نگارشی رایج باشد"
    )]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']  # مرتب‌سازی بر اساس نام
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
        
class Clinic(models.Model):
    name = models.CharField(
        max_length=100, unique=True,
        validators=[RegexValidator(
        regex=r'^[a-zA-Z0-9\u0600-\u06FF\s\.,!?():;"\'\-]+$',
        message="نام فقط می‌تواند شامل حروف، اعداد و علائم نگارشی رایج باشد"
    )]
        )
    address = models.CharField(
        max_length=100,
        validators=[RegexValidator(
        regex=r'^[a-zA-Z0-9\u0600-\u06FF\s\.,!?():;"\'\-]+$',
        message="آدرس فقط می‌تواند شامل حروف، اعداد و علائم نگارشی رایج باشد"
    )]
        )
    phone = models.CharField(
        max_length=20,
        validators=[validate_phone])
    email = models.EmailField(max_length=254)
    description = models.TextField(validators=[validate_text])
    image = models.ImageField(
        upload_to='clinic_images',
        validators=[validate_image]
        )
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "مطب"
        verbose_name_plural = "مطب‌ها"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
        
    
    def ensure_single_primary(self):
        """اطمینان از اینکه فقط این مطب اصلی باشد"""
        Clinic.objects.filter(is_primary=True).exclude(pk=self.pk).update(is_primary=False)

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():  # تراکنش اتمی
            if self.is_primary:  # فقط در صورت لزوم اجرا شود
                self.ensure_single_primary()
            super().save(*args, **kwargs)