from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView

from apps.core.forms import CategoryForm
from apps.core.models import Category
from utils.http.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


class CategoryView(DoctorOrSuperuserRequiredMixin, View):
    """Render the category management page (list + inline form)."""
    template_name = 'core/category.html'
    form_class = CategoryForm

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'categories': Category.objects.all(),
            'form': self.form_class(),
        })


class AddCategoryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'core/category.html'
    success_url = reverse_lazy('core:category')
    success_message = "دسته‌بندی جدید با موفقیت ایجاد شد"

    def get(self, request, *args, **kwargs):
        return redirect('core:category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

    def form_invalid(self, form):
        messages.error(self.request, "خطا در ایجاد دسته بندی")
        return super().form_invalid(form)


class UpdateCategoryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    Update endpoint used from both a regular POST and an AJAX handshake.
    AJAX callers get a JSON payload; regular POSTs redirect back to the list.
    """
    form_class = CategoryForm
    template_name = 'core/category.html'

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(Category, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'categories': Category.objects.all(),
            'form': self.form_class(instance=self.category),
        })

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, instance=self.category)
        ajax = _is_ajax(request)

        if form.is_valid():
            category = form.save()
            if ajax:
                return JsonResponse({
                    'success': True,
                    'category_name': category.name,
                    'category_id': category.id,
                })
            messages.success(request, "دسته‌بندی جدید با موفقیت ایجاد شد")
            return redirect('core:category')

        if ajax:
            return JsonResponse({'success': False, 'error': form.errors}, status=400)

        messages.error(request, "خطا در ایجاد دسته بندی")
        return render(request, self.template_name, {
            'categories': Category.objects.all(),
            'form': form,
        })


class RemoveCategoryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('core:category')
    success_message = "دسته‌بندی با موفقیت حذف شد"

    def get(self, request, *args, **kwargs):
        return redirect('core:category')
