from django import forms
from .models import Doctor

class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['description', 'twitter', 'instagram', 'telegram', 'linkedin']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'توضیحات', 'rows': 4}),
            'twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'آدرس توییتر'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'آدرس اینستاگرام'}),
            'telegram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'آدرس تلگرام'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'آدرس لینکدین'}),
        }