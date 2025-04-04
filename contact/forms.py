from utils.common_imports import forms

from captcha.fields import ReCaptchaField  
from captcha.widgets import ReCaptchaV2Checkbox  

from .models import ContactMessage  


class ContactMessageForm(forms.ModelForm):
    """
    Form for submitting contact messages with CAPTCHA and honeypot field for spam prevention.
    """
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(),
        error_messages={
            'required': "لطفاً کپچا را تأیید کنید",
            'invalid': "کپچا نامعتبر است. لطفاً دوباره تلاش کنید",
        }
    )
    # Honeypot field to prevent spam
    MyLoveDoctor = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}),
        label=''
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'phone', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام شما',
                'autocomplete': 'off',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'متن پیام',
                'autocomplete': 'off',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شماره تماس شما مانند : 093670346',
                'autocomplete': 'off',
            }),
        }
        labels = {
            'name': 'نام',
            'phone': 'شماره تماس',
            'message': 'پیام',
        }
        error_messages = {
            'name': {'required': "لطفاً نام خود را وارد کنید"},
            'phone': {'required': "لطفاً شماره تلفن خود را وارد کنید"},
            'message': {'required': "لطفاً پیام خود را وارد کنید"},
        }

    def clean_MyLoveDoctor(self):
        """
        Custom validation for the honeypot field to detect and prevent spam.
        """
        MyLoveDoctor = self.cleaned_data.get('MyLoveDoctor')
        if MyLoveDoctor:
            raise forms.ValidationError("فعالیت مشکوک تشخیص داده شد!")
        return MyLoveDoctor