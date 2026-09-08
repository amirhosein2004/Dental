from django import forms

from .models import PricingCategory, PricingItem


class PricingItemForm(forms.ModelForm):
    """Form for creating and updating pricing items."""

    class Meta:
        model = PricingItem
        fields = ['category', 'title', 'price']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان خدمت را وارد کنید',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'قیمت به تومان',
                'min': '0',
            }),
        }
        labels = {
            'category': 'دسته‌بندی',
            'title': 'عنوان خدمت',
            'price': 'قیمت (تومان)',
        }
        error_messages = {
            'title': {
                'required': "لطفاً عنوان را وارد کنید",
                'max_length': "عنوان باید حداکثر 500 کاراکتر باشد",
            },
            'price': {
                'required': "لطفاً قیمت را وارد کنید",
                'min_value': "قیمت باید بیشتر از صفر باشد",
                'max_value': "قیمت باید حداکثر 20 رقم باشد",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        self.fields['category'].empty_label = 'بدون دسته‌بندی'


class PricingCategoryForm(forms.ModelForm):
    """Form for creating and updating pricing categories."""

    class Meta:
        model = PricingCategory
        fields = ['name', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام دسته (مثال: ایمپلنت، عصب‌کشی)',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0',
            }),
        }
        labels = {
            'name': 'نام دسته',
            'order': 'ترتیب نمایش',
        }
        error_messages = {
            'name': {
                'required': "لطفاً نام دسته را وارد کنید",
                'unique': "دسته‌ای با این نام قبلاً ثبت شده است",
                'max_length': "نام نمی‌تواند بیشتر از ۱۵۰ کاراکتر باشد",
            },
        }
