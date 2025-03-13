# Project-specific imports from common_imports
from utils.common_imports import render, Http404, messages, View, get_user_model, get_object_or_404, transaction, PasswordChangeForm
from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin
# Imports from local models
from .models import Doctor  

# Imports from local forms
from .forms import DoctorForm  
from users.forms import CustomUserDoctorUpdateForm  


User = get_user_model()

class DashboardView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    template_name = 'dashboard/dashboard.html'
    form_class_doctor = DoctorForm
    form_class_user = CustomUserDoctorUpdateForm
    form_class_password = PasswordChangeForm

    def dispatch(self, request, *args, **kwargs):
        # اول کوئری رو می‌زنیم
        self.doctor = get_object_or_404(
            Doctor.objects.select_related('user').prefetch_related(
                'blog_posts', 'doctor_galleries__images'
            ),
            id=kwargs['doctor_id']
        )
        self.blogs = self.doctor.blog_posts.all()
        self.galleries = self.doctor.doctor_galleries.all()
        
        # اگر کاربر دکتر باشد ولی بخواهد داشبورد دکتر دیگری را ببیند، خطا بده
        if request.user.is_doctor and request.user.doctor != self.doctor:
            raise PermissionError("شما فقط می‌توانید داشبورد خودتان را مشاهده کنید")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):

        doctor_form = self.form_class_doctor(instance=self.doctor)
        user_form = self.form_class_user(instance=self.doctor.user)
        password_form = self.form_class_password(user=self.doctor.user)  # فرم تغییر رمز
        context = {
            'doctor': self.doctor,
            'blogs': self.blogs,
            'galleries': self.galleries,
            'doctor_form': doctor_form,
            'user_form': user_form,
            'password_form': password_form,  
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        user_form = self.form_class_user(request.POST, request.FILES, instance=self.doctor.user)
        doctor_form = self.form_class_doctor(request.POST, instance=self.doctor)

        if user_form.is_valid() and doctor_form.is_valid():
            with transaction.atomic():
                user_form.save()
                doctor_form.save()
                messages.success(request, "تغییرات با موفقیت ذخیره شدند")

        else:
            messages.error(request, "خطا در اعتبارسنجی فرم‌ها")

        # برگرداندن کاربر به همون صفحه با فرم‌ها و داده‌ها
        context = {
            'doctor': self.doctor,
            'blogs': self.blogs,
            'galleries': self.galleries,
            'doctor_form': doctor_form,
            'user_form': user_form,
        }
        return render(request, self.template_name, context)

class DashboardListView(View):
    template_name = 'dashboard/dashboard_list.html'

    def dispatch(self, request, *args, **kwargs):
        if not(request.user.is_superuser and request.user.is_authenticated):
            raise Http404("صفحه مورد نظر یافت نشد.")
        return super().dispatch(request, *args, **kwargs)
        
    def get(self, request, *args, **kwargs):
        doctors = Doctor.objects.select_related('user').all()
        context = {'doctors': doctors}
        return render(request, self.template_name, context)