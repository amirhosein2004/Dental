from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404
from about.models import Clinic
from about.forms import ClinicForm


class DetailClinicView(View):
    template_name = 'about/detail_clinic.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
        
    def get(self, request, *args, **kwargs):
        clinic = Clinic.objects.get(pk=kwargs['pk'])
        context = {
            'clinic': clinic,
        }
        return render(request, self.template_name, context)

class AddClinicView(View):
    template_name = 'about/add_clinic.html'
    form_class = ClinicForm

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
            messages.success(request, 'Clinic added successfully.')
            return redirect('about:edit_about')
        context = {
            'form': form,
        }
        return render(request, self.template_name, context)

class UpdateClinicView(View):
    template_name = 'about/update_clinic.html'
    form_class = ClinicForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
        
    def get(self, request, *args, **kwargs):
        clinic = Clinic.objects.get(pk=kwargs['pk'])
        form = self.form_class(instance=clinic)
        context = {
            'form': form,
            'clinic': clinic
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        clinic = Clinic.objects.get(pk=kwargs['pk'])
        form = self.form_class(request.POST, request.FILES, instance=clinic)
        if form.is_valid():
            form.save()
            messages.success(request, 'Clinic updated successfully.')
            return redirect('about:edit_about')
        context = {
            'form': form,
            'clinic': clinic
        }
        return render(request, self.template_name, context)

class DeleteClinicView(View):
    template_name = 'about/delete_clinic.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")

    def get(self, request, *args, **kwargs):
        clinic = Clinic.objects.get(pk=kwargs['pk'])
        context = {
            'clinic': clinic,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        clinic = Clinic.objects.get(pk=kwargs['pk'])
        clinic.delete()
        messages.success(request, 'Clinic deleted successfully.')
        return redirect('about:edit_about')