from django.db import models
from core.models import Category

class Gallery(models.Model):
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, related_name='galleries') 

    def __str__(self):
        return f"{self.category} - {self.id}"

class Image(models.Model):
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='gallery_images/')

    def __str__(self):
        return f"Image {self.id} for Gallery {self.gallery.id}"