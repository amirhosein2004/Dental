from django.views import View
from django.shortcuts import render, redirect
from .models import BlogPost
from django.http import Http404, HttpResponse
from .forms import BlogPostForm
from django.contrib import messages

class BlogView(View):

    def get(self, request, *args, **kwargs):
        blogs = BlogPost.objects.all()
        return render(request, 'blog/blog.html', {'blogs': blogs})

class BlogDetailView(View):

    def get(self, request, *args, **kwargs):
        try:
            blog = BlogPost.objects.get(pk=kwargs['pk'])
        except BlogPost.DoesNotExist:
            raise Http404("Blog post not found")
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
            form.save()
            messages.success(request, "بلاگ جدید با موفقیت ایجاد شد.")
            return redirect('blog')
        messages.error(request, "خطا در ایجاد بلاگ. لطفاً دوباره تلاش کنید.")
        return render(request, self.template_name, {'form': form})

class UpdateBlogView(View):

    form_class = BlogPostForm
    template_name = 'blog/update_blog.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
        
    def get(self, request, *args, **kwargs):
        try:
            blog = BlogPost.objects.get(pk=kwargs['pk'])
        except BlogPost.DoesNotExist:
            raise Http404("Blog post not found")
        form = self.form_class(instance=blog)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        try:
            blog = BlogPost.objects.get(pk=kwargs['pk'])
        except BlogPost.DoesNotExist:
            raise Http404("Blog post not found")
        form = self.form_class(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            form.save()
            messages.success(request, "بلاگ با موفقیت به‌روزرسانی شد.")
            return redirect('blog')
        messages.error(request, "خطا در به‌روزرسانی بلاگ. لطفاً دوباره تلاش کنید.")
        return render(request, self.template_name, {'form': form})
    
class DeleteBlogView(View):

    template_name = 'blog/delete_blog.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")

    def get(self, request, *args, **kwargs):
        blog = self.get_blog(kwargs['pk'])
        return render(request, self.template_name, {'blog': blog})

    def post(self, request, *args, **kwargs):
        blog = self.get_blog(kwargs['pk'])
        blog.delete()
        messages.success(request, "بلاگ با موفقیت حذف شد.")
        return redirect('blog')

    def get_blog(self, pk):
        try:
            return BlogPost.objects.get(pk=pk)
        except BlogPost.DoesNotExist:
            raise Http404("Blog post not found")
