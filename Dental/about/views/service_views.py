from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404
from about.models import Service
from about.forms import ServiceForm


class DetailServiceView(View):
    template_name = 'about/detail_service.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
    
    def get(self, request, *args, **kwargs):
        service = Service.objects.get(pk=kwargs['pk'])
        context = {
            'service': service,
        }
        return render(request, self.template_name, context)

class AddServiceView(View):
    template_name = 'about/add_service.html'
    form_class = ServiceForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
        
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {
            'form': form,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service added successfully.')
            return redirect('about:edit_about')
        context = {
            'form': form,
        }
        return render(request, self.template_name, context)

class UpdateServiceView(View):
    template_name = 'about/update_service.html'
    form_class = ServiceForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
        
    def get(self, request, *args, **kwargs):
        service = Service.objects.get(pk=kwargs['pk'])
        form = self.form_class(instance=service)
        context = {
            'form': form,
            'service': service,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        service = Service.objects.get(pk=kwargs['pk'])
        form = self.form_class(request.POST, request.FILES, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service updated successfully.')
            return redirect('about:edit_about')
        context = {
            'form': form,
            'service': service,
        }
        return render(request, self.template_name, context)

class DeleteServiceView(View):
    template_name = 'about/delete_service.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
        
    def get(self, request, *args, **kwargs):
        service = Service.objects.get(pk=kwargs['pk'])
        context = {
            'service': service,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        service = Service.objects.get(pk=kwargs['pk'])
        service.delete()
        messages.success(request, 'Service deleted successfully.')
        return redirect('about:edit_about')