from utils.common_imports import forms, ValidationError
from .models import Service

class ServiceForm(forms.ModelForm):
    """
    A form for creating and updating Service instances.
    """
    class Meta:
        model = Service
        fields = ['title', 'description', 'image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً: مشاوره پزشکی آنلاین'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً: ارائه خدمات مشاوره پزشکی به صورت آنلاین با پزشکان مجرب',
                'rows': 5
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png'  # Limit file formats in the browser
            }),
        }
        labels = {
            'title': 'عنوان',
            'description': 'توضیحات',
            'image': 'تصویر',
        }
        error_messages = {
            'title': {
                'required': "لطفاً عنوان خدمت را وارد کنید",
                'max_length': 'عنوان نمی‌تواند بیشتر از ۲۰۰ کاراکتر باشد'
            },
            'description': {
                'required': "لطفاً توضیحات خدمت را وارد کنید",
            },
            'image': {
                'required': "لطفاً تصویر خدمت را آپلود کنید",
            },
        }

    def clean_title(self):
        """
        Custom validation for the title field to ensure uniqueness.
        """
        title = self.cleaned_data.get('title')
        if title and Service.objects.exclude(pk=self.instance.pk).filter(title=title).exists():
            raise ValidationError("این عنوان قبلاً ثبت شده است")
        return title