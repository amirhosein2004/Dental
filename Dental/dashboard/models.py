from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()
class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(default="توضیحات پزشک هنوز ثبت نشده است.")
    twitter = models.URLField(max_length=200, blank=True, default='')
    instagram = models.URLField(max_length=200, blank=True, default='')
    telegram = models.URLField(max_length=200, blank=True, default='')
    linkedin = models.URLField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name if self.user else "بدون نام"
    
