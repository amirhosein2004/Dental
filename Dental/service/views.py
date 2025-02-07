from django.views import View
from django.shortcuts import render, redirect
from django.http import Http404
from django.contrib import messages
from .models import Service
from .forms import ServiceForm

class ServiceView(View):
    template_name = 'service/service.html'

    def get(self, request, *args, **kwargs):
        services = Service.objects.all()
        return render(request, self.template_name, {'services': services})
    
class ServiceDetailView(View):
    template_name = 'service/service_detail.html'

    def get(self, request, *args, **kwargs):
        service = Service.objects.get(pk=kwargs['pk'])
        return render(request, 'service/service_detail.html', {'service': service})
    
class AddServiceView(View):
    template_name = 'service/add_service.html'
    form_class = ServiceForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "سرویس جدید با موفقیت ایجاد شد.")
            return redirect('service:service')
        messages.error(request, "خطا در ایجاد سرویس. لطفاً دوباره تلاش کنید.")
        return render(request, self.template_name, {'form': form})

class UpdateServiceView(View):
    template_name = 'service/update_service.html'
    form_class = ServiceForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
    
    def get(self, request, *args, **kwargs):
        service = Service.objects.get(pk=kwargs['pk'])
        form = self.form_class(instance=service)
        return render(request, self.template_name, {'form': form, 'service': service})
    
    def post(self, request, *args, **kwargs):
        service = Service.objects.get(pk=kwargs['pk'])
        form = self.form_class(request.POST, request.FILES, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "سرویس با موفقیت ویرایش شد.")
            return redirect('service:service_detail' ,pk=service.pk)
        messages.error(request, "خطا در ویرایش سرویس. لطفاً دوباره تلاش کنید.")
        return render(request, self.template_name, {'form': form, 'service': service})

class RemoveServiceView(View):
    template_name = 'service/remove_service.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")

    def get(self, request, *args, **kwargs):
        service = Service.objects.get(pk=kwargs['pk'])
        return render(request, self.template_name, {'service': service})
    
    def post(self, request, *args, **kwargs):
        service = Service.objects.get(pk=kwargs['pk'])
        service.delete()
        messages.success(request, "سرویس با موفقیت حذف شد.")
        return redirect('service:service')