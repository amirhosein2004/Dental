from django.shortcuts import render, redirect
import json
from django.http import Http404, JsonResponse
from django.contrib import messages
from django.views import View
from .models import Doctor
from blog.models import BlogPost
from gallery.models import Gallery
from .forms import DoctorForm
from users.forms import CustomUserDoctorUpdateForm
from blog.forms import BlogPostForm
from gallery.forms import GalleryForm
from django.contrib.auth import get_user_model


User = get_user_model()

class DasboardView(View):
    template_name = 'dashboard/dashboard.html'
    form_class_doctor = DoctorForm
    form_class_user = CustomUserDoctorUpdateForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise Http404("صفحه مورد نظر یافت نشد.")

        doctor_id = kwargs.get('doctor_id')

        # دریافت پروفایل دکتر فعلی که لاگین کرده
        logged_in_doctor = getattr(request.user, 'doctor', None)

        # اگر کاربر دکتر باشد ولی بخواهد داشبورد دکتر دیگری را ببیند، خطا بده
        if request.user.is_doctor and (not logged_in_doctor or logged_in_doctor.id != doctor_id):
            raise Http404("شما اجازه دسترسی به این صفحه را ندارید.")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        doctor_id = kwargs.get('doctor_id')

        # اگر سوپر یوزر است، می‌تواند هر دکتری را ببیند
        if request.user.is_superuser:
            doctor = Doctor.objects.filter(id=doctor_id).first()
        else:
            doctor = getattr(request.user, 'doctor', None)

        if not doctor:
            raise Http404("پروفایل پزشک یافت نشد.")

        blogs = BlogPost.objects.filter(writer=doctor).order_by("-updated_at")
        galleries = Gallery.objects.filter(doctor=doctor).order_by("-updated_at")

        doctor_form = self.form_class_doctor(instance=doctor)
        user_form = self.form_class_user(instance=doctor.user)

        user = User.objects.get(id=doctor.user.id)

        context = {
            'doctor': doctor,
            'blogs': blogs,
            'galleries': galleries,
            'doctor_form': doctor_form,
            'user_form': user_form,
            'user': user,
        }
        return render(request, self.template_name, context)
    
class EditProfileDashboardView(View):
    form_class_doctor = DoctorForm
    form_class_user = CustomUserDoctorUpdateForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise Http404("صفحه مورد نظر یافت نشد.")

        doctor_id = kwargs.get('doctor_id')

        # دریافت دکتر لاگین‌شده
        logged_in_doctor = getattr(request.user, 'doctor', None)

        # اگر کاربر دکتر باشد ولی بخواهد پروفایل دکتر دیگری را ویرایش کند، خطا بده
        if request.user.is_doctor and (not logged_in_doctor or logged_in_doctor.id != doctor_id):
            raise Http404("شما اجازه ویرایش این پروفایل را ندارید.")

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        doctor_id = kwargs.get('doctor_id')

        # سوپر یوزر می‌تواند اطلاعات هر دکتری را ویرایش کند
        if request.user.is_superuser:
            doctor_instance = Doctor.objects.filter(id=doctor_id).first()
        else:
            doctor_instance = getattr(request.user, 'doctor', None)

        if not doctor_instance:
            return JsonResponse({'status': 'error', 'message': 'پروفایل پزشک یافت نشد.'})

        user_form = self.form_class_user(request.POST, request.FILES, instance=doctor_instance.user)
        doctor_form = self.form_class_doctor(request.POST, instance=doctor_instance)

        if user_form.is_valid() and doctor_form.is_valid():
            user_form.save()
            doctor_form.save()
            return JsonResponse({'status': 'success', 'message': 'تغییرات با موفقیت ذخیره شدند.'})

        errors = {
            'user_errors': user_form.errors,
            'doctor_errors': doctor_form.errors
        }
        return JsonResponse({'status': 'error', 'message': 'خطا در اعتبارسنجی فرم‌ها', 'errors': errors})

class DashboardListView(View):
    template_name = 'dashboard/dashboard_list.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
    
    def get(self, request, *args, **kwargs):
        doctors = Doctor.objects.all()
        return render(request, self.template_name, {'doctors': doctors})