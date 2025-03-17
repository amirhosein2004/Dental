# Project-specific imports from common_imports
from utils.common_imports import (
    View, render,
    redirect, get_object_or_404,
    messages, ValidationError,
    PermissionDenied, cache_page,
    method_decorator,
)

from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin
# Imports from local models, forms, and filters
from .models import BlogPost  
from .forms import BlogPostForm  
from .filters import BlogPostFilter  

# Imports from external applications
from dashboard.models import Doctor  
from utils.cache import get_cache_key
 

class BlogView(View):
    """
    View to display a list of blog posts with filtering options.
    """
    filter_class = BlogPostFilter
    template_name = 'blog/blog.html'

    @method_decorator(lambda func: cache_page(86400, key_prefix=lambda request: get_cache_key(request, cache_view='blogview'))(func))  # Cache for 24 hours
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to display the list of blog posts.
        """
        blogs = BlogPost.objects.select_related('writer').prefetch_related('categories').all()
        blog_filter = self.filter_class(request.GET, queryset=blogs)
        context = {
            'blogs': blog_filter.qs,  # Filtered blog posts
            'filter': blog_filter,    # Filter object
        }
        return render(request, self.template_name, context)

class BlogDetailView(View):
    """
    View to display the details of a single blog post.
    """

    @method_decorator(lambda func: cache_page(86400, key_prefix=lambda request: get_cache_key(request, cache_view='blogdetailview'))(func))   # Cache for 24 hours
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

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to display the blog post deletion confirmation.
        """
        context = {'blog': self.blog}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to delete the blog post.
        """
        self.blog.delete()
        messages.success(request, "بلاگ با موفقیت حذف شد")
        return redirect('blog:blog_list')