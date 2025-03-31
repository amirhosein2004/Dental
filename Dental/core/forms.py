from utils.common_imports import forms
from .models import Category, Clinic, WorkingHours, Banner

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
                'placeholder': 'توضیحات درباره مطب ',
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
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
            'description': {
                'required': "لطفا توضیحات خود را وارد کنبد",
            },
            'image': {
                'required': "لطفا عکس خود را وارد کنید",
            },
        }

class WorkingHoursForm(forms.ModelForm):
    """
    Form for managing working hours with validation for morning and evening times.
    """
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
        labels = {
            'day': 'روز هفته',
            'morning_start': 'ساعت شروع صبح',
            'morning_end': 'ساعت پایان صبح',
            'evening_start': 'ساعت شروع عصر',
            'evening_end': 'ساعت پایان عصر',
        }
        error_messages = {
            'day': {
                'required': "لطفاً روز هفته را انتخاب کنید.",
            },
        }

    def clean(self):
        """
        Custom validation for the form to ensure that start times are before end times
        and that both start and end times are provided if one is provided.
        """
        cleaned_data = super().clean()
        morning_start = cleaned_data.get('morning_start')
        morning_end = cleaned_data.get('morning_end')
        evening_start = cleaned_data.get('evening_start')
        evening_end = cleaned_data.get('evening_end')

        # Validate morning shift
        if morning_start is not None and morning_end is not None:
            if morning_start >= morning_end:
                self.add_error('morning_start', "ساعت شروع صبح باید کمتر از ساعت پایان باشد")
                self.add_error('morning_end', "ساعت پایان صبح باید بیشتر از ساعت شروع باشد")

        # Validate evening shift
        if evening_start is not None and evening_end is not None:
            if evening_start >= evening_end:
                self.add_error('evening_start', "ساعت شروع عصر باید کمتر از ساعت پایان باشد")
                self.add_error('evening_end', "ساعت پایان عصر باید بیشتر از ساعت شروع باشد")

        # Ensure both start and end times are provided if one is provided
        if morning_start is not None and morning_end is None:
            self.add_error('morning_end', "لطفاً ساعت پایان صبح را وارد کنید")
        if morning_end is not None and morning_start is None:
            self.add_error('morning_start', "لطفاً ساعت شروع صبح را وارد کنید")
        if evening_start is not None and evening_end is None:
            self.add_error('evening_end', "لطفاً ساعت پایان عصر را وارد کنید")
        if evening_end is not None and evening_start is None:
            self.add_error('evening_start', "لطفاً ساعت شروع عصر را وارد کنید")

        return cleaned_data
    
class BannerForm(forms.ModelForm):
    """
    Form for creating and updating Banner instances.
    """
    class Meta:
        model = Banner
        fields = ['title', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام بنر'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'نام بنر',
            'image': 'تصویر بنر',
        }
        error_messages = {
            'title': {
                'required': "لطفاً نام بنر را وارد کنید.",
                'unique': "بنر با این نام قبلاً وجود دارد.",
                'max_length': "عنوان نمی‌تواند بیشتر از 150 کاراکتر باشد",
            },
            'image': {
                'required': "لطفا عکس را وارد کنید",
            }
        }