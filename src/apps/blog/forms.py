from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import BlogPost


class BlogPostForm(forms.ModelForm):
    """
    Form for creating and updating BlogPost instances. Slug is auto-generated
    from the title (Unicode-aware) so the author doesn't need to think about
    it — Persian titles produce Persian slugs, collisions are resolved by
    appending a numeric suffix.
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
            'content': CKEditor5Widget(attrs={
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
        title = self.cleaned_data.get('title')
        if title and BlogPost.objects.exclude(pk=self.instance.pk).filter(title=title).exists():
            raise ValidationError("این عنوان قبلاً ثبت شده است")
        return title

    def save(self, commit=True):
        # Auto-slug from title on create (or when title changed on update).
        # allow_unicode=True keeps Persian characters instead of stripping to ''.
        if self.cleaned_data.get('title') and (
            not self.instance.slug or 'title' in self.changed_data
        ):
            base = slugify(self.cleaned_data['title'], allow_unicode=True) or 'blog'
            slug = base
            n = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
                n += 1
                slug = f'{base}-{n}'
            self.instance.slug = slug
        return super().save(commit=commit)
