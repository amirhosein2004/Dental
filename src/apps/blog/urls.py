from django.urls import path

from .views.manage_view import CreateBlogView, DeleteBlogView, UpdateBlogView
from .views.public_view import BlogDetailView, BlogView, LoadMoreBlogsView

# Define app namespace
app_name = 'blog'

urlpatterns = [
    # List all blog posts
    path('', BlogView.as_view(), name='blog_list'),

    # Load more blog posts
    path('load-more-blog/', LoadMoreBlogsView.as_view(), name='load_more_blogs'),
    
    # View a specific blog post (using slug for readability and SEO).
    # `str` rather than `slug`: slugs are Unicode (Persian), and the built-in
    # `slug` converter only matches [-a-zA-Z0-9_]+.
    path('detail/<str:slug>/', BlogDetailView.as_view(), name='blog_detail'),
    
    # Create a new blog post
    path('create/', CreateBlogView.as_view(), name='create_blog'),
    
    # Update an existing blog post
    path('update/<int:pk>/', UpdateBlogView.as_view(), name='update_blog'),
    
    # Delete a blog post
    path('delete/<int:pk>/', DeleteBlogView.as_view(), name='delete_blog'),
]