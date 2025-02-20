from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.hashers import check_password
from django.http import Http404
from django.contrib import messages
from django.views import View
from .forms import DoctorLoginForm, VerifyOTPForm
from .models import OTP
from django.core.mail import send_mail
from django.conf import settings


User = get_user_model()

class DoctorLoginView(View):
    template_name = 'accounts/login.html'
    form_class = DoctorLoginForm

    def get(self, request, *args, **kwargs):
        # اگر کاربر قبلاً وارد شده باشد، به داشبورد هدایت شود
        if request.user.is_authenticated:
            return redirect('home:home')
        
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # احراز هویت کاربر
            user = authenticate(username=username, password=password)
            
            if user and user.is_doctor:  # بررسی اینکه آیا کاربر پزشک است
                # ایجاد کد OTP جدید
                otp, created = OTP.objects.get_or_create(user=user)
                otp.generate_otp()

                # # ارسال ایمیل حاوی کد OTP
                send_mail(
                    'کد تأیید ورود پزشک',
                    f'کد ورود شما: {otp.code}',
                    settings.EMAIL_HOST_USER,
                    [user.email]
                )

                # ذخیره کد OTP در جلسه
                request.session['otp_user_id'] = user.id
                return redirect('accounts:verify_otp')  # هدایت به صفحه وارد کردن کد OTP

            else:
                messages.error(request, "شما مجاز به ورود به این بخش نیستید.")
                
        return render(request, self.template_name, {'form': form})
    
class DoctorLogoutView(View):   
    template_name = 'accounts/logout.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "با موفقیت خارج شدید.")
        return redirect('home:home')  # هدایت به صفحه ورود پزشک

class VerifyOTPView(View):
    template_name = 'accounts/verify_otp.html'
    form_class = VerifyOTPForm

    def dispatch(self, request, *args, **kwargs):
        if request.session.get('otp_user_id'):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            otp_code = form.cleaned_data["otp"]
            user_id = request.session.get('otp_user_id')

            if user_id:
                user = User.objects.get(id=user_id)
                otp = OTP.objects.get(user=user)
                
                if otp.code == otp_code and otp.is_valid():
                    login(request, user)
                    otp.delete()  # حذف کد OTP پس از استفاده
                    request.session.pop('otp_user_id', None)  # حذف متغیر سشن
                    messages.success(request, "با موفقیت وارد شدید.")
                    return redirect('home:home')  # هدایت به داشبورد پزشک
                else:
                    messages.error(request, "کد وارد شده صحیح نیست یا منقضی شده است.")
            else:
                messages.error(request, "جلسه شما به پایان رسیده است. لطفاً دوباره وارد شوید.")
                
        return render(request, self.template_name, {'form': form})