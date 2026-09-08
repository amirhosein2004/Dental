"""Staff screens: tariff items and the categories they group into."""
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, UpdateView

from utils.http.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin, safe_next_url

from ..forms import PricingCategoryForm, PricingItemForm
from ..models import PricingCategory, PricingItem


class AddPricingItemView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, SuccessMessageMixin, CreateView):
    model = PricingItem
    form_class = PricingItemForm
    template_name = 'pricing/add_pricing_item.html'
    success_url = reverse_lazy('pricing:pricing_list')
    success_message = "تعرفه جدید با موفقیت اضافه شد"


class UpdatePricingItemView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = PricingItem
    form_class = PricingItemForm
    template_name = 'pricing/update_pricing_item.html'
    context_object_name = 'pricing_item'
    success_url = reverse_lazy('pricing:pricing_list')
    success_message = "تعرفه با موفقیت به‌روزرسانی شد"


class DeletePricingItemView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, SuccessMessageMixin, DeleteView):
    model = PricingItem
    template_name = 'pricing/delete_pricing_item.html'
    context_object_name = 'pricing_item'
    success_url = reverse_lazy('pricing:pricing_list')
    success_message = "تعرفه با موفقیت حذف شد"

    def get_success_url(self):
        return safe_next_url(self.request, str(self.success_url))


# ============================================================================
# Category CRUD (staff-only)
# ============================================================================

class PricingCategoryListView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """Manage pricing categories — list + inline add form on one page."""
    template_name = 'pricing/pricing_category_list.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'categories': PricingCategory.objects.all(),
            'form': PricingCategoryForm(),
        })


class AddPricingCategoryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, SuccessMessageMixin, CreateView):
    model = PricingCategory
    form_class = PricingCategoryForm
    template_name = 'pricing/pricing_category_list.html'
    success_url = reverse_lazy('pricing:pricing_category_list')
    success_message = "دسته‌بندی جدید با موفقیت اضافه شد"

    def get(self, request, *args, **kwargs):
        # Creation happens through the list-page form; direct GETs land there.
        from django.shortcuts import redirect
        return redirect('pricing:pricing_category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = PricingCategory.objects.all()
        return context


class UpdatePricingCategoryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = PricingCategory
    form_class = PricingCategoryForm
    template_name = 'pricing/pricing_category_update.html'
    context_object_name = 'category'
    success_url = reverse_lazy('pricing:pricing_category_list')
    success_message = "دسته‌بندی با موفقیت به‌روزرسانی شد"


class DeletePricingCategoryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, SuccessMessageMixin, DeleteView):
    model = PricingCategory
    success_url = reverse_lazy('pricing:pricing_category_list')
    success_message = "دسته‌بندی با موفقیت حذف شد"

    def get(self, request, *args, **kwargs):
        from django.shortcuts import redirect
        return redirect('pricing:pricing_category_list')
