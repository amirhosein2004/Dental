"""Staff side: create a gallery, add or remove images, delete it."""
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from utils.http.mixins import (
    DoctorOrSuperuserRequiredMixin,
    RateLimitMixin,
    get_doctor_profile,
    safe_next_url,
)

from ..forms import GalleryForm, ImageForm
from ..models import Gallery, Image
from .common import _GalleryOwnerAccessMixin


MAX_IMAGES_PER_UPLOAD = 30


def _too_many_images(request):
    """Return an error message when the POST carries more files than allowed."""
    count = len(request.FILES.getlist('image'))
    if count > MAX_IMAGES_PER_UPLOAD:
        return (
            f'{count} تصویر انتخاب شده و سقف هر بار آپلود '
            f'{MAX_IMAGES_PER_UPLOAD} تصویر است. لطفاً در چند مرحله آپلود کنید.'
        )
    return None


class AddGalleryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """Create a new gallery with an initial batch of images."""
    template_name = 'gallery/add_gallery.html'
    form_class_image = ImageForm
    form_class_gallery = GalleryForm

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'gallery_form': self.form_class_gallery(),
            'image_form': self.form_class_image(),
        })

    def post(self, request, *args, **kwargs):
        too_many = _too_many_images(request)
        if too_many:
            messages.error(request, too_many)
            return redirect('gallery:add_gallery')

        gallery_form = self.form_class_gallery(request.POST)
        image_form = self.form_class_image(request.POST, request.FILES)

        if gallery_form.is_valid() and image_form.is_valid():
            # A superuser who isn't also a doctor has no profile to attribute
            # the gallery to; surface that instead of raising DoesNotExist.
            doctor = get_doctor_profile(request.user)
            if doctor is None:
                messages.error(request, "شما به‌عنوان پزشک ثبت نشده‌اید و نمی‌توانید گالری اضافه کنید")
            else:
                try:
                    with transaction.atomic():
                        gallery = gallery_form.save(commit=False)
                        gallery.doctor = doctor
                        gallery.save()
                        # Per-image save (not bulk_create) so ``Image.save`` runs
                        # ``full_clean`` and ``validate_image`` on every upload;
                        # bulk_create skips model save hooks and lets bad files
                        # through the ``ImageForm`` single-field check.
                        for uploaded in request.FILES.getlist('image'):
                            Image.objects.create(gallery=gallery, image=uploaded)
                except ValidationError as exc:
                    messages.error(request, exc.messages[0] if exc.messages else "خطا در آپلود تصاویر")
                else:
                    messages.success(request, "گالری با موفقیت ایجاد شد")
                    return redirect('gallery:gallery_list')

        return render(request, self.template_name, {
            'gallery_form': gallery_form,
            'image_form': image_form,
        })


class UpdateGalleryView(_GalleryOwnerAccessMixin, RateLimitMixin, View):
    """
    Render the update page. All mutating actions live in dedicated views
    (:class:`UpdateGalleryCategoryView`, :class:`AddGalleryImagesView`,
    :class:`DeleteGalleryImageView`, :class:`ClearGalleryImagesView`) so URLs
    map 1-to-1 to actions instead of dispatching on POST button names.
    """
    template_name = 'gallery/update_gallery.html'
    gallery_queryset = Gallery.objects.select_related('doctor__user').prefetch_related('images')

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'gallery_form': GalleryForm(instance=self.gallery),
            'image_form': ImageForm(),
            'gallery': self.gallery,
        })


class UpdateGalleryCategoryView(_GalleryOwnerAccessMixin, RateLimitMixin, View):
    """POST: change the gallery's category."""

    def post(self, request, *args, **kwargs):
        form = GalleryForm(request.POST, instance=self.gallery)
        if form.is_valid():
            form.save()
            messages.success(request, "دسته بندی گالری با موفقیت به‌روزرسانی شد")
        else:
            messages.error(request, "خطا در به‌روزرسانی دسته بندی")
        return redirect('gallery:update_gallery', pk=self.gallery.pk)


class AddGalleryImagesView(_GalleryOwnerAccessMixin, RateLimitMixin, View):
    """POST: append new images to an existing gallery."""

    def post(self, request, *args, **kwargs):
        too_many = _too_many_images(request)
        if too_many:
            messages.error(request, too_many)
            return redirect('gallery:update_gallery', pk=self.gallery.pk)

        image_form = ImageForm(request.POST, request.FILES)
        if not image_form.is_valid():
            messages.error(request, "خطا در آپلود تصاویر")
            return redirect('gallery:update_gallery', pk=self.gallery.pk)

        try:
            with transaction.atomic():
                for uploaded in request.FILES.getlist('image'):
                    Image.objects.create(gallery=self.gallery, image=uploaded)
        except ValidationError as exc:
            messages.error(request, exc.messages[0] if exc.messages else "خطا در آپلود تصاویر")
        else:
            messages.success(request, "تصاویر جدید با موفقیت اضافه شدند")

        return redirect('gallery:update_gallery', pk=self.gallery.pk)


class DeleteGalleryImageView(_GalleryOwnerAccessMixin, RateLimitMixin, View):
    """POST: delete a single image belonging to the gallery."""

    def post(self, request, *args, **kwargs):
        image = get_object_or_404(Image, pk=kwargs['image_id'], gallery=self.gallery)
        image.delete()
        messages.success(request, "تصویر با موفقیت حذف شد")
        return redirect('gallery:update_gallery', pk=self.gallery.pk)


class ClearGalleryImagesView(_GalleryOwnerAccessMixin, RateLimitMixin, View):
    """POST: remove every image from the gallery."""

    def post(self, request, *args, **kwargs):
        self.gallery.images.all().delete()
        messages.success(request, "تمامی تصاویر گالری حذف شدند")
        return redirect('gallery:update_gallery', pk=self.gallery.pk)


class DeleteGalleryView(_GalleryOwnerAccessMixin, RateLimitMixin, View):
    """POST: delete the entire gallery."""
    template_name = 'gallery/delete_gallery.html'

    def post(self, request, *args, **kwargs):
        self.gallery.delete()
        messages.success(request, "گالری با موفقیت حذف شد")
        return redirect(safe_next_url(request, reverse('gallery:gallery_list')))
