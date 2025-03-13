# Project-specific imports from common_imports
from utils.common_imports import forms

# Third-party imports (Django validators and captcha fields/widgets)
from captcha.fields import ReCaptchaField  
from captcha.widgets import ReCaptchaV2Checkbox  

# Imports from local models
from .models import WorkingHours, ContactMessage  


class WorkingHoursForm(forms.ModelForm):
    class Meta:
        model = WorkingHours
        fields = ['day', 'morning_start', 'morning_end', 'evening_start', 'evening_end']
        widgets = {
            'day': forms.Select(attrs={'class': 'form-control'}),
            'morning_start': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 23,
                'placeholder': 'اگر چیزی وارد نکنید تعطیل ثبت می‌شود'
            }),
            'morning_end': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 23,
                'placeholder': 'اگر چیزی وارد نکنید تعطیل ثبت می‌شود'
            }),
            'evening_start': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 23,
                'placeholder': 'اگر چیزی وارد نکنید تعطیل ثبت می‌شود'
            }),
            'evening_end': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 23,
                'placeholder': 'اگر چیزی وارد نکنید تعطیل ثبت می‌شود'
            }),
        }
        error_messages = {
            'day': {
                'required': "لطفاً روز هفته را انتخاب کنید.",
            },
        }
    def clean(self):
        """اعتبارسنجی فرم"""
        cleaned_data = super().clean()
        morning_start = cleaned_data.get('morning_start')
        morning_end = cleaned_data.get('morning_end')
        evening_start = cleaned_data.get('evening_start')
        evening_end = cleaned_data.get('evening_end')

        # اعتبارسنجی شیفت صبح
        if morning_start is not None and morning_end is not None:
            if morning_start >= morning_end:
                self.add_error('morning_start', "ساعت شروع صبح باید کمتر از ساعت پایان باشد")
                self.add_error('morning_end', "ساعت پایان صبح باید بیشتر از ساعت شروع باشد")

        # اعتبارسنجی شیفت عصر
        if evening_start is not None and evening_end is not None:
            if evening_start >= evening_end:
                self.add_error('evening_start', "ساعت شروع عصر باید کمتر از ساعت پایان باشد")
                self.add_error('evening_end', "ساعت پایان عصر باید بیشتر از ساعت شروع باشد")

        # اگر فقط یکی از شروع یا پایان پر شده باشد
        if morning_start is not None and morning_end is None:
            self.add_error('morning_end', "لطفاً ساعت پایان صبح را وارد کنید")
        if morning_end is not None and morning_start is None:
            self.add_error('morning_start', "لطفاً ساعت شروع صبح را وارد کنید")
        if evening_start is not None and evening_end is None:
            self.add_error('evening_end', "لطفاً ساعت پایان عصر را وارد کنید")
        if evening_end is not None and evening_start is None:
            self.add_error('evening_start', "لطفاً ساعت شروع عصر را وارد کنید")

        return cleaned_data

class ContactMessageForm(forms.ModelForm):

    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(),
        error_messages={
            'required': "لطفاً کپچا را تأیید کنید",
            'invalid': "کپچا نامعتبر است. لطفاً دوباره تلاش کنید",
        }
    )
    # honeypot field to prevent spam
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
                  'placeholder': 'شماره تماس شما',
                  'autocomplete': 'off',
            }),
        }
        error_messages = {
            'name': {'required': "لطفاً نام خود را وارد کنید"},
            'phone': {'required': "لطفاً شماره تلفن خود را وارد کنید"},
            'message': {'required': "لطفاً پیام خود را وارد کنید"},
        }
    def clean_MyLoveDoctor(self):
        MyLoveDoctor = self.cleaned_data.get('MyLoveDoctor')
        if MyLoveDoctor:
            raise forms.ValidationError("فعالیت مشکوک تشخیص داده شد!")
        return MyLoveDoctor