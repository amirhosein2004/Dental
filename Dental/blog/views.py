from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from .models import BlogPost
from django.http import Http404
from .forms import BlogPostForm
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .filters import BlogPostFilter
from dashboard.models import Doctor

class BlogView(View):
    filter_class = BlogPostFilter

    def get(self, request, *args, **kwargs):
        blogs = BlogPost.objects.all()
        blog_filter = self.filter_class(request.GET, queryset=blogs)
        return render(request, 'blog/blog.html', {'blogs': blog_filter.qs, 'filter': blog_filter})

class BlogDetailView(View):

    def get(self, request, *args, **kwargs):
        blog = get_object_or_404(BlogPost, pk=kwargs['pk'])
        return render(request, 'blog/blog_detail.html', {'blog': blog})

class CreateBlogView(View):
    form_class = BlogPostForm
    template_name = 'blog/create_blog.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
        
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            blog = form.save(commit=False)
            doctor = Doctor.objects.get(user=request.user)
            blog.writer = doctor
            blog.save()
            messages.success(request, "بلاگ جدید با موفقیت ایجاد شد.")
            return redirect('blog:blog')
        messages.error(request, "خطا در ایجاد بلاگ. لطفاً دوباره تلاش کنید.")
        return render(request, self.template_name, {'form': form})

class UpdateBlogView(View):
    form_class = BlogPostForm
    template_name = 'blog/update_blog.html'

    def dispatch(self, request, *args, **kwargs):
        blog = get_object_or_404(BlogPost, pk=kwargs['pk'])
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            if request.user.is_superuser or request.user == blog.writer:
                return super().dispatch(request, *args, **kwargs)
            else:
                raise PermissionDenied("شما اجازه دسترسی ندارید.")
        raise Http404("صفحه مورد نظر یافت نشد.")
        
    def get(self, request, *args, **kwargs):
        blog = get_object_or_404(BlogPost, pk=kwargs['pk'])
        form = self.form_class(instance=blog)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        blog = get_object_or_404(BlogPost, pk=kwargs['pk'])
        form = self.form_class(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            form.save()
            messages.success(request, "بلاگ با موفقیت به‌روزرسانی شد.")
            return redirect('blog:blog')
        messages.error(request, "خطا در به‌روزرسانی بلاگ. لطفاً دوباره تلاش کنید.")
        return render(request, self.template_name, {'form': form})
    
class DeleteBlogView(View):
    template_name = 'blog/delete_blog.html'

    def dispatch(self, request, *args, **kwargs):
        blog = get_object_or_404(BlogPost, pk=kwargs['pk'])
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            if request.user.is_superuser or request.user == blog.writer:
                return super().dispatch(request, *args, **kwargs)
            else:
                raise PermissionDenied("شما اجازه دسترسی ندارید.")
        raise Http404("صفحه مورد نظر یافت نشد.")

    def get(self, request, *args, **kwargs):
        blog = get_object_or_404(BlogPost, pk=kwargs['pk'])
        return render(request, self.template_name, {'blog': blog})

    def post(self, request, *args, **kwargs):
        blog = get_object_or_404(BlogPost, pk=kwargs['pk'])
        blog.delete()
        messages.success(request, "بلاگ با موفقیت حذف شد.")
        return redirect('blog:blog')
