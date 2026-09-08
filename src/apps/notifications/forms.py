from django import forms

from .models import ContactGroup
from .phones import parse_numbers


class ContactGroupForm(forms.ModelForm):
    """Create/edit a reusable list of numbers."""

    class Meta:
        model = ContactGroup
        fields = ['name', 'description', 'numbers']
        labels = {
            'name': 'نام گروه',
            'description': 'توضیح (اختیاری)',
            'numbers': 'شماره‌ها',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'مثلاً: بیماران ایمپلنت',
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'برای یادآوری اینکه این گروه چیست',
            }),
            'numbers': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 8, 'dir': 'ltr',
                'placeholder': '09121234567, 09351112233\n09024445566',
            }),
        }
        error_messages = {
            'name': {
                'required': 'لطفاً نام گروه را وارد کنید',
                'unique': 'گروهی با این نام قبلاً ثبت شده است',
            },
        }

    def clean_numbers(self):
        raw = self.cleaned_data.get('numbers', '')
        valid, invalid = parse_numbers(raw)
        if not valid:
            raise forms.ValidationError('هیچ شماره‌ی معتبری پیدا نشد')

        # Reported, not silently dropped — the operator can only fix a typo
        # they are told about, and a group is saved once but sent to for months.
        self.invalid_tokens = invalid
        return '\n'.join(valid)


class GroupCheckboxSelect(forms.CheckboxSelectMultiple):
    """
    Checkbox list that carries each group's numbers on the input itself.

    The bulk-SMS page shows a live recipient count before sending, and that
    count must de-duplicate across ticked groups — which the browser can only
    do if it knows the membership. The server still recomputes the merge; this
    is a pre-flight estimate, never the source of truth.
    """

    def create_option(self, name, value, *args, **kwargs):
        option = super().create_option(name, value, *args, **kwargs)
        group = getattr(value, 'instance', None)
        if group is not None:
            option['attrs']['data-numbers'] = ','.join(group.number_list)
            option['attrs']['data-count'] = group.member_count
        return option


class BulkSmsForm(forms.Form):
    """
    Compose a batch: pick saved groups, and/or paste extra numbers.

    Both sources are merged and de-duplicated, so a number that appears in two
    groups — or in a group *and* the paste box — is still texted once.
    """

    # Every recipient costs money and there is no undo once the task is queued.
    # A paste that lands ten times larger than intended — a whole exported
    # column instead of one cell — should be refused and looked at, not billed.
    # Raise this deliberately if a genuine campaign needs more.
    MAX_RECIPIENTS = 500

    groups = forms.ModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        label='گروه‌ها',
        widget=GroupCheckboxSelect,
    )
    numbers = forms.CharField(
        label='شماره‌های دیگر',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 5, 'dir': 'ltr',
            'placeholder': '09121234567, 09351112233',
        }),
        help_text='با فاصله، کاما یا خط جدید جدا کنید. تکراری‌ها خودکار حذف می‌شوند.',
    )
    message = forms.CharField(
        label='متن پیام',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 5, 'placeholder': 'متن پیامک...',
        }),
        max_length=1000,
    )

    def clean(self):
        cleaned = super().clean()

        # Groups first so their order is stable across sends, then the
        # ad-hoc paste box. dict.fromkeys keeps first-seen order while
        # collapsing duplicates across both sources.
        merged = []
        for group in cleaned.get('groups') or []:
            merged.extend(group.number_list)

        typed, invalid = parse_numbers(cleaned.get('numbers', ''))
        merged.extend(typed)

        deduped = list(dict.fromkeys(merged))
        if not deduped:
            raise forms.ValidationError(
                'هیچ شماره‌ای انتخاب نشده — یک گروه انتخاب کنید یا شماره وارد کنید'
            )

        if len(deduped) > self.MAX_RECIPIENTS:
            raise forms.ValidationError(
                f'{len(deduped)} گیرنده انتخاب شده و سقف هر ارسال '
                f'{self.MAX_RECIPIENTS} شماره است. لطفاً فهرست را به چند بخش '
                'تقسیم کنید یا سقف را در تنظیمات بالا ببرید.'
            )

        cleaned['parsed_numbers'] = deduped
        cleaned['invalid_tokens'] = invalid
        return cleaned
