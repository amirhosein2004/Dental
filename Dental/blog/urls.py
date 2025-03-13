"""
URL configuration for the Blog section.

This module defines the URL patterns for the 'blog' app, handling requests for 
listing blogs, viewing blog details, creating, updating, and deleting blog posts.
"""

from utils.common_imports import path
from .views import BlogView, BlogDetailView, CreateBlogView, UpdateBlogView, DeleteBlogView

# Define app namespace
app_name = 'blog'

urlpatterns = [
    # List all blog posts
    path('', BlogView.as_view(), name='blog_list'),
    
    # View a specific blog post (using slug for readability and SEO)
    path('detail/<slug:slug>/', BlogDetailView.as_view(), name='blog_detail'),
    
    # Create a new blog post
    path('create/', CreateBlogView.as_view(), name='create_blog'),
    
    # Update an existing blog post
    path('update/<int:pk>/', UpdateBlogView.as_view(), name='update_blog'),
    
    # Delete a blog post
    path('delete/<int:pk>/', DeleteBlogView.as_view(), name='delete_blog'),
]