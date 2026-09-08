from django import forms

from utils.security.math_captcha import MathCaptchaFormMixin

from .models import ContactMessage


class ContactMessageForm(MathCaptchaFormMixin, forms.ModelForm):
    """
    Contact form with a math captcha and a hidden honeypot for spam protection.
    """
    MyLoveDoctor = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}),
        label='',
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
                'placeholder': 'شماره تماس (موبایل 09... یا ثابت 05...) — 11 رقم',
                'autocomplete': 'off',
                'inputmode': 'tel',
                'maxlength': '11',
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
        value = self.cleaned_data.get('MyLoveDoctor')
        if value:
            raise forms.ValidationError("فعالیت مشکوک تشخیص داده شد!")
        return value
