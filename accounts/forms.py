from utils.common_imports import forms, get_user_model, RegexValidator, authenticate, ValidationError
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox

User = get_user_model()

class DoctorLoginForm(forms.Form):
    """
    Form for doctor login with username, password, and captcha validation.
    Includes a honeypot field to prevent spam.
    """
    username = forms.CharField(
        max_length=150,
        validators=[RegexValidator(
            regex=r'^(?!\d+$)(?![_\W]+$)[a-zA-Z0-9_@.+-]+$',
            message="نام کاربری باید ترکیبی از حروف و اعداد باشه و فقط از '_', '@', '.', '+', '-' استفاده کنه"
        )],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام کاربری', 'autocomplete': 'off'}),
        label="نام کاربری", 
        error_messages={'required': "نام کاربری الزامی است"}
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور', 'autocomplete': 'new-password'}),
        label="رمز عبور",
        validators=[validate_password],
        error_messages={'required': "رمز عبور الزامی است"}
    )
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(),
        error_messages={'required': "لطفاً کپچا رو تکمیل کن"}
    )
    # Honeypot field to prevent spam
    MyLoveDoctor = forms.CharField( 
        required=False,
        widget=forms.HiddenInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}),
        label=''
    )

    def clean(self):
        """
        Custom clean method to authenticate the user and check if the user is a doctor.
        """
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise ValidationError("نام کاربری یا رمز عبور اشتباه است")
            if not user.is_doctor:
                raise ValidationError("شما مجاز به ورود به این بخش نیستی")
            self.user = user
        return cleaned_data
    
    def clean_MyLoveDoctor(self):
        """
        Custom clean method for the honeypot field to detect suspicious activity.
        """
        MyLoveDoctor = self.cleaned_data.get('MyLoveDoctor')
        if MyLoveDoctor:
            raise ValidationError("فعالیت مشکوک تشخیص داده شد!")
        return MyLoveDoctor
        
class VerifyOTPForm(forms.Form):
    """
    Form for verifying OTP with captcha validation.
    Includes a honeypot field to prevent spam.
    """
    otp = forms.CharField(
        label="کد تأیید",
        max_length=6,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "کد تأیید ۶ رقمی", 'autocomplete': 'one-time-code'}),
        validators=[RegexValidator(
            regex=r'^\d{6}$',
            message="لطفاً یه کد ۶ رقمی عددی وارد کن"
        )],
        error_messages={'required': "کد تأیید الزامی است"}
    )
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(),
        error_messages={'required': "لطفاً کپچا رو تکمیل کن"}
    )
    # Honeypot field to prevent spam
    MyLoveDoctor = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}),
        label=''
    )

    def clean_MyLoveDoctor(self):
        """
        Custom clean method for the honeypot field to detect suspicious activity.
        """
        MyLoveDoctor = self.cleaned_data.get('MyLoveDoctor')
        if MyLoveDoctor:
            raise ValidationError("فعالیت مشکوک تشخیص داده شد!")
        return MyLoveDoctor

class PasswordResetCaptchaForm(PasswordResetForm):
    """
    Form for password reset with captcha validation.
    Includes a honeypot field to prevent spam.
    """
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(),
        error_messages={'required': "لطفاً کپچا رو تکمیل کن"}
    ) 
    # Honeypot field to prevent spam
    MyLoveDoctor = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}),
        label=''
    )
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form and update the email field attributes and error messages.
        """
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'ایمیل',
            'autocomplete': 'off'
        })
        self.fields['email'].error_messages.update({
            'required': "لطفاً ایمیل رو وارد کن",
            'invalid': "لطفاً یه ایمیل معتبر وارد کن"
        })

    def clean_MyLoveDoctor(self):
        """
        Custom clean method for the honeypot field to detect suspicious activity.
        """
        MyLoveDoctor = self.cleaned_data.get('MyLoveDoctor')
        if MyLoveDoctor:
            raise ValidationError("فعالیت مشکوک تشخیص داده شد!")
        return MyLoveDoctor

class SetPasswordCaptchaForm(SetPasswordForm):
    """
    Form for setting a new password with captcha validation.
    Includes a honeypot field to prevent spam.
    """
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(),
        error_messages={'required': "لطفاً کپچا رو تکمیل کن"}
    )
    # Honeypot field to prevent spam
    MyLoveDoctor = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}),
        label=''
    )

    error_messages = {
        'password_mismatch': "رمزهای عبور وارد شده یکسان نیستن",
        'password_too_short': "رمز عبورت باید حداقل ۸ کاراکتر داشته باشه",
        'password_too_common': "رمز عبورت نباید یه رمز رایج باشه",
        'password_entirely_numeric': "رمز عبورت نباید فقط عدد باشه",
        'password_too_similar': "رمز عبورت نباید خیلی شبیه اطلاعات شخصی دیگه‌ات باشه",
    }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form and update the new password fields attributes and error messages.
        """
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'رمز عبور جدید',
            'autocomplete': 'new-password'
        })
        self.fields['new_password1'].error_messages.update({
            'required': "لطفاً رمز عبور جدید رو وارد کن"
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'تکرار رمز عبور',
            'autocomplete': 'new-password'
        })
        self.fields['new_password2'].error_messages.update({
            'required': "لطفاً تکرار رمز عبور رو وارد کن"
        })
        # Disable default help text
        self.fields['new_password1'].help_text = ""
        self.fields['new_password2'].help_text = ""
    
    def clean_MyLoveDoctor(self):
        """
        Custom clean method for the honeypot field to detect suspicious activity.
        """
        MyLoveDoctor = self.cleaned_data.get('MyLoveDoctor')
        if MyLoveDoctor:
            raise forms.ValidationError("فعالیت مشکوک تشخیص داده شد!")
        return MyLoveDoctor