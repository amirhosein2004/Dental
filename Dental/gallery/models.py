from django.db import models
from core.models import Category
from dashboard.models import Doctor

class Gallery(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, related_name='doctor_galleries', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='galleries', null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category} - {self.id}"

class Image(models.Model):
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='gallery_images/')

    def __str__(self):
        return f"Image {self.id} for Gallery {self.gallery.id}"