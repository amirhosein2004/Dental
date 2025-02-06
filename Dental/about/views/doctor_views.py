from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404
from about.models import Doctor
from about.forms import DoctorForm
from django.core.exceptions import PermissionDenied


# class AddDoctorView(View):
#     template_name = 'about/add_doctor.html'
#     form_class = DoctorForm

#     def dispatch(self, request, *args, **kwargs):
#         if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
#             return super().dispatch(request, *args, **kwargs)
#         raise Http404("صفحه مورد نظر یافت نشد.")
    
#     def get(self, request, *args, **kwargs):    
#         form = self.form_class()
#         return render(request, self.template_name, {'form': form})
    
#     def post(self, request, *args, **kwargs):
#         form = self.form_class(request.POST, request.FILES)
#         if form.is_valid():
#             doctor = form.save(commit=False)
#             doctor.user = request.user
#             doctor.save()
#             messages.success(request, 'پروفایل دکتر با موفقیت ایجاد شد.')
#             return redirect('about:detail_doctor', doctor.pk)
#         return render(request, self.template_name, {'form': form})

class DetailDoctorView(View):
    template_name = 'about/detail_doctor.html'
    form_class = DoctorForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            if request.user.is_superuser or request.user.doctor.pk == kwargs['pk']:
                return super().dispatch(request, *args, **kwargs)
            else:
                raise PermissionDenied("شما اجازه دسترسی ندارید.")
        raise Http404("صفحه مورد نظر یافت نشد.")
    
    def get(self, request, *args, **kwargs):
        doctor = Doctor.objects.get(pk=kwargs['pk'])
        form = self.form_class(instance=doctor)
        return render(request, self.template_name, {'form': form, 'doctor': doctor})
    
    def post(self, request, *args, **kwargs):
        doctor = Doctor.objects.get(pk=kwargs['pk'])
        form = self.form_class(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, 'پروفایل دکتر با موفقیت ویرایش شد.')
            return redirect('about:detail_doctor', doctor.pk)
        return render(request, self.template_name, {'form': form, 'doctor': doctor})
    


    