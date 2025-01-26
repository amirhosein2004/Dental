from django.urls import path
from .views import BlogView, BlogDetailView

urlpatterns = [
    path('', BlogView.as_view(), name='blog'),
    path('blog_detail/<int:pk>/', BlogDetailView.as_view(), name='blog_detail'),
]