from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from utils.security.login_throttle import locked_for
from utils.security.math_captcha import MathCaptchaFormMixin


User = get_user_model()


class _HoneypotFormMixin:
    """Adds a hidden honeypot field named `MyLoveDoctor` (kept for template compat)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['MyLoveDoctor'] = forms.CharField(
            required=False,
            widget=forms.HiddenInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}),
            label='',
        )

    def clean_MyLoveDoctor(self):
        value = self.cleaned_data.get('MyLoveDoctor')
        if value:
            raise ValidationError("فعالیت مشکوک تشخیص داده شد!")
        return value


class DoctorLoginForm(MathCaptchaFormMixin, _HoneypotFormMixin, forms.Form):
    """
    Doctor login: username + password + math captcha + honeypot.
    """
    username = forms.CharField(
        max_length=150,
        validators=[RegexValidator(
            regex=r'^(?!\d+$)(?![_\W]+$)[a-zA-Z0-9_@.+-]+$',
            message="نام کاربری باید ترکیبی از حروف و اعداد باشه و فقط از '_', '@', '.', '+', '-' استفاده کنه",
        )],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام کاربری', 'autocomplete': 'off'}),
        label="نام کاربری",
        error_messages={'required': "نام کاربری الزامی است"},
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور', 'autocomplete': 'new-password'}),
        label="رمز عبور",
        validators=[validate_password],
        error_messages={'required': "رمز عبور الزامی است"},
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            request = self._captcha_request

            # Asked before authenticating so a locked-out doctor is told how
            # long is left. LoginThrottleBackend would refuse the attempt
            # anyway, but only as a generic "wrong password" — correct, and
            # unhelpful to the person who simply mistyped five times.
            remaining = locked_for(request, username)
            if remaining:
                raise ValidationError(
                    'به دلیل تلاش‌های ناموفق زیاد، ورود موقتاً مسدود شده است. '
                    f'حدود {remaining // 60} دقیقه دیگر دوباره تلاش کنید'
                )

            # `request` is required, not optional: LoginThrottleBackend needs
            # it to resolve the caller's IP. The captcha mixin already holds
            # it, so there is nothing extra for callers to pass.
            user = authenticate(
                request=request,
                username=username,
                password=password,
            )
            if not user:
                raise ValidationError("نام کاربری یا رمز عبور اشتباه است")
            if not user.is_doctor:
                raise ValidationError("شما مجاز به ورود به این بخش نیستی")
            self.user = user
        return cleaned_data


class VerifyOTPForm(MathCaptchaFormMixin, _HoneypotFormMixin, forms.Form):
    """
    OTP verification: 6-digit code + math captcha + honeypot.
    """
    otp = forms.CharField(
        label="کد تأیید",
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'auth-form__otp',
            'placeholder': '••••••',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'pattern': r'\d{6}',
            'maxlength': '6',
        }),
        validators=[RegexValidator(
            regex=r'^\d{6}$',
            message="لطفاً یه کد ۶ رقمی عددی وارد کن",
        )],
        error_messages={'required': "کد تأیید الزامی است"},
    )


class PasswordResetCaptchaForm(MathCaptchaFormMixin, _HoneypotFormMixin, PasswordResetForm):
    """Password reset request with math captcha + honeypot."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'ایمیل',
            'autocomplete': 'off',
        })
        self.fields['email'].error_messages.update({
            'required': "لطفاً ایمیل رو وارد کن",
            'invalid': "لطفاً یه ایمیل معتبر وارد کن",
        })


class SetPasswordCaptchaForm(MathCaptchaFormMixin, _HoneypotFormMixin, SetPasswordForm):
    """Set new password after reset link, with math captcha + honeypot."""

    error_messages = {
        'password_mismatch': "رمزهای عبور وارد شده یکسان نیستن",
        'password_too_short': "رمز عبورت باید حداقل ۸ کاراکتر داشته باشه",
        'password_too_common': "رمز عبورت نباید یه رمز رایج باشه",
        'password_entirely_numeric': "رمز عبورت نباید فقط عدد باشه",
        'password_too_similar': "رمز عبورت نباید خیلی شبیه اطلاعات شخصی دیگه‌ات باشه",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'رمز عبور جدید',
            'autocomplete': 'new-password',
        })
        self.fields['new_password1'].error_messages.update({
            'required': "لطفاً رمز عبور جدید رو وارد کن",
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'تکرار رمز عبور',
            'autocomplete': 'new-password',
        })
        self.fields['new_password2'].error_messages.update({
            'required': "لطفاً تکرار رمز عبور رو وارد کن",
        })
        self.fields['new_password1'].help_text = ""
        self.fields['new_password2'].help_text = ""
