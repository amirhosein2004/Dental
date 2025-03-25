from utils.common_imports import reverse_lazy
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView, 
    PasswordResetConfirmView, PasswordResetCompleteView
)
from accounts.forms import PasswordResetCaptchaForm, SetPasswordCaptchaForm
from utils.mixins import RateLimitMixin, RedirectIfAuthenticatedMixin

# Custom views for handling password reset process with additional features like rate limiting and captcha

class CustomPasswordResetView(RateLimitMixin, RedirectIfAuthenticatedMixin, PasswordResetView):
    """
    Custom view for initiating the password reset process.
    Inherits from RateLimitMixin to limit the number of requests and RedirectIfAuthenticatedMixin to redirect authenticated users.
    """
    rate_limit = '5/m' 
    template_name = 'accounts/password_reset.html'  
    email_template_name = 'accounts/password_reset_email.html'  # Template for password reset email
    success_url = reverse_lazy('accounts:password_reset_done')  # URL to redirect to on successful password reset request
    form_class = PasswordResetCaptchaForm  

class CustomPasswordResetDoneView(RedirectIfAuthenticatedMixin, PasswordResetDoneView):
    """
    Custom view for displaying the password reset done page.
    Inherits from RedirectIfAuthenticatedMixin to redirect authenticated users.
    """
    template_name = 'accounts/password_reset_done.html'  

class CustomPasswordResetConfirmView(RateLimitMixin, RedirectIfAuthenticatedMixin, PasswordResetConfirmView):
    """
    Custom view for confirming the password reset.
    Inherits from RateLimitMixin to limit the number of requests and RedirectIfAuthenticatedMixin to redirect authenticated users.
    """
    rate_limit = '5/m' 
    template_name = 'accounts/password_reset_confirm.html'  
    success_url = reverse_lazy('accounts:password_reset_complete')  # URL to redirect to on successful password reset confirmation
    form_class = SetPasswordCaptchaForm  

class CustomPasswordResetCompleteView(RedirectIfAuthenticatedMixin, PasswordResetCompleteView):
    """
    Custom view for displaying the password reset complete page.
    Inherits from RedirectIfAuthenticatedMixin to redirect authenticated users.
    """
    template_name = 'accounts/password_reset_complete.html'  #