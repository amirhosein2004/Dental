from django.db import models

# if need to banner or images or another things we back


class Banner(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='banner_images')

    def __str__(self):
        return self.title
