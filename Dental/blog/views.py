# Project-specific imports from common_imports
from utils.common_imports import View, render, redirect, get_object_or_404, Http404, messages, ValidationError, PermissionDenied  

from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin
# Imports from local models, forms, and filters
from .models import BlogPost  
from .forms import BlogPostForm  
from .filters import BlogPostFilter  

# Imports from external applications
from dashboard.models import Doctor  
 

class BlogView(View):
    filter_class = BlogPostFilter
    template_name = 'blog/blog.html'

    def get(self, request, *args, **kwargs):
        blogs = BlogPost.objects.all()
        blog_filter = self.filter_class(request.GET, queryset=blogs)
        context = {
        'blogs': blog_filter.qs,  # فیلتر شده‌ها
        'filter': blog_filter,    # فیلتر خود
        }
        return render(request, self.template_name, context)

class BlogDetailView(View):

    def get(self, request, *args, **kwargs):
        blog = get_object_or_404(
            BlogPost.objects.select_related('writer').prefetch_related('categories'),
            slug=kwargs['slug']
        )
        context = {'blog': blog}
        return render(request, 'blog/blog_detail.html', context)
    
class CreateBlogView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    form_class = BlogPostForm
    template_name = 'blog/create_blog.html'
        
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {'form': form}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        context = {'form': form}
        if form.is_valid():

            try:
                blog = form.save(commit=False)
                doctor = Doctor.objects.get(user=request.user)  # بهینه‌سازی کوئری
                blog.writer = doctor
                blog.save()
                form.save_m2m()  # ذخیره ارتباطات ManyToMany
                messages.success(request, "بلاگ جدید با موفقیت ایجاد شد.")
                return redirect('blog:blog_list')
            
            except Doctor.DoesNotExist:
                messages.error(request, "شما به عنوان پزشک ثبت نشده‌اید و نمی‌توانید بلاگ بنویسید")
            except ValidationError as ve:
                messages.error(request, ve.message)
        # else:
        #     messages.error(request, "خطا در ایجاد بلاگ. لطفاً اطلاعات را بررسی کنید")
        return render(request, self.template_name, context) 

class UpdateBlogView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    form_class = BlogPostForm
    template_name = 'blog/update_blog.html'

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_superuser or request.user == self.blog.writer.user):
            raise PermissionDenied("شما فقط می‌توانید بلاگ‌های خودتان را ویرایش کنید")
        
        self.blog = get_object_or_404(
            BlogPost.objects.select_related('writer').prefetch_related('categories'),
            pk=kwargs['pk']
        )

        return super().dispatch(request, *args, **kwargs)
        
    def get(self, request, *args, **kwargs):
        form = self.form_class(instance=self.blog)
        context = {'form': form}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES, instance=self.blog)
        context = {'form': form}
        if form.is_valid():

            try:
                form.save()
                messages.success(request, "بلاگ با موفقیت به‌روزرسانی شد")
                return redirect('blog:blog_detail', slug=self.blog.slug)
            
            except ValidationError as ve:
                # نمایش پیام خطای مرتبط با ترجمه عنوان یا سایر خطاهای مدل
                messages.error(request, ve.message)
        # else:
        #     messages.error(request, "خطا در به‌روزرسانی بلاگ. لطفاً اطلاعات را بررسی کنید")
        return render(request, self.template_name, context)
    
class DeleteBlogView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    template_name = 'blog/delete_blog.html'

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_superuser or request.user == self.blog.writer.user):
            raise PermissionDenied("شما فقط می‌توانید بلاگ‌های خودتان را حذف کنید")
        
        self.blog = get_object_or_404(
            BlogPost.objects.select_related('writer'),  # categories لازم نیست
            pk=kwargs['pk']
        )

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {'blog': self.blog}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        self.blog.delete()
        messages.success(request, "بلاگ با موفقیت حذف شد")
        return redirect('blog:blog_list')