from utils.common_imports import models, transaction
from utils.validators import validate_phone, validate_image, validate_length

class Category(models.Model):
    """
    Model for category.
    """
    name = models.CharField(max_length=150, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']  # Sort by name
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def save(self, *args, **kwargs):
        """
        Override save method to perform full_clean before saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
        
class Clinic(models.Model):
    """
    Model for clinic.
    """
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, validators=[validate_phone])
    email = models.EmailField(max_length=254)
    description = models.TextField(validators=[validate_length])
    image = models.ImageField(upload_to='clinic_images', validators=[validate_image])
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']  # Sort by name
        verbose_name = "مطب"
        verbose_name_plural = "مطب‌ها"

    def save(self, *args, **kwargs):
        """
        Override save method to perform full_clean before saving.
        Ensure only one primary clinic exists.
        """
        self.full_clean()
        with transaction.atomic():  # Atomic transaction
            if self.is_primary:  # Execute only if necessary
                self.ensure_single_primary()
            super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def ensure_single_primary(self):
        """
        Ensure that only this clinic is marked as primary.
        """
        Clinic.objects.filter(is_primary=True).exclude(pk=self.pk).update(is_primary=False)


# Constants for days of the week in Persian
DAYS_OF_WEEK = (
    (0, "شنبه"),
    (1, "یک‌شنبه"),
    (2, "دو‌شنبه"),
    (3, "سه‌شنبه"),
    (4, "چهارشنبه"),
    (5, "پنج‌شنبه"),
    (6, "جمعه"),
)  

class WorkingHours(models.Model):
    """
    Model to represent working hours for each day of the week.
    """
    day = models.IntegerField(
        choices=DAYS_OF_WEEK,
        help_text="روز هفته",
    )
    morning_start = models.IntegerField(
        null=True, blank=True,
        help_text="ساعت شروع شیفت صبح (0-23)"
    )
    morning_end = models.IntegerField(
        null=True, blank=True,
        help_text="ساعت پایان شیفت صبح (0-23)"
    )
    evening_start = models.IntegerField(
        null=True, blank=True,
        help_text="ساعت شروع شیفت عصر (0-23)"
    )
    evening_end = models.IntegerField(
        null=True, blank=True,
        help_text="ساعت پایان شیفت عصر (0-23)"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['day'], name='unique_day')
        ]
        ordering = ['day']
        verbose_name = "ساعت کاری"
        verbose_name_plural = "ساعات کاری"

    def save(self, *args, **kwargs):
        """
        Override save method to perform full clean before saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        day_name = dict(DAYS_OF_WEEK).get(self.day, "نامشخص")
        morning = f"{self.morning_start or '-'} تا {self.morning_end or '-'}" if self.morning_start and self.morning_end else "تعطیل"
        evening = f"{self.evening_start or '-'} تا {self.evening_end or '-'}" if self.evening_start and self.evening_end else "تعطیل"
        return f"{day_name}: صبح {morning} | عصر {evening}"
    
    
class Banner(models.Model):
    """
    Model represent banner in home page
    """
    title = models.CharField(max_length=200, unique=True)
    image = models.ImageField(upload_to='banner_images/%Y/%m/%d', validators=[validate_image])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "بنر"
        verbose_name_plural = "بنرها"

    def __str__(self):
        return self.title
    
