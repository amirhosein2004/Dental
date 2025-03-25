from utils.common_imports import forms
from .models import Doctor

class DoctorForm(forms.ModelForm):
    """
    A form for creating and updating Doctor instances.
    """
    class Meta:
        model = Doctor
        fields = ['description', 'twitter', 'instagram', 'telegram', 'linkedin']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً: متخصص داخلی با 10 سال تجربه',
                'rows': 4
            }),
            'twitter': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً: https://twitter.com/yourusername'
            }),
            'instagram': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً: https://instagram.com/yourusername'
            }),
            'telegram': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً: https://t.me/yourusername'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً: https://linkedin.com/in/yourusername'
            }),
        }
        labels = {
            'description': 'توضیحات',
            'twitter': 'توییتر',
            'instagram': 'اینستاگرام',
            'telegram': 'تلگرام',
            'linkedin': 'لینکدین',
        }
        error_messages = {
            'description': {
                'required': "لطفاً توضیحات خود را وارد کنید",
            },
            'twitter': {
                'invalid': "لطفاً یک آدرس توییتر معتبر وارد کنید",
            },
            'instagram': {
                'invalid': "لطفاً یک آدرس اینستاگرام معتبر وارد کنید",
            },
            'telegram': {
                'invalid': "لطفاً یک آدرس تلگرام معتبر وارد کنید",
            },
            'linkedin': {
                'invalid': "لطفاً یک آدرس لینکدین معتبر وارد کنید",
            },
        }