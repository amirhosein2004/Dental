from django.views import View
from django.shortcuts import render, redirect
from django.http import Http404
from django.contrib import messages
from .models import Gallery, Image
from core.models import Category
from .forms import GalleryForm, ImageForm
from .filters import GalleryFilter


class GalleryView(View):
    template_name = 'gallery/gallery.html'

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        galleries = Gallery.objects.all()
        gallery_filter = GalleryFilter(request.GET, queryset=galleries)
        return render(request, self.template_name, {'galleries': gallery_filter.qs, 'filter': gallery_filter, 'categories': categories})
    
class AddGalleryView(View):
    template_name = 'gallery/add_gallery.html'
    form_class_image = ImageForm
    form_class_gallery = GalleryForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")

    def get(self, request, *args, **kwargs):
        gallery_form = self.form_class_gallery()
        image_form = self.form_class_image()
        return render(request, self.template_name, {
            'gallery_form': gallery_form,
            'image_form': image_form,})
        
    def post(self, request, *args, **kwargs):
        gallery_form = self.form_class_gallery(request.POST)
        image_form = self.form_class_image(request.POST, request.FILES)

        if gallery_form.is_valid():
            gallery = gallery_form.save()
        
            images = request.FILES.getlist('image')  
            for img in images:
                Image.objects.create(gallery=gallery, image=img)  
            return redirect('gallery:gallery')

        return render(request, self.template_name, {
            'gallery_form': gallery_form,
            'image_form': image_form,
        })
    
class UpdateGalleryView(View):
    template_name = 'gallery/update_gallery.html'
    form_class_image = ImageForm
    form_class_gallery = GalleryForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")

    def get(self, request, *args, **kwargs):
        gallery = Gallery.objects.get(pk=kwargs['pk'])
        gallery_form = self.form_class_gallery(instance=gallery)  # برای پر کردن فیلدها با مقادیر فعلی
        image_form = self.form_class_image()
        images = gallery.images.all()  # گرفتن تصاویر موجود گالری
        return render(request, self.template_name, {
            'gallery_form': gallery_form,
            'image_form': image_form,
            'gallery': gallery,
            'images': images  # ارسال تصاویر به قالب
        })

    def post(self, request, *args, **kwargs):
        gallery = Gallery.objects.get(pk=kwargs['pk'])
        gallery_form = self.form_class_gallery(request.POST, instance=gallery)  # دریافت فرم گالری
        image_form = self.form_class_image(request.POST, request.FILES)

        if 'add_images' in request.POST:  # وقتی که دکمه "Add Images" زده شود
            if image_form.is_valid():
                images = request.FILES.getlist('image')  # دریافت فایل‌های تصویر
                for img in images:
                    Image.objects.create(gallery=gallery, image=img)  # ذخیره تصاویر جدید
                messages.success(request, "تصاویر جدید با موفقیت اضافه شدند.")
                return redirect('gallery:update_gallery', pk=gallery.id)

        if 'delete_all_images' in request.POST:  # وقتی که دکمه "Delete All Images" زده شود
            gallery.images.all().delete()  # حذف تمامی تصاویر گالری
            messages.success(request, "تمامی تصاویر حذف شدند.")
            return redirect('gallery:update_gallery', pk=gallery.id)

        if 'change_category' in request.POST:
            if gallery_form.is_valid():
                gallery = gallery_form.save()  # ذخیره تغییرات گالری از جمله تغییر دسته‌بندی
                messages.success(request, "گالری با موفقیت به‌روزرسانی شد.")
                return redirect('gallery:update_gallery', pk=gallery.id)

        # حذف یا اضافه کردن تصاویر جدید (در صورت انتخاب)
        if 'delete_image' in request.POST:
            image_id = request.POST.get('image_id')
            try:
                image = Image.objects.get(id=image_id, gallery=gallery)
                image.delete()  # حذف تصویر
                messages.success(request, "تصویر با موفقیت حذف شد.")
            except Image.DoesNotExist:
                messages.error(request, "تصویر یافت نشد.")
            return redirect('gallery:update_gallery', pk=gallery.id)

        return render(request, self.template_name, {
            'gallery_form': gallery_form,
            'image_form': image_form,
            'gallery': gallery,
            'images': gallery.images.all()  # ارسال دوباره تصاویر برای نمایش
        })
    
class DeleteGalleryView(View):
    template_name = 'gallery/delete_gallery.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")

    def get(self, request, *args, **kwargs):
        gallery = Gallery.objects.get(pk=kwargs['pk'])
        return render(request, self.template_name, {'gallery': gallery})
    
    def post(self, request, *args, **kwargs):
        gallery = Gallery.objects.get(pk=kwargs['pk'])
        gallery.delete()
        return redirect('gallery:gallery')
    
