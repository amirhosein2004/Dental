from utils.common_imports import forms
from .models import Gallery, Image

class GalleryForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = ['category']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'category': 'دسته‌بندی',
        }
        error_messages = {
            'category': {
                'required': "لطفاً دسته‌بندی را انتخاب کنید",
            },
        }

class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png',  # فقط jpg و png
            }),
        }
        labels = {
            'image': 'تصویر',
        }
        error_messages = {
            'image': {
                'required': "لطفاً یک تصویر آپلود کنید",
            },
        }