from utils.common_imports import reverse_lazy, redirect, messages
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView, 
    PasswordResetConfirmView, PasswordResetCompleteView
)
from accounts.forms import PasswordResetCaptchaForm, SetPasswordCaptchaForm
from utils.mixins import RateLimitMixin, RedirectIfAuthenticatedMixin


class CustomPasswordResetView(RateLimitMixin, RedirectIfAuthenticatedMixin,  PasswordResetView):
    rate_limit = '5/m'
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')
    form_class = PasswordResetCaptchaForm

class CustomPasswordResetDoneView(RedirectIfAuthenticatedMixin, PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'

class CustomPasswordResetConfirmView(RateLimitMixin, RedirectIfAuthenticatedMixin, PasswordResetConfirmView):
    rate_limit = '5/m'
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    form_class = SetPasswordCaptchaForm

class CustomPasswordResetCompleteView(RedirectIfAuthenticatedMixin, PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'