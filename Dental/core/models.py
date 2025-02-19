from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
    
class Clinic(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    description = models.TextField()
    image = models.ImageField(upload_to='clinic_images')

    def __str__(self):
        return self.name