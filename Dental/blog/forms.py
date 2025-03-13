# Project-specific imports from common_imports
from utils.common_imports import forms

# Imports from local models
from .models import BlogPost 

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'categories', 'content', 'image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان پست',
            }),
            'categories': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'محتوای پست',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png',  # محدود کردن نوع فایل توی مرورگر
            }),
        }
        labels = {
            'title': 'عنوان',
            'categories': 'دسته‌بندی‌ها',
            'content': 'محتوا',
            'image': 'تصویر',
        }
        error_messages = {
            'title': {
                'required': "لطفاً عنوان پست را وارد کنید",
                'max_length': "عنوان نمی‌تواند بیشتر از ۲۰۰ کاراکتر باشد",
            },
            'categories': {
                'required': "لطفاً حداقل یک دسته‌بندی انتخاب کنید",
            },
            'content': {
                'required': "لطفاً محتوای پست را وارد کنید",
            },
            'image': {
                'required': "لطفاً یک تصویر انتخاب کنید",
            },
        }