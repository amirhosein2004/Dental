# Django imports
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin  

# Project-specific imports from common_imports
from utils.common_imports import models, RegexValidator
from utils.validators import validate_image

# Imports from local managers
from .managers import CustomUserManager  


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^(?![_\W])(?!(\d+$))[a-zA-Z0-9_@.+-]+$',
                message="نام کاربری نباید با `_` یا کاراکتر خاص شروع شود، نباید فقط شامل اعداد باشد و فقط می‌تواند شامل حروف، اعداد و کاراکترهای `_@.+-` باشد"
        )])
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(
        max_length=100,
        validators=[RegexValidator(r'^[a-zA-Z\u0600-\u06FF\s]+$', 'فقط حروف فارسی یا انگلیسی')]
    )
    last_name = models.CharField(
        max_length=100,
        validators=[RegexValidator(r'^[a-zA-Z\u0600-\u06FF\s]+$', 'فقط حروف فارسی یا انگلیسی')]
    )
    image = models.ImageField(
        upload_to='users',
        default='users/default.png',
        blank=True,
        validators=[validate_image]
    )
    is_doctor = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.username
    
    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser
