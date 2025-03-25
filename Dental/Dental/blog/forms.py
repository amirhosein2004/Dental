# Project-specific imports from common_imports
from utils.common_imports import forms, ValidationError
from django_ckeditor_5.widgets import CKEditor5Widget

# Imports from local models
from .models import BlogPost 

class BlogPostForm(forms.ModelForm):
    """
    A form for creating and updating BlogPost instances.
    """
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
            'content': CKEditor5Widget(attrs={  # add CKEditor 5 
                'class': 'django_ckeditor_5',
            }, config_name='default'),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png',
            }),
        }
        labels = {
            'title': 'عنوان', 
            'categories': 'دسته‌بندی‌ها', 
            'content': 'محتوا', 
            'image': 'تصویر', 
        }
        # Error handling
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
    def clean_title(self):
        """
        Custom validation for the title field to ensure uniqueness.
        """
        title = self.cleaned_data.get('title')
        if title and BlogPost.objects.exclude(pk=self.instance.pk).filter(title=title).exists():
            raise ValidationError("این عنوان قبلاً ثبت شده است")
        return title