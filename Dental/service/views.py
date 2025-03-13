from utils.common_imports import View, render, redirect, messages, get_object_or_404, ValidationError
from .models import Service
from .forms import ServiceForm
from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin


class ServiceView(View):
    template_name = 'service/service.html'

    def get(self, request, *args, **kwargs):
        services = Service.objects.all()
        context = {'services': services}
        return render(request, self.template_name, context)
    
class ServiceDetailView(View):
    template_name = 'service/service_detail.html'

    def get(self, request, *args, **kwargs):
        service = get_object_or_404(Service, slug=kwargs['slug'])
        context = {'service': service}
        return render(request, 'service/service_detail.html', context)
    
class AddServiceView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
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
                # نمایش پیام خطای مرتبط با ترجمه عنوان یا سایر خطاهای مدل
                messages.error(request, ve.message)
        # else:
        #     messages.error(request, "خطا در ایجاد سرویس. لطفاً دوباره تلاش کنید")
        return render(request, self.template_name, context)

class UpdateServiceView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    template_name = 'service/update_service.html'
    form_class = ServiceForm
    
    def dispatch(self, request, *args, **kwargs):
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
                # نمایش پیام خطای مرتبط با ترجمه عنوان یا سایر خطاهای مدل
                messages.error(request, ve.message)
        # else:
        #     messages.error(request, "خطا در ویرایش سرویس. لطفاً دوباره تلاش کنید.")
        return render(request, self.template_name, context)

class RemoveServiceView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    template_name = 'service/remove_service.html'

    def dispatch(self, request, *args, **kwargs):
        self.service = get_object_or_404(Service, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {'service': self.service}
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        self.service.delete()
        messages.success(request, "سرویس با موفقیت حذف شد")
        return redirect('service:service_list')