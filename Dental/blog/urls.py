from django.urls import path
from .views import BlogView, BlogDetailView, CreateBlogView, UpdateBlogView, DeleteBlogView

app_name = 'blog'
urlpatterns = [
    path('', BlogView.as_view(), name='blog'),
    path('blog_detail/<int:pk>/', BlogDetailView.as_view(), name='blog_detail'),
    path('create_blog/', CreateBlogView.as_view(), name='create_blog'),
    path('update_blog/<int:pk>', UpdateBlogView.as_view(), name='update_blog'),
    path('delete_blog/<int:pk>', DeleteBlogView.as_view(), name='delete_blog'),
]