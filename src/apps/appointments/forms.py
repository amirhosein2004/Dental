from django import forms

from .models import Appointment, AvailabilitySlot
from .weeks import WEEKDAYS


class AvailabilitySlotForm(forms.ModelForm):
    """Staff-side: declare one recurring opening."""

    class Meta:
        model = AvailabilitySlot
        fields = ['doctor', 'branch', 'weekday', 'time', 'is_active']
        labels = {
            'doctor': 'پزشک',
            'branch': 'مطب',
            'weekday': 'روز هفته',
            'time': 'ساعت',
            'is_active': 'فعال',
        }
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'weekday': forms.Select(attrs={'class': 'form-control'}, choices=WEEKDAYS),
            'time': forms.TimeInput(
                attrs={'class': 'form-control', 'type': 'time'}, format='%H:%M'
            ),
            'is_active': forms.CheckboxInput(),
        }
        error_messages = {
            'branch': {'required': 'لطفاً مطب را انتخاب کنید'},
            'weekday': {'required': 'لطفاً روز هفته را انتخاب کنید'},
            'time': {'required': 'لطفاً ساعت را وارد کنید'},
        }

    def __init__(self, *args, doctor=None, **kwargs):
        super().__init__(*args, **kwargs)

        # A patient has to be told which city they are booking, so the branch
        # is required here even though the column is nullable — nullable only
        # so that rows created before the field existed stay valid.
        self.fields['branch'].required = True
        self.fields['branch'].empty_label = 'مطب را انتخاب کنید'

        if doctor is not None:
            # A doctor manages only their own schedule; the field is fixed and
            # hidden so a crafted POST cannot assign a slot to a colleague.
            self.fields['doctor'].queryset = self.fields['doctor'].queryset.filter(pk=doctor.pk)
            self.fields['doctor'].initial = doctor
            self.fields['doctor'].widget = forms.HiddenInput()

            # Offer only the practices this doctor actually works at, when that
            # is recorded. A doctor with no branches set is not narrowed —
            # an empty list would leave them unable to add any slot at all.
            own = doctor.branches.all()
            if own.exists():
                self.fields['branch'].queryset = own

    def clean(self):
        cleaned = super().clean()
        doctor, weekday, time = (
            cleaned.get('doctor'), cleaned.get('weekday'), cleaned.get('time'),
        )
        if doctor and weekday is not None and time:
            clash = AvailabilitySlot.objects.filter(
                doctor=doctor, weekday=weekday, time=time
            ).exclude(pk=self.instance.pk)
            if clash.exists():
                raise forms.ValidationError('این زمان قبلاً برای همین پزشک ثبت شده است')
        return cleaned


class AppointmentForm(forms.ModelForm):
    """
    Public-side: a patient claims a slot.

    The slot and the week are supplied by the view, never by the browser, so a
    tampered POST cannot book an inactive slot or reserve a future week.
    """

    class Meta:
        model = Appointment
        fields = ['full_name', 'national_code', 'phone', 'note']
        labels = {
            'full_name': 'نام و نام خانوادگی',
            'national_code': 'کد ملی',
            'phone': 'شماره تماس',
            'note': 'توضیحات (اختیاری)',
        }
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'مثلاً: مریم احمدی',
                'autocomplete': 'name',
            }),
            'national_code': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '۱۰ رقم',
                'inputmode': 'numeric', 'maxlength': '10', 'dir': 'ltr',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '۰۹۱۲۳۴۵۶۷۸۹',
                'inputmode': 'tel', 'maxlength': '11', 'dir': 'ltr',
                'autocomplete': 'tel',
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'اگر نکته‌ای هست بنویسید',
            }),
        }
        error_messages = {
            'full_name': {'required': 'لطفاً نام و نام خانوادگی را وارد کنید'},
            'national_code': {'required': 'لطفاً کد ملی را وارد کنید'},
            'phone': {'required': 'لطفاً شماره تماس را وارد کنید'},
        }

    def clean_national_code(self):
        # Persian digits are what a phone keyboard produces by default.
        value = (self.cleaned_data.get('national_code') or '').strip()
        return value.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789'))

    def clean_phone(self):
        value = (self.cleaned_data.get('phone') or '').strip()
        return value.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789'))
