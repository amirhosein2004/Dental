from utils.common_imports import (
    render, redirect, login, logout, 
    get_user_model, messages, PermissionDenied,
    View, timezone, get_object_or_404,
    PasswordChangeForm, transaction
)
from utils.tasks import send_otp_email_task  # import send email task celery
from utils.sessions import generate_otp_token
from utils.mixins import RateLimitMixin, SessionValidatorMixin, DoctorOrSuperuserRequiredMixin, RedirectIfAuthenticatedMixin
from accounts.forms import DoctorLoginForm, VerifyOTPForm 
from accounts.models import OTP 
from datetime import timedelta
from django.contrib.auth import update_session_auth_hash    

# Get the custom user model
User = get_user_model()

class DoctorLoginView(RateLimitMixin, RedirectIfAuthenticatedMixin, View):
    """
    View for handling doctor login.
    This view handles the display and processing of the login form for doctors.
    The doctor needs to provide their credentials to receive an OTP for login.
    """
    rate_limit = '5/m'  # Rate limit for login attempts
    template_name = 'accounts/login.html'  
    form_class = DoctorLoginForm  

    def get(self, request, *args, **kwargs):
        """
        Display the login form.
        """
        return render(request, self.template_name, {'form': self.form_class()})
    
    def post(self, request, *args, **kwargs):
        """
        Handle login form submission.
        If the form is valid, generate an OTP, send it via email, and store an OTP token in the session.
        """
        form = self.form_class(request.POST)

        if form.is_valid():
            user = form.user  # Valid user set in the form
            otp = OTP.objects.get_or_create(user=user)[0]
            otp.generate_otp()

            # Store OTP token in session for later verification
            request.session['otp_token'] = generate_otp_token(user)

            # Send the OTP to the user's email
            if send_otp_email_task.delay(user.email, otp.code):
                messages.success(request, "کد تأیید به ایمیل شما ارسال شد")
                return redirect('accounts:verify_otp')

        # If the form is invalid, re-render the login form with errors
        return render(request, self.template_name, {'form': form})
    
class DoctorLogoutView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View for handling doctor logout.
    This view handles the display of the logout confirmation page and processes the logout action.
    """
    rate_limit = '5/m'  # Rate limit for logout attempts
    template_name = 'accounts/logout.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "شما با موفقیت از حساب کاربری خارج شدید. به امید دیدار دوباره")
        return redirect('home:home')  

class VerifyOTPView(RateLimitMixin, SessionValidatorMixin, View):
    """
    View for verifying the OTP sent to the doctor.
    This view handles OTP input by the doctor and verifies whether the entered OTP is correct and valid.
    """
    rate_limit = '5/2m'  # Rate limit for OTP verification attempts
    error_message = "شما به حداکثر تعداد درخواست‌ها رسیده‌اید. لطفا دو دقیقه دیگر تلاش کنید"
    template_name = 'accounts/verify_otp.html'  
    form_class = VerifyOTPForm  

    def get(self, request, *args, **kwargs):
        """
        Display the OTP verification form.
        """
        return render(request, self.template_name, {'form': self.form_class()})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            otp_code = form.cleaned_data["otp"]
            otp = OTP.objects.filter(user=self.user).first()

            # OTP not found, invalid code, or expired code handling
            if not otp:
                messages.error(request, "کد برای این کاربر یافت نشد")
            elif otp.code != otp_code:
                messages.error(request, "کد وارد شده اشتباه است")
            elif not otp.is_valid():
                messages.error(request, "کد تأیید منقضی شده است. لطفاً دوباره درخواست کنید")
            else:
                # OTP is valid, log the user in
                request.session.flush()
                login(request, self.user)
                otp.delete()
                messages.success(request, f"ورود با موفقیت انجام شد. {self.user.username} خوش آمدید")
                return redirect('home:home')

        return render(request, self.template_name, {'form': form})
    
class ResendOTPView(RateLimitMixin, SessionValidatorMixin, View):     
    """
    View for resending OTP to the doctor.
    This view handles requests to resend OTP after a certain cooldown period.
    """
    rate_limit = '5/m'  # Rate limit for OTP resend attempts
    template_name = 'accounts/verify_otp.html'  
    form_class = VerifyOTPForm  
    RESEND_COOLDOWN = timedelta(seconds=60)  # Cooldown time for OTP resend

    def post(self, request, *args, **kwargs):
        last_resend_time = request.session.get('last_resend_time')
        current_time = timezone.now()

        # Check if the cooldown period has passed
        if last_resend_time:
            last_resend = timezone.datetime.fromisoformat(last_resend_time)
            if current_time - last_resend < self.RESEND_COOLDOWN:
                remaining_seconds = int((self.RESEND_COOLDOWN - (current_time - last_resend)).total_seconds())
                return render(request, self.template_name, {
                    'form': self.form_class(),
                    'remaining_seconds': remaining_seconds
                })

        # Generate a new OTP and send it to the user's email
        otp, _ = OTP.objects.get_or_create(user=self.user)
        otp.generate_otp()

        if send_otp_email_task.delay(self.user.email, otp.code):
            request.session['last_resend_time'] = current_time.isoformat()
            messages.success(request, "کد تأیید به ایمیل شما ارسال شد")
            return render(request, self.template_name, {
                'form': self.form_class(),
                'remaining_seconds': 60,  # Time remaining until next resend
            })

        messages.error(request, "ارسال ایمیل با مشکل مواجه شد. لطفاً دوباره تلاش کنید")
        return redirect('accounts:verify_otp')

class ChangePasswordView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View for changing the doctor's password.
    This view allows doctors or superusers to change their password after authentication.
    """
    rate_limit = '5/m'  # Rate limit for password change attempts
    template_name = 'accounts/change_password.html'  
    form_class = PasswordChangeForm  

    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(
            User, id=kwargs['user_id']
        )
        if not request.user.is_superuser and request.user != self.user:
            raise PermissionDenied("شما فقط می‌توانید رمز عبور خودتان را تغییر دهید")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(user=self.user)
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(user=self.user, data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                update_session_auth_hash(request, form.user)  # Keep the user logged in after changing password
                messages.success(request, "رمز عبور شما با موفقیت تغییر کرد.")
                return redirect('home:home')

        return render(request, self.template_name, {'form': form})