from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class Clinic(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    description = models.TextField()
    image = models.ImageField(upload_to='clinic_images')

    def __str__(self):
        return self.name
    
class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    description = models.TextField()
    image = models.ImageField(upload_to='doctor_images')
    twitter = models.URLField(max_length=200, blank=True, null=True)
    instagram = models.URLField(max_length=200, blank=True, null=True)
    telegram = models.URLField(max_length=200, blank=True, null=True)
    linkedin = models.URLField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name 

class Service(models.Model):
    title = models.CharField(max_length=255, verbose_name="عنوان خدمت")
    description = models.TextField(verbose_name="توضیحات خدمت")
    icon = models.ImageField(upload_to='service_icons', null=True, blank=True, verbose_name="آیکون خدمت")

    def __str__(self):
        return self.title