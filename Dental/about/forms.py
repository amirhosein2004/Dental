from django import forms
from .models import Clinic, Doctor, Service

class ClinicForm(forms.ModelForm):
    class Meta:
        model = Clinic
        fields = ['name', 'address', 'phone', 'description', 'image']

class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['description', 'image', 'twitter', 'instagram', 'telegram', 'linkedin']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # افزودن ویژگی disabled به همه فیلدها
        for field in self.fields.values():
            field.widget.attrs.update({'disabled': 'disabled'})

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['title', 'description', 'icon']
