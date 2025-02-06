from django.db import models
from django_jalali.db import models as jmodels
from django.contrib.auth import get_user_model
from core.models import Category

User = get_user_model()
class BlogPost(models.Model):
    writer = models.ForeignKey(User, on_delete=models.CASCADE)
    categories = models.ManyToManyField(Category, related_name='blog_posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='blog_images')
    created_at = jmodels.jDateField(auto_now_add=True)
    updated_at = jmodels.jDateField(auto_now=True)

    def __str__(self):
        return self.title[:50]
