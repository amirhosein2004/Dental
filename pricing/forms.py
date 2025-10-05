from utils.common_imports import forms
from .models import PricingItem


class PricingItemForm(forms.ModelForm):
    """
    Form for creating and updating pricing items.
    """
    class Meta:
        model = PricingItem
        fields = ['title', 'price']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان خدمت را وارد کنید'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'قیمت به تومان',
                'min': '0'
            }),
        }
        error_messages = {
            'title': {
                'required': "لطفاً عنوان را وارد کنید",
                'max_length': "عنوان باید حداکثر 500 کاراکتر باشد",
            },
            'price': {
                'required': "لطفاً قیمت را وارد کنید",
                'min_value': "قیمت باید بیشتر از صفر باشد",  
            },
        }
