from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
)
from django.urls import reverse_lazy

from apps.accounts.forms import PasswordResetCaptchaForm, SetPasswordCaptchaForm
from utils.http.mixins import RateLimitMixin, RedirectIfAuthenticatedMixin


class _CaptchaFormViewMixin:
    """Injects the current request into the form so the math captcha can use it."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class CustomPasswordResetView(RateLimitMixin, RedirectIfAuthenticatedMixin, _CaptchaFormViewMixin, PasswordResetView):
    rate_limit = '5/m'
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')
    form_class = PasswordResetCaptchaForm


class CustomPasswordResetDoneView(RedirectIfAuthenticatedMixin, PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(RateLimitMixin, RedirectIfAuthenticatedMixin, _CaptchaFormViewMixin, PasswordResetConfirmView):
    rate_limit = '5/m'
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    form_class = SetPasswordCaptchaForm


class CustomPasswordResetCompleteView(RedirectIfAuthenticatedMixin, PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'
