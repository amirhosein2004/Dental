from django import forms

from apps.about.models import Branch
from utils.data.social import PLATFORMS, to_handle, to_url

from .models import Doctor


class DoctorForm(forms.ModelForm):
    """
    Form for creating and updating Doctor instances.

    Social fields take a bare handle, not a URL: the doctor types
    ``dr.saeedebabaee`` and the form stores
    ``https://instagram.com/dr.saeedebabaee``. Storing the full URL keeps every
    consumer template able to use the value straight as an ``href``. A pasted
    full URL is still accepted and reduced to its handle.
    """

    SOCIAL_FIELDS = tuple(PLATFORMS)

    class Meta:
        model = Doctor
        fields = ['description', 'twitter', 'instagram', 'telegram', 'linkedin']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً: متخصص داخلی با 10 سال تجربه',
                'rows': 4
            }),
        }
        labels = {
            'description': 'توضیحات',
            'twitter': 'توییتر',
            'instagram': 'اینستاگرام',
            'telegram': 'تلگرام',
            'linkedin': 'لینکدین',
        }
        error_messages = {
            'description': {
                'required': "لطفاً توضیحات خود را وارد کنید",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.SOCIAL_FIELDS:
            _base, label = PLATFORMS[name]
            # Swap the model's URLField for a plain CharField: a bare handle is
            # not a valid URL, so URLField's validator would reject it.
            self.fields[name] = forms.CharField(
                required=False,
                max_length=100,
                label=self.Meta.labels[name],
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    # Latin-only placeholder: the input is forced LTR, and a
                    # mixed Persian/Latin string reorders confusingly there.
                    'placeholder': 'dr.babaei',
                    'dir': 'ltr',
                    'autocomplete': 'off',
                }),
            )
            # Show the stored URL as just its handle when editing.
            if self.instance and self.instance.pk:
                self.initial[name] = to_handle(getattr(self.instance, name), name)

    def social_fields(self):
        """
        Yield ``(bound_field, prefix)`` for the template.

        The prefix can't ride along in ``widget.attrs`` because Django's
        template variable syntax cannot resolve a key containing hyphens
        (``data-social-prefix``).
        """
        for name in self.SOCIAL_FIELDS:
            yield self[name], PLATFORMS[name][1]

    def _clean_social(self, name):
        return to_url(self.cleaned_data.get(name, ''), name)

    def clean_instagram(self):
        return self._clean_social('instagram')

    def clean_telegram(self):
        return self._clean_social('telegram')

    def clean_twitter(self):
        return self._clean_social('twitter')

    def clean_linkedin(self):
        return self._clean_social('linkedin')


class DoctorResumeForm(forms.ModelForm):
    """
    The CV behind a doctor's public page.

    Every field here already existed on ``Doctor`` and was already rendered on
    the profile page — the specialty, the degree, the medical-council number,
    the education and work history. None of them had a form: the only way to
    fill any of it in was the Django admin, which means a superuser account,
    which means most of the page shipped empty.

    That matters more here than on a typical bio page. Dentistry is a YMYL
    subject, so demonstrated credentials are ranking input, and the profile is
    what a search for the doctor's own name lands on.
    """

    class Meta:
        model = Doctor
        fields = [
            'headline', 'specialty', 'degree', 'license_number',
            'experience_years', 'education', 'experience', 'certifications',
            'memberships', 'branches', 'meta_description',
            'is_published', 'order',
        ]
        labels = {
            'headline': 'عنوان کوتاه',
            'specialty': 'تخصص',
            'degree': 'مدرک تحصیلی',
            'license_number': 'شماره نظام پزشکی',
            'experience_years': 'سال‌های تجربه',
            'education': 'تحصیلات',
            'experience': 'سوابق کاری',
            'certifications': 'دوره‌ها و گواهی‌نامه‌ها',
            'memberships': 'عضویت‌ها',
            'branches': 'مطب‌های محل کار',
            'meta_description': 'توضیح متا',
            'is_published': 'نمایش صفحه‌ی عمومی رزومه',
            'order': 'ترتیب نمایش',
        }
        widgets = {
            'headline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'دندانپزشک، متخصص ایمپلنت و زیبایی',
            }),
            'specialty': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ایمپلنت و جراحی دهان و دندان',
            }),
            'degree': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'دکترای حرفه‌ای دندانپزشکی',
            }),
            'license_number': forms.TextInput(attrs={
                'class': 'form-control', 'dir': 'ltr', 'inputmode': 'numeric',
                'placeholder': '128456',
            }),
            'experience_years': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 0, 'max': 70, 'dir': 'ltr',
            }),
            'education': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'دکترای دندانپزشکی — دانشگاه علوم پزشکی مشهد، ۱۳۹۲',
            }),
            'experience': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'مسئول بخش ایمپلنت کلینیک … ، ۱۳۹۵ تا ۱۳۹۹',
            }),
            'certifications': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'دوره‌ی پیشرفته‌ی جراحی پیزو، ۱۳۹۷',
            }),
            'memberships': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'عضو انجمن دندانپزشکی ایران',
            }),
            'branches': forms.CheckboxSelectMultiple(),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'خالی بگذارید تا از عنوان کوتاه و تخصص ساخته شود',
            }),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

    #: Site-wide switches, not credentials. They decide whether the profile is
    #: public at all, where it sorts among the others and what Google prints
    #: under its title — three answers that belong to whoever runs the site,
    #: not to each doctor editing their own CV.
    SUPERUSER_FIELDS = ('meta_description', 'is_published', 'order')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # `order` has a model default but no `blank=True`, so a submit that
        # left the box alone would fail on a field nobody was asked about.
        self.fields['order'].required = False
        # Set explicitly so the checkbox list renders in the same order as the
        # pages that read it.
        self.fields['branches'].queryset = Branch.objects.all()

        # Dropped from the form, not hidden in the template: a hidden field is
        # still bound, so a doctor saving their CV would post an empty value
        # over the superuser's meta text and unpublish their own page.
        if user is not None and not user.is_superuser:
            for name in self.SUPERUSER_FIELDS:
                self.fields.pop(name, None)

    def clean_order(self):
        return self.cleaned_data.get('order') or 0

    def has_site_fields(self):
        """Whether this render carries the superuser-only block."""
        return 'is_published' in self.fields

    def intro_fields(self):
        """The single-line credential fields, in reading order."""
        for name in ('headline', 'specialty', 'degree',
                     'license_number', 'experience_years'):
            yield self[name]

    def line_fields(self):
        """
        The four "one item per line" fields, for the template.

        They share a hint and a layout, and listing them here keeps the
        template from repeating the same six lines of markup four times.
        """
        for name in ('education', 'experience', 'certifications', 'memberships'):
            yield self[name]
