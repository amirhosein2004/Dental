from django import forms

from .models import About, Branch


class AboutForm(forms.ModelForm):
    """
    Form for the singleton About row.

    Address and phone are deliberately absent. They belong to a location, and
    the site has two — so they are edited per practice on ``BranchForm``,
    which is also the only place anything reads them from. What is left here
    is what the "درباره ما" page is actually for: who the practice is, not
    where it is.
    """

    class Meta:
        model = About
        fields = ['name', 'email', 'description', 'image']
        labels = {
            'name': 'نام مطب',
            'email': 'ایمیل',
            'description': 'توضیحات',
            'image': 'تصویر',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام مطب (مثال: مطب دکتر احمدی)',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ایمیل مطب (مثال: clinic@example.com)',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'معرفی مطب و تیم درمانی',
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
            }),
        }
        error_messages = {
            'name': {
                'required': "لطفاً نام مطب را وارد کنید.",
                'max_length': "نام نمی‌تواند بیشتر از ۱۰۰ کاراکتر باشد.",
            },
            'email': {
                'required': "لطفاً ایمیل مطب را وارد کنید.",
                'invalid': "لطفاً یک ایمیل معتبر وارد کنید.",
            },
            'description': {'required': "لطفا توضیحات خود را وارد کنید"},
            'image': {'required': "لطفا عکس خود را وارد کنید"},
        }


class BranchForm(forms.ModelForm):
    """
    Form for one physical practice.

    Every field the footer, the contact page and the LocalBusiness JSON-LD
    read is editable here — opening hours included. There is no site-wide
    hours row any more: two practices in two cities do not keep the same
    hours, and one shared block meant whichever city it did not describe was
    being told the wrong thing.
    """

    class Meta:
        model = Branch
        fields = [
            'city', 'title', 'address', 'postal_code', 'phone', 'extra_phones',
            'hours', 'map_embed_url', 'map_link', 'latitude', 'longitude',
            'order',
        ]
        labels = {
            'city': 'شهر',
            'title': 'عنوان نمایشی',
            'address': 'آدرس',
            'postal_code': 'کد پستی',
            'phone': 'تلفن اصلی',
            'extra_phones': 'شماره‌های دیگر',
            'hours': 'ساعات کاری این مطب',
            'map_embed_url': 'لینک embed نقشه',
            'map_link': 'لینک مسیریابی',
            'latitude': 'عرض جغرافیایی',
            'longitude': 'طول جغرافیایی',
            'order': 'ترتیب نمایش',
        }
        widgets = {
            'city': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'مثلاً: مشهد',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'مطب دندانپزشکی مشهد',
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'آدرس کامل مطب',
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control', 'inputmode': 'numeric',
                'maxlength': '10', 'dir': 'ltr',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '05147247247',
                'inputmode': 'tel', 'maxlength': '11', 'dir': 'ltr',
            }),
            'extra_phones': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 'dir': 'ltr',
                'placeholder': '05147247247\n09121234567',
            }),
            'hours': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': (
                    'شنبه تا چهارشنبه: ۹ الی ۱۳ و ۱۶ الی ۲۰\n'
                    'پنجشنبه: ۹ الی ۱۳\n'
                    'جمعه: تعطیل'
                ),
            }),
            'map_embed_url': forms.URLInput(attrs={
                'class': 'form-control', 'dir': 'ltr',
                'placeholder': 'https://www.google.com/maps/embed?pb=…',
            }),
            'map_link': forms.URLInput(attrs={
                'class': 'form-control', 'dir': 'ltr',
                'placeholder': 'https://maps.app.goo.gl/…',
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control', 'step': 'any', 'dir': 'ltr',
                'placeholder': '36.297',
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control', 'step': 'any', 'dir': 'ltr',
                'placeholder': '59.606',
            }),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
        error_messages = {
            'city': {
                'required': 'لطفاً نام شهر را وارد کنید',
                'unique': 'برای این شهر قبلاً مطبی ثبت شده است',
            },
            'address': {'required': 'لطفاً آدرس مطب را وارد کنید'},
            'phone': {'required': 'لطفاً تلفن مطب را وارد کنید'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Model default, no `blank=True` — which would otherwise make the form
        # reject a submit that left the ordering box empty.
        self.fields['order'].required = False

    def clean_order(self):
        return self.cleaned_data.get('order') or 0
