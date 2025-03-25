# Project-specific imports from common_imports
from utils.common_imports import (View, render, redirect,
        get_object_or_404, transaction,
        messages, PermissionDenied,
        method_decorator, cache_page
    ) 

from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

# Imports from local models
from .models import Gallery, Image 
from core.models import Category  
from dashboard.models import Doctor  

# Imports from local forms
from .forms import GalleryForm, ImageForm  

# Imports from local filters
from .filters import GalleryFilter  

from utils.cache import get_cache_key


class GalleryView(RateLimitMixin, View):
    """
    View to display the gallery page with a list of galleries and a filter.
    """
    template_name = 'gallery/gallery.html'

    @method_decorator(lambda func: cache_page(21600, key_prefix=lambda request: get_cache_key(request, cache_view='galleryview'))(func))   # Cache for 6 hours
    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        galleries = Gallery.objects.select_related('category', 'doctor__user').prefetch_related('images')
        gallery_filter = GalleryFilter(request.GET, queryset=galleries)
        context = {'galleries': gallery_filter.qs, 'filter': gallery_filter, 'categories': categories}
        return render(request, self.template_name, context)
    
class AddGalleryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle adding a new gallery.
    """
    template_name = 'gallery/add_gallery.html'
    form_class_image = ImageForm
    form_class_gallery = GalleryForm

    def get(self, request, *args, **kwargs):
        gallery_form = self.form_class_gallery()
        image_form = self.form_class_image()
        context = {
            'gallery_form': gallery_form,
            'image_form': image_form,
        }
        return render(request, self.template_name, context)
        
    def post(self, request, *args, **kwargs):
        gallery_form = self.form_class_gallery(request.POST)
        image_form = self.form_class_image(request.POST, request.FILES)

        if gallery_form.is_valid() and image_form.is_valid():
            try:
                with transaction.atomic():
                    gallery = gallery_form.save(commit=False)
                    doctor = Doctor.objects.get(user=request.user)
                    gallery.doctor = doctor
                    gallery.save()
                    
                    images = [
                        Image(gallery=gallery, image=img)
                        for img in request.FILES.getlist('image')
                    ]
                    Image.objects.bulk_create(images)
                messages.success(request, "گالری با موفقیت ایجاد شد")
                return redirect('gallery:gallery_list')
            except Doctor.DoesNotExist:
                messages.error(request, "شما به‌عنوان پزشک ثبت نشده‌اید و نمی‌توانید گالری اضافه کنید")
        
        context = {
            'gallery_form': gallery_form,
            'image_form': image_form,
        }
        return render(request, self.template_name, context)
    
class UpdateGalleryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle updating an existing gallery.
    """
    template_name = 'gallery/update_gallery.html'
    form_class_image = ImageForm
    form_class_gallery = GalleryForm

    def dispatch(self, request, *args, **kwargs):
        """
        Ensure the user has permission to update the gallery.
        """
        self.gallery = get_object_or_404(
            Gallery.objects.select_related('doctor__user').prefetch_related('images'),
            pk=kwargs['pk']
        )
        if not(request.user.is_superuser or request.user == self.gallery.doctor.user):
            raise PermissionDenied("شما فقط می‌توانید گالری‌های خودتان را ویرایش کنید")
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        gallery_form = self.form_class_gallery(instance=self.gallery)
        image_form = self.form_class_image()
        context = {
            'gallery_form': gallery_form,
            'image_form': image_form,
            'gallery': self.gallery,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        gallery_form = self.form_class_gallery(request.POST, instance=self.gallery)
        image_form = self.form_class_image(request.POST, request.FILES)

        if 'add_images' in request.POST:
            if image_form.is_valid():
                images = [
                    Image(gallery=gallery_form, image=img)
                    for img in request.FILES.getlist('image')
                ]
                Image.objects.bulk_create(images)
                messages.success(request, "تصاویر جدید با موفقیت اضافه شدند")
                return redirect('gallery:update_gallery', pk=self.gallery.id)

        if 'delete_all_images' in request.POST:
            self.gallery.images.all().delete()
            messages.success(request, "تمامی تصاویر گالری حذف شدند")
            return redirect('gallery:update_gallery', pk=self.gallery.id)

        if 'change_category' in request.POST:
            if gallery_form.is_valid():
                gallery_form.save()
                messages.success(request, "دسته بندی گالری با موفقیت به‌روزرسانی شد")
                return redirect('gallery:update_gallery', pk=self.gallery.id)

        if 'delete_image' in request.POST:
            image_id = request.POST.get('image_id')
            image = get_object_or_404(Image, id=image_id, gallery=self.gallery)
            image.delete()
            messages.success(request, "تصویر با موفقیت حذف شد")
            return redirect('gallery:update_gallery', pk=self.gallery.id)

        context = {
            'gallery_form': gallery_form,
            'image_form': image_form,
            'gallery': self.gallery,
            'images': self.gallery.images.all()
        }
        return render(request, self.template_name, context)
    
class DeleteGalleryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle deleting a gallery.
    """
    template_name = 'gallery/delete_gallery.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Ensure the user has permission to delete the gallery.
        """
        self.gallery = get_object_or_404(Gallery, pk=kwargs['pk'])
        if not(request.user.is_superuser or request.user == self.gallery.doctor.user):
            raise PermissionDenied("شما فقط می‌توانید گالری‌های خودتان را حذف کنید")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {'gallery': self.gallery}
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        self.gallery.delete()
        return redirect('gallery:gallery_list')