from django.db import models


class Service(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='service_images')

    def __str__(self):
        return self.title[:50]
    
