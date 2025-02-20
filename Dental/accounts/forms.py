from django import forms
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.forms import SetPasswordForm



User = get_user_model()
class DoctorLoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام کاربری'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور' }))
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if not username or not password:
            raise forms.ValidationError("نام کاربری و رمز عبور الزامی است.")

        try:
            user = User.objects.get(username=username)
            if not user.is_doctor:
                raise forms.ValidationError("شما مجاز به ورود به این بخش نیستید.")

            if not user.check_password(password):
                raise forms.ValidationError("رمز عبور اشتباه است.")
            
            # ذخیره‌ی کاربر برای استفاده در `get_user()`
            self.user = user

        except User.DoesNotExist:
            raise forms.ValidationError("نام کاربری یا رمز عبور اشتباه است.")

        return cleaned_data
    
class VerifyOTPForm(forms.Form):
    otp = forms.CharField(label="کد تأیید", max_length=6, widget=forms.TextInput(attrs={"class": "form-control"}))
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

class PasswordResetCaptchaForm(PasswordResetForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())  # اضافه کردن کپچا

class SetPasswordCaptchaForm(SetPasswordForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())  # اضافه کردن کپچا