from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    image = models.ImageField(upload_to='users', default='users/default.png')
    is_doctor = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        return self.username

    """
    in the PermissionsMixin we have:
        def has_perm(self, perm, obj=None):
            if self.is_active and self.is_superuser:
                return True
        def has_module_perms(self, app_label):
            if self.is_active and self.is_superuser:
                return True
    """
    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser
    
