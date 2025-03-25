from utils.common_imports import (
    View, render, redirect, messages, get_object_or_404,
    ValidationError, method_decorator, cache_page
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

    @method_decorator(lambda func: cache_page(86400, key_prefix=lambda request: get_cache_key(request, cache_view='serviceview'))(func))  # Cache for 24 hours
    def get(self, request, *args, **kwargs):
        services = Service.objects.all()
        context = {'services': services}
        return render(request, self.template_name, context)

class ServiceDetailView(View):
    """
    View to display the details of a specific service.
    """
    template_name = 'service/service_detail.html'

    @method_decorator(lambda func: cache_page(86400, key_prefix=lambda request: get_cache_key(request, cache_view='servicedetailview'))(func))   # Cache for 24 hours
    def get(self, request, *args, **kwargs):
        service = get_object_or_404(Service, slug=kwargs['slug'])
        context = {'service': service}
        return render(request, 'service/service_detail.html', context)

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
            try:
                form.save()
                messages.success(request, "سرویس جدید با موفقیت ایجاد شد")
                return redirect('service:service_list')
            except ValidationError as ve:
                # Display error message related to title translation or other model errors
                messages.error(request, ve.message)
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
            try:
                form.save()
                messages.success(request, "سرویس با موفقیت ویرایش شد")
                return redirect('service:service_detail', slug=self.service.slug)
            except ValidationError as ve:
                # Display error message related to title translation or other model errors
                messages.error(request, ve.message)
        return render(request, self.template_name, context)

class RemoveServiceView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to remove an existing service.
    """
    template_name = 'service/remove_service.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to get the service object before handling the request.
        """
        self.service = get_object_or_404(Service, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {'service': self.service}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        self.service.delete()
        messages.success(request, "سرویس با موفقیت حذف شد")
        return redirect('service:service_list')