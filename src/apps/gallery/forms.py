from django import forms

from .models import Gallery, Image

class GalleryForm(forms.ModelForm):
    """
    Form for creating and updating Gallery instances.
    """
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Django's placeholder for an unselected choice is a row of dashes,
        # which says nothing about what the control wants.
        self.fields['category'].empty_label = 'یک دسته‌بندی انتخاب کنید'


class ImageForm(forms.ModelForm):
    """
    Form for uploading images to the Gallery.
    """
    class Meta:
        model = Image
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png',  # Only jpg and png
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