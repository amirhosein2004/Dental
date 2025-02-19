from django import forms
from .models import Category, Clinic

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class ClinicForm(forms.ModelForm):
    class Meta:
        model = Clinic
        fields = ['name', 'address', 'phone', 'description', 'image']