"""Authoring: create, update, delete — a doctor may touch only their own."""
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView

from utils.http.mixins import (
    DoctorOrSuperuserRequiredMixin,
    RateLimitMixin,
    get_doctor_profile,
    require_staff,
    safe_next_url,
    user_owns,
)

from ..forms import BlogPostForm
from ..models import BlogPost
from .common import _blogs_queryset


class CreateBlogView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, SuccessMessageMixin, CreateView):
    model = BlogPost
    form_class = BlogPostForm
    template_name = 'blog/create_blog.html'
    success_url = reverse_lazy('blog:blog_list')
    success_message = "بلاگ جدید با موفقیت ایجاد شد."

    def form_valid(self, form):
        # A superuser who isn't also a doctor has no profile to attribute the
        # post to; surface that instead of raising DoesNotExist.
        doctor = get_doctor_profile(self.request.user)
        if doctor is None:
            messages.error(self.request, "شما به عنوان پزشک ثبت نشده‌اید و نمی‌توانید بلاگ بنویسید")
            return self.form_invalid(form)
        form.instance.writer = doctor
        return super().form_valid(form)


class _BlogOwnerAccessMixin(DoctorOrSuperuserRequiredMixin):
    """
    Fetch the blog post once, enforce ownership, and re-use it downstream.

    ``self.object`` is populated in ``dispatch`` so subsequent calls from
    Django's UpdateView/DeleteView flow use the cached instance instead of
    re-hitting the DB via a second ``get_queryset() + filter`` round-trip.
    """

    def get_queryset(self):
        return _blogs_queryset()

    def get_object(self, queryset=None):
        return self.object

    def dispatch(self, request, *args, **kwargs):
        # Staff gate first — this override precedes DoctorOrSuperuserRequiredMixin
        # in the MRO, so an ownership check placed first would 403 anonymous
        # users and leak that the post id exists.
        require_staff(request)
        self.object = get_object_or_404(self.get_queryset(), pk=kwargs['pk'])
        if not user_owns(request.user, self.object.writer):
            raise PermissionDenied("شما فقط می‌توانید بلاگ‌های خودتان را ویرایش کنید")
        return super().dispatch(request, *args, **kwargs)


class UpdateBlogView(_BlogOwnerAccessMixin, RateLimitMixin, SuccessMessageMixin, UpdateView):
    model = BlogPost
    form_class = BlogPostForm
    template_name = 'blog/update_blog.html'
    success_message = "بلاگ با موفقیت به‌روزرسانی شد"

    def get_success_url(self):
        return reverse('blog:blog_detail', kwargs={'slug': self.object.slug})


class DeleteBlogView(_BlogOwnerAccessMixin, RateLimitMixin, SuccessMessageMixin, DeleteView):
    model = BlogPost
    template_name = 'blog/delete_blog.html'
    success_message = "بلاگ با موفقیت حذف شد"

    def get_success_url(self):
        return safe_next_url(self.request, reverse('blog:blog_list'))
