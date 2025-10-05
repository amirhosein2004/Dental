# Project-specific imports from common_imports
from utils.common_imports import (
    View, render, redirect,
    get_object_or_404, transaction,
    messages, cache
)

from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

# Imports from local models
from .models import PricingItem

# Imports from local forms
from .forms import PricingItemForm

from utils.cache import get_cache_key


class PricingListView(RateLimitMixin, View):
    """
    Public view to display the pricing list for regular users.
    """
    template_name = 'pricing/pricing_list.html'

    def get(self, request, *args, **kwargs):
        cache_key = get_cache_key(request, cache_view='pricinglistview')
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        pricing_items = PricingItem.objects.all()
        
        context = {
            'pricing_items': pricing_items,
        }
        
        response = render(request, self.template_name, context)
        cache.set(cache_key, response, 3600)  # Cache for 1 hour
        return response


class AddPricingItemView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle adding a new pricing item.
    """
    template_name = 'pricing/add_pricing_item.html'
    form_class = PricingItemForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {
            'form': form,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():                    
                    form.save()
                    
                messages.success(request, "تعرفه جدید با موفقیت اضافه شد")
                return redirect('pricing:pricing_list')
                
            except Exception as e:
                messages.error(request, "متاسفانه خطایی رخ داده است")

        context = {
            'form': form,
        }
        return render(request, self.template_name, context)


class UpdatePricingItemView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle updating an existing pricing item.
    """
    template_name = 'pricing/update_pricing_item.html'
    form_class = PricingItemForm

    def dispatch(self, request, *args, **kwargs):
        """
        update the pricing item.
        """
        self.pricing_item = get_object_or_404(
            PricingItem.objects,
            pk=kwargs['pk']
        )
        
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(instance=self.pricing_item)
        context = {
            'form': form,
            'pricing_item': self.pricing_item,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, instance=self.pricing_item)

        if form.is_valid():
            form.save()
            messages.success(request, "تعرفه با موفقیت به‌روزرسانی شد")
            return redirect('pricing:pricing_list')

        context = {
            'form': form,
            'pricing_item': self.pricing_item,
        }
        return render(request, self.template_name, context)


class DeletePricingItemView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle deleting a pricing item.
    """
    template_name = 'pricing/delete_pricing_item.html'

    def dispatch(self, request, *args, **kwargs):
        """
        delete the pricing item.
        """
        self.pricing_item = get_object_or_404(PricingItem, pk=kwargs['pk'])
        
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.pricing_item.delete()
        messages.success(request, "تعرفه با موفقیت حذف شد")
        next_url = request.POST.get('next', 'pricing:pricing_list')
        return redirect(next_url)
