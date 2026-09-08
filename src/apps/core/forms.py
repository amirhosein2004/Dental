from django import forms

from .models import Category


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
