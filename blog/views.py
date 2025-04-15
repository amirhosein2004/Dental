# Project-specific imports from common_imports
from utils.common_imports import (
    View, render, cache,
    redirect, get_object_or_404,
    messages, ValidationError,
    PermissionDenied, JsonResponse
)

from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin
# Imports from local models, forms, and filters
from .models import BlogPost  
from .forms import BlogPostForm  
from .filters import BlogPostFilter  

# Imports from external applications
from dashboard.models import Doctor  
from utils.cache import get_cache_key
from django.core.paginator import Paginator


class BlogView(View):
    """
    View to display a list of blog posts with filtering options.
    """
    filter_class = BlogPostFilter
    template_name = 'blog/blog.html'

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to display the list of blog posts.
        """
        cache_key = get_cache_key(request, cache_view='blogview')
        cached_data = cache.get(cache_key)  # بررسی کش قبل از اجرای کوئری‌ها
        if cached_data:
            return cached_data
        
        blogs = BlogPost.objects.select_related('writer').prefetch_related('categories').all()
        blog_filter = self.filter_class(request.GET, queryset=blogs)

        context = {
            'blogs': blog_filter.qs[:3],  # Paginated blog posts
            'filter': blog_filter,    # Filter object
        }
        
        response = render(request, self.template_name, context)
        cache.set(cache_key, response, 86400)  # ذخیره کش برای 24 ساعت
        return response
    
class LoadMoreBlogsView(View):
    """
    View to handle loading more blog posts via AJAX requests.
    """
    filter_class = BlogPostFilter

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to load more blog posts.
        """
        # Check if the request is an AJAX request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Get the offset value from the request and set the number of posts to load per request
            offset = int(request.GET.get('offset', 0))
            limit = 3  # Number of posts to load per request
            
            # Apply filters sent from the form
            blogs = BlogPost.objects.select_related('writer').prefetch_related('categories').all()
            blog_filter = self.filter_class(request.GET, queryset=blogs)

            # Retrieve more posts based on the offset and limit
            more_blogs = blog_filter.qs[offset:offset + limit]
            
            # Prepare the blog post data to send to the client
            blogs_data = [
                {
                    'title': blog.title,  
                    'writer': f"{blog.writer.user.get_full_name}",  
                    'image': blog.image.url, 
                    'slug': blog.slug,  
                    'categories': [cat.name for cat in blog.categories.all()[:3]]  
                } for blog in more_blogs
            ]
            
            return JsonResponse({
                'blogs': blogs_data,  
                'has_more': len(more_blogs) == limit  
            })
        
        return JsonResponse({'error': 'Invalid request'}, status=400)

class BlogDetailView(View):
    """
    View to display the details of a single blog post.
    """

    # Cache for 24 hours
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to display the details of a blog post.
        """
        blog = get_object_or_404(
            BlogPost.objects.select_related('writer').prefetch_related('categories'),
            slug=kwargs['slug']
        )
        context = {'blog': blog}
        return render(request, 'blog/blog_detail.html', context)
    
class CreateBlogView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle the creation of a new blog post.
    """
    form_class = BlogPostForm
    template_name = 'blog/create_blog.html'
        
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to display the blog post creation form.
        """
        form = self.form_class()
        context = {'form': form}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to create a new blog post.
        """
        form = self.form_class(request.POST, request.FILES)
        context = {'form': form}
        if form.is_valid():
            try:
                blog = form.save(commit=False)
                doctor = Doctor.objects.get(user=request.user)  # Optimize query
                blog.writer = doctor
                blog.save()
                form.save_m2m()  # Save ManyToMany relationships
                messages.success(request, "بلاگ جدید با موفقیت ایجاد شد.")
                return redirect('blog:blog_list')
            except Doctor.DoesNotExist:
                messages.error(request, "شما به عنوان پزشک ثبت نشده‌اید و نمی‌توانید بلاگ بنویسید")
            except ValidationError as ve:
                messages.error(request, ve.message)
        return render(request, self.template_name, context) 

class UpdateBlogView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle the update of an existing blog post.
    """
    form_class = BlogPostForm
    template_name = 'blog/update_blog.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch method to check permissions before processing the request.
        """
        self.blog = get_object_or_404(
            BlogPost.objects.select_related('writer').prefetch_related('categories'),
            pk=kwargs['pk']
        )
        if not (request.user.is_superuser or request.user == self.blog.writer.user):
            raise PermissionDenied("شما فقط می‌توانید بلاگ‌های خودتان را ویرایش کنید")
        return super().dispatch(request, *args, **kwargs)
        
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to display the blog post update form.
        """
        form = self.form_class(instance=self.blog)
        context = {'form': form}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to update an existing blog post.
        """
        form = self.form_class(request.POST, request.FILES, instance=self.blog)
        context = {'form': form}
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "بلاگ با موفقیت به‌روزرسانی شد")
                return redirect('blog:blog_detail', slug=self.blog.slug)
            except ValidationError as ve:
                messages.error(request, ve.message)
        return render(request, self.template_name, context)
    
class DeleteBlogView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle the deletion of a blog post.
    """
    template_name = 'blog/delete_blog.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch method to check permissions before processing the request.
        """
        self.blog = get_object_or_404(
            BlogPost.objects.select_related('writer'),  # No need to prefetch categories
            pk=kwargs['pk']
        )
        if not (request.user.is_superuser or request.user == self.blog.writer.user):
            raise PermissionDenied("شما فقط می‌توانید بلاگ‌های خودتان را حذف کنید")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to delete the blog post.
        """
        self.blog.delete()
        messages.success(request, "بلاگ با موفقیت حذف شد")
        next_url = request.POST.get('next', 'blog:blog_list')  # برای وقتی کی میخواهیم ار داشبورد حذف کنیم به داشبورد ریدایرکت شویم
        return redirect(next_url)