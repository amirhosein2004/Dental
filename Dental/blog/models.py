from django.db import models
import jdatetime
from core.models import Category
from dashboard.models import Doctor


class BlogPost(models.Model):
    writer = models.ForeignKey(Doctor, on_delete=models.SET_NULL, related_name='blog_posts', null=True, blank=True)
    categories = models.ManyToManyField(Category, related_name='blog_posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='blog_images')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_updated_at_jalali(self):
        """ تبدیل تاریخ میلادی به شمسی """
        return jdatetime.datetime.fromgregorian(datetime=self.updated_at).strftime("%Y/%m")

    def __str__(self):
        return self.title[:50]
    