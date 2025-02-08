from django import forms
from .models import Gallery, Image
from core.models import Category

class GalleryForm(forms.ModelForm):
    # category = forms.ModelChoiceField(queryset=Category.objects.all(), empty_label='انتخاب کنید')

    class Meta:
        model = Gallery
        fields = ['category']

class ImageForm(forms.ModelForm):
    image = forms.ImageField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

    class Meta:
        model = Image
        fields = ['image']
