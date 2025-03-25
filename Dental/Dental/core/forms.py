from utils.common_imports import forms
from .models import Category, Clinic

class CategoryForm(forms.ModelForm):
    """
    Form for creating and updating Category instances.
    """
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام دسته‌بندی'}),
        }
        error_messages = {
            'name': {
                'required': "لطفاً نام دسته‌بندی را وارد کنید.",
                'unique': "دسته‌بندی با این نام قبلاً وجود دارد.",
                'max_length': "عنوان نمی‌تواند بیشتر از 150 کاراکتر باشد",
            },
        }

class ClinicForm(forms.ModelForm):
    """
    Form for creating and updating Clinic instances.
    """
    class Meta:
        model = Clinic
        fields = ['name', 'address', 'phone', 'email', 'description', 'image', 'is_primary']
        labels = {
            'name': 'نام مطب',
            'address': 'آدرس',
            'phone': 'تلفن',
            'email': 'ایمیل',
            'description': 'توضیحات',
            'image': 'تصویر',
            'is_primary': 'مطب اصلی',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام مطب (مثال: مطب دکتر احمدی)',
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'آدرس مطب (مثال: تهران، خ انقلاب)',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شماره تماس (مثال: 09123456789)',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ایمیل مطب (مثال: clinic@example.com)',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'توضیحات درباره مطب (اختیاری)',
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png',  # Restrict file types in the browser
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        error_messages = {
            'name': {
                'required': "لطفاً نام مطب را وارد کنید.",
                'unique': "مطبی با این نام قبلاً ثبت شده است.",
                'max_length': "نام نمی‌تواند بیشتر از ۱۰۰ کاراکتر باشد.",
            },
            'address': {
                'required': "لطفاً آدرس مطب را وارد کنید.",
                'max_length': "آدرس نمی‌تواند بیشتر از ۱۰۰ کاراکتر باشد.",
            },
            'phone': {
                'required': "لطفاً شماره تلفن را وارد کنید."
            },
            'email': {
                'required': "لطفاً ایمیل مطب را وارد کنید.",
                'invalid': "لطفاً یک ایمیل معتبر وارد کنید.",
            },
        }