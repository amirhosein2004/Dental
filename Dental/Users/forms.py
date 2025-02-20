from django import forms
from django.contrib.auth import get_user_model


User = get_user_model()

class CustomUserDoctorUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['image', 'username', 'email', 'first_name', 'last_name']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control-file', 'placeholder': 'تصویر پروفایل'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام کاربری'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ایمیل'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی'}),
        }
