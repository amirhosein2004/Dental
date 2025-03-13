from utils.common_imports import (
    render, redirect, login, logout, 
    get_user_model, messages,  
    View, timezone, get_object_or_404,
    PasswordChangeForm, transaction
)
from utils.email_utils import send_otp_email
from utils.sessions import generate_otp_token
from utils.mixins import RateLimitMixin, SessionValidatorMixin, DoctorOrSuperuserRequiredMixin, RedirectIfAuthenticatedMixin
from accounts.forms import DoctorLoginForm, VerifyOTPForm 
from accounts.models import OTP 
from datetime import timedelta
from django.contrib.auth import update_session_auth_hash    


User = get_user_model()

class DoctorLoginView(RateLimitMixin, RedirectIfAuthenticatedMixin, View):
    rate_limit = '5/m'
    template_name = 'accounts/login.html'
    form_class = DoctorLoginForm

    def get(self, request, *args, **kwargs):
        """نمایش فرم ورود"""
        return render(request, self.template_name, {'form': self.form_class()})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            user = form.user  # کاربر معتبر که توی فرم ست شده
            otp= OTP.objects.get_or_create(user=user)[0]
            otp.generate_otp()

            request.session['otp_token'] = generate_otp_token(user)

            if send_otp_email(user, otp.code):
                messages.success(request, "کد تأیید به ایمیل شما ارسال شد")
                return redirect('accounts:verify_otp')

            messages.error(request, "ارسال ایمیل با مشکل مواجه شد. لطفاً دوباره تلاش کنید")
        return render(request, self.template_name, {'form': form})

class DoctorLogoutView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    rate_limit = '5/m'   
    template_name = 'accounts/logout.html'
           
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "شما با موفقیت از حساب کاربری خارج شدید. به امید دیدار دوباره")
        return redirect('home:home')  # هدایت به صفحه ورود پزشک

class VerifyOTPView(RateLimitMixin, SessionValidatorMixin, View):
    rate_limit = '5/2m'
    error_message = "شما به حداکثر تعداد در خوسات رسیده اید. لطفا دو دقیقه دیگر تلاش کنید"
    template_name = 'accounts/verify_otp.html'
    form_class = VerifyOTPForm

    def get(self, request, *args, **kwargs):
        """نمایش فرم تأیید OTP"""
        return render(request, self.template_name, {'form': self.form_class()})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            otp_code = form.cleaned_data["otp"]
            otp = OTP.objects.filter(user=self.user).first()

            if not otp:
                messages.error(request, "کد برای این کاربر یافت نشد")
            elif otp.code != otp_code:
                messages.error(request, "کد وارد شده اشتباه است")
            elif not otp.is_valid():
                messages.error(request, "کد تأیید منقضی شده است. لطفاً دوباره درخواست کنید")
            else:
                request.session.flush()
                login(request, self.user)
                otp.delete()
                messages.success(request, f"ورود با موفقیت انجام شد {self.user.username} خوش آمدید")
                return redirect('home:home')

        return render(request, self.template_name, {'form': form})
    
class ResendOTPView(RateLimitMixin, SessionValidatorMixin, View):     
    rate_limit = '5/m'
    template_name = 'accounts/verify_otp.html'
    form_class = VerifyOTPForm
    RESEND_COOLDOWN = timedelta(seconds=60)

    def post(self, request, *args, **kwargs):
        """ارسال مجدد کد OTP با محدودیت زمانی"""
        last_resend_time = request.session.get('last_resend_time')
        current_time = timezone.now()

        if last_resend_time:
            last_resend = timezone.datetime.fromisoformat(last_resend_time)
            if current_time - last_resend < self.RESEND_COOLDOWN:
                remaining_seconds = int((self.RESEND_COOLDOWN - (current_time - last_resend)).total_seconds())
                return render(request, self.template_name, {
                    'form': self.form_class(),
                    'remaining_seconds': remaining_seconds
                })

        otp, _ = OTP.objects.get_or_create(user=self.user)
        otp.generate_otp()

        if send_otp_email(self.user, otp.code):
            request.session['last_resend_time'] = current_time.isoformat()
            messages.success(request, "کد تأیید به ایمیل شما ارسال شد")
            return render(request, self.template_name, {
                'form': self.form_class(),
                'remaining_seconds': 30,
            })

        messages.error(request, "ارسال ایمیل با مشکل مواجه شد. لطفاً دوباره تلاش کنید")
        return redirect('accounts:verify_otp')

class ChangePasswordView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    rate_limit = '5/m'
    template_name = 'accounts/change_password.html'
    form_class = PasswordChangeForm

    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(
            User, id=kwargs['user_id']
        )
        if not request.user.is_superuser and request.user != self.user:
            raise PermissionError("شما فقط می‌توانید رمز عبور خودتان را تغییر دهید")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(user=self.user)
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(user=self.user, data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                update_session_auth_hash(request, form.user)  # حفظ جلسه کاربر پس از تغییر رمز
                messages.success(request, "رمز عبور شما با موفقیت تغییر کرد")
                return redirect('home:home')

        return render(request, self.template_name, {'form': form})

