from utils.common_imports import forms, get_user_model, ValidationError

User = get_user_model()


class CustomUserDoctorUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['image', 'username', 'email', 'first_name', 'last_name']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/jpeg,image/png',
                'autocomplete': 'off'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام کاربری',
                'autocomplete': 'off'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً: ahmad@example.com',
                'autocomplete': 'off'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً: احمد',
                'autocomplete': 'off'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً: احمدی',
                'autocomplete': 'off'
            }),
        }
        labels = {
            'image': 'تصویر پروفایل',
            'username': 'نام کاربری',
            'email': 'ایمیل',
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
        }
        error_messages = {
            'image': {'required': 'لطفاً تصویر پروفایل را آپلود کنید'},
            'username': {
                'required': 'لطفاً نام کاربری را وارد کنید',
            },
            'email': {
                'required': 'لطفاً ایمیل خود را وارد کنید',
            },
            'first_name': {'required': 'لطفاً نام خود را وارد کنید'},
            'last_name': {'required': 'لطفاً نام خانوادگی خود را وارد کنید'},
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise ValidationError("این نام کاربری قبلاً استفاده شده است")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError("این ایمیل قبلاً ثبت شده است")
        return email