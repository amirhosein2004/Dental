from utils.common_imports import models

# if need to banner or images or another things we back


class Banner(models.Model):
    title = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    image = models.ImageField(upload_to='banner_images')

    class Meta:
        ordering = ['title']
        verbose_name = "بنر"
        verbose_name_plural = "بنرها"

    def __str__(self):
        return self.title
