from django import forms
from django.core.exceptions import ValidationError
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import Service, ServiceFAQ


class ServiceForm(forms.ModelForm):
    """
    A form for creating and updating Service instances.

    It used to expose three fields — title, description, image — while the
    model carried eight. The four it left out were not incidental: `content`
    is the body text the treatment page ranks on, and the two `meta_` fields
    are the title and snippet a search result shows. A doctor filling this in
    could therefore publish a page with no body at all, and the only way to
    add one was the Django admin, i.e. a superuser account.

    `description` is a rich-text field too, on a deliberately small toolbar.
    It is the blurb on the card and the lead paragraph on the treatment page,
    and it was a plain 500-character box — no way to emphasise the one phrase
    that matters, and a cap that counted characters the writer could not see.
    """

    class Meta:
        model = Service
        fields = [
            'title', 'description', 'content', 'image',
            'meta_title', 'meta_description', 'order',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً: ایمپلنت دندان'
            }),
            'description': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='simple',
            ),
            'content': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='default',
            ),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png'  # Limit file formats in the browser
            }),
            'meta_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'خالی بگذارید تا از عنوان خدمت ساخته شود',
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'خالی بگذارید تا از توضیح کوتاه ساخته شود',
            }),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
        labels = {
            'title': 'عنوان',
            'description': 'توضیح کوتاه',
            'content': 'متن کامل',
            'image': 'تصویر',
            'meta_title': 'عنوان متا',
            'meta_description': 'توضیح متا',
            'order': 'ترتیب نمایش',
        }
        error_messages = {
            'title': {
                'required': "لطفاً عنوان خدمت را وارد کنید",
                'max_length': 'عنوان نمی‌تواند بیشتر از ۲۰۰ کاراکتر باشد'
            },
            'description': {
                'required': "لطفاً توضیح کوتاه خدمت را وارد کنید",
            },
            'image': {
                'required': "لطفاً تصویر خدمت را آپلود کنید",
            },
        }

    #: Fields only a superuser is shown. Overriding the meta title and the
    #: snippet is a search-console job, not a clinical one — the model builds
    #: both from the treatment's own title and blurb when they are blank, so
    #: a doctor who never sees them still ships a correctly tagged page.
    SEO_FIELDS = ('meta_title', 'meta_description')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # `order` has a model default but no `blank=True`, which makes the form
        # field required — so a submit that simply omits it fails with "This
        # field is required" on a field the user was never asked about.
        self.fields['order'].required = False

        # Dropped rather than hidden. A hidden input still posts, so a doctor
        # editing a treatment would silently blank whatever a superuser had
        # written in these two boxes; a field the form does not carry is a
        # field `construct_instance` does not touch.
        if user is not None and not user.is_superuser:
            for name in self.SEO_FIELDS:
                self.fields.pop(name, None)

    def clean_order(self):
        return self.cleaned_data.get('order') or 0

    def clean_title(self):
        """
        Custom validation for the title field to ensure uniqueness.
        """
        title = self.cleaned_data.get('title')
        if title and Service.objects.exclude(pk=self.instance.pk).filter(title=title).exists():
            raise ValidationError("این عنوان قبلاً ثبت شده است")
        return title


class ServiceFAQForm(forms.ModelForm):
    """One question/answer pair, edited inline on its own treatment's form."""

    class Meta:
        model = ServiceFAQ
        fields = ['question', 'answer', 'order']
        labels = {
            'question': 'سؤال',
            'answer': 'پاسخ',
            'order': 'ترتیب',
        }
        widgets = {
            'question': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً: ایمپلنت چقدر طول می‌کشد؟',
            }),
            'answer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'پاسخ کوتاه و روشن، همان‌طور که به بیمار توضیح می‌دهید',
            }),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order'].required = False

    def clean_order(self):
        return self.cleaned_data.get('order') or 0


# `extra=0`: the form opens with exactly the questions this treatment already
# has, and a button adds a row when the writer wants one. It used to open with
# two blank rows whether or not anyone wanted them, which read as two required
# questions and left a tall block of empty boxes under every treatment.
#
# `can_delete` is what makes an existing question removable at all — without
# it the only way to drop one was the Django admin.
ServiceFAQFormSet = forms.inlineformset_factory(
    Service,
    ServiceFAQ,
    form=ServiceFAQForm,
    extra=0,
    can_delete=True,
)


class StandaloneServiceFAQForm(forms.ModelForm):
    """
    One question written from the FAQ panel rather than from a treatment form.

    A ``ServiceFAQ`` cannot exist without a treatment, so this form asks which
    one first. That is the whole difference from ``ServiceFAQForm``: the
    inline version already knows its parent from the formset.
    """

    class Meta:
        model = ServiceFAQ
        fields = ['service', 'question', 'answer', 'order']
        labels = {
            'service': 'این سؤال مربوط به کدام خدمت است؟',
            'question': 'سؤال',
            'answer': 'پاسخ',
            'order': 'ترتیب',
        }
        widgets = {
            'service': forms.Select(attrs={'class': 'form-control'}),
            'question': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً: ایمپلنت چقدر طول می‌کشد؟',
            }),
            'answer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'پاسخ کوتاه و روشن، همان‌طور که به بیمار توضیح می‌دهید',
            }),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
        error_messages = {
            'service': {'required': 'لطفاً خدمت مربوط به این سؤال را انتخاب کنید'},
            'question': {'required': 'لطفاً متن سؤال را وارد کنید'},
            'answer': {'required': 'لطفاً پاسخ سؤال را وارد کنید'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order'].required = False
        self.fields['service'].empty_label = 'یک خدمت را انتخاب کنید'

    def clean_order(self):
        return self.cleaned_data.get('order') or 0
