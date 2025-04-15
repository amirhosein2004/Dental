from utils.common_imports import (
    View, render, redirect, messages, get_object_or_404,
    cache
)
from .models import Service
from .forms import ServiceForm
from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin
from utils.cache import get_cache_key

class ServiceView(View):
    """
    View to list all services.
    """
    template_name = 'service/service.html'

    def get(self, request, *args, **kwargs):
        cache_key = get_cache_key(request, cache_view='serviceview')
        cached_data = cache.get(cache_key)  # بررسی کش قبل از اجرای کوئری‌ها
        if cached_data:
            return cached_data
        
        services = Service.objects.all()
        context = {'services': services}

        response = render(request, self.template_name, context)
        cache.set(cache_key, response, 86400)  # ذخیره کش برای 24 ساعت
        return response

class AddServiceView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to add a new service.
    """
    template_name = 'service/add_service.html'
    form_class = ServiceForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {'form': form}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        context = {'form': form}
        if form.is_valid():
            form.save()
            messages.success(request, "سرویس جدید با موفقیت ایجاد شد")
            return redirect('service:service_list')
        return render(request, self.template_name, context)

class UpdateServiceView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to update an existing service.
    """
    template_name = 'service/update_service.html'
    form_class = ServiceForm

    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to get the service object before handling the request.
        """
        self.service = get_object_or_404(Service, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(instance=self.service)
        context = {'form': form, 'service': self.service}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES, instance=self.service)
        context = {'form': form, 'service': self.service}
        if form.is_valid():
            form.save()
            messages.success(request, "سرویس با موفقیت ویرایش شد")
            return redirect('service:service_list')
        return render(request, self.template_name, context)

class RemoveServiceView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to remove an existing service.
    """
    template_name = 'service/remove_service.html'

    def post(self, request, *args, **kwargs):
        get_object_or_404(Service, pk=kwargs['pk']).delete()
        messages.success(request, "سرویس با موفقیت حذف شد")
        return redirect('service:service_list')