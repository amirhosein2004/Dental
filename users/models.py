# Django imports
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin  

# Project-specific imports from common_imports
from utils.common_imports import models
from utils.validators import validate_image

# Imports from local managers
from .managers import CustomUserManager  


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that extends AbstractBaseUser and PermissionsMixin.
    """
    username = models.CharField(max_length=150, unique=True,)
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=100,)
    last_name = models.CharField(max_length=100,)
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
        """
        Override the save method to ensure full_clean is called before saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)
        
    @property
    def get_full_name(self):
        """
        Returns the full name of the user.
        """
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        """
        Returns the string representation of the user.
        """
        return self.username
    
    def has_perm(self, perm, obj=None):
        """
        Returns True if the user has the specified permission.
        """
        return self.is_superuser

    def has_module_perms(self, app_label):
        """
        Returns True if the user has permissions to view the app `app_label`.
        """
        return self.is_superuser
