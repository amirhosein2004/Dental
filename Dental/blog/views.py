from django.views import View
from django.shortcuts import render
from .models import BlogPost

class BlogView(View):

    def get(self, request, *args, **kwargs):
        blogs = BlogPost.objects.all()
        return render(request, 'blog/blog.html', {'blogs':blogs})
    
    def post(self, request, *args, **kwargs):
        pass

class BlogDetailView(View):

    def get(self, request, *args, **kwargs):
        blog = BlogPost.objects.get(pk=kwargs['pk'])
        return render(request, 'blog/blog_detail.html', {'blog':blog})

    def post(self, request, *args, **kwargs):
        pass
