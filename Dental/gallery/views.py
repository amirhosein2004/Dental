# Project-specific imports from common_imports
from utils.common_imports import View, render, redirect, get_object_or_404, messages, PermissionDenied, transaction 

from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

# Imports from local models
from .models import Gallery, Image  
from core.models import Category  
from dashboard.models import Doctor  

# Imports from local forms
from .forms import GalleryForm, ImageForm  

# Imports from local filters
from .filters import GalleryFilter  



class GalleryView(RateLimitMixin, View):
    template_name = 'gallery/gallery.html'

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        galleries = Gallery.objects.select_related('category', 'doctor__user').prefetch_related('images')
        gallery_filter = GalleryFilter(request.GET, queryset=galleries)
        context = {'galleries': gallery_filter.qs, 'filter': gallery_filter, 'categories': categories}
        return render(request, self.template_name, context)
    
class AddGalleryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
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
        # else:
        #     messages.error(request, "لطفاً اطلاعات را به درستی وارد کنید")  
        
        context = {
            'gallery_form': gallery_form,
            'image_form': image_form,
        }
        return render(request, self.template_name, context)
    
class UpdateGalleryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    template_name = 'gallery/update_gallery.html'
    form_class_image = ImageForm
    form_class_gallery = GalleryForm

    def dispatch(self, request, *args, **kwargs):
        self.gallery = get_object_or_404(
            Gallery.objects.select_related('doctor__user').prefetch_related('images'),
            pk=kwargs['pk']
        )
        if not(request.user.is_superuser or request.user == self.gallery.doctor.user):
                raise PermissionError("شما فقط می‌توانید گالری‌های خودتان را ویرایش کنید")
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        gallery_form = self.form_class_gallery(instance=self.gallery)  # برای پر کردن فیلدها با مقادیر فعلی
        image_form = self.form_class_image()
        context = {
            'gallery_form': gallery_form,
            'image_form': image_form,
            'gallery': self.gallery,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        gallery_form = self.form_class_gallery(request.POST, instance=self.gallery)  # دریافت فرم گالری
        image_form = self.form_class_image(request.POST, request.FILES)

        if 'add_images' in request.POST:  # وقتی که دکمه "Add Images" زده شود
            if image_form.is_valid():
                images = [
                    Image(gallery=gallery_form, image=img)
                    for img in request.FILES.getlist('image')
                ]
                Image.objects.bulk_create(images)
                messages.success(request, "تصاویر جدید با موفقیت اضافه شدند")
                return redirect('gallery:update_gallery', pk=self.gallery.id)

        if 'delete_all_images' in request.POST:  # وقتی که دکمه "Delete All Images" زده شود
            self.gallery.images.all().delete()  # حذف تمامی تصاویر گالری
            messages.success(request, "تمامی تصاویر گالری حذف شدند")
            return redirect('gallery:update_gallery', pk=self.gallery.id)

        if 'change_category' in request.POST:
            if gallery_form.is_valid():
                gallery_form.save()  # ذخیره تغییرات گالری از جمله تغییر دسته‌بندی
                messages.success(request, "دسته بندی گالری با موفقیت به‌روزرسانی شد")
                return redirect('gallery:update_gallery', pk=self.gallery.id)

        # حذف یا اضافه کردن تصاویر جدید (در صورت انتخاب)
        if 'delete_image' in request.POST:
            image_id = request.POST.get('image_id')
            image = get_object_or_404(Image, id=image_id, gallery=self.gallery)
            image.delete()  # حذف تصویر
            messages.success(request, "تصویر با موفقیت حذف شد")
            return redirect('gallery:update_gallery', pk=self.gallery.id)

        context = {
            'gallery_form': gallery_form,
            'image_form': image_form,
            'gallery': self.gallery,
            'images': self.gallery.images.all()  # ارسال دوباره تصاویر برای نمایش
        }
        return render(request, self.template_name, context)
    
class DeleteGalleryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    template_name = 'gallery/delete_gallery.html'

    def dispatch(self, request, *args, **kwargs):
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