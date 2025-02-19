from django import forms
from .models import WorkingHours, ContactMessage
from django.core.validators import RegexValidator
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox


class WorkingHoursForm(forms.ModelForm):
    class Meta:
        model = WorkingHours
        fields = ['day', 'morning_start', 'morning_end', 'evening_start', 'evening_end']
        widgets = {
            'day': forms.Select(attrs={'class': 'form-control'}),
            'morning_start': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 23}),
            'morning_end': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 23}),
            'evening_start': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 23}),
            'evening_end': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 23}),
        }

    # def clean_day(self):
    #     day = self.cleaned_data.get('day')

    #     # بررسی اینکه آیا روز قبلاً در دیتابیس ثبت شده است
    #     if WorkingHours.objects.filter(day=day).exists():
    #         raise forms.ValidationError(f'ساعات کاری برای {day} قبلاً ثبت شده است!')

    #     return day

class ContactMessageForm(forms.ModelForm):
    phone_validator = RegexValidator(
        regex=r'^09[0-9]{9}$',  # شماره باید با 09 شروع شود و 9 رقم بعدی داشته باشد
        message="شماره تلفن باید با 09 شروع شده و 11 رقم باشد."
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'phone', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام شما'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره تماس شما'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'متن پیام'}),
        }

    phone = forms.CharField(validators=[phone_validator])
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())