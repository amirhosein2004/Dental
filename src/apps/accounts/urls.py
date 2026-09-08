from django.urls import path

from .views.auth_view import (
    DoctorLoginView, DoctorLogoutView, VerifyOTPView, ResendOTPView, ChangePasswordView,
)
from apps.accounts.views.password_reset_view import (
    CustomPasswordResetView, CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView, CustomPasswordResetCompleteView,
)

app_name = 'accounts'

urlpatterns = [
    path('login/', DoctorLoginView.as_view(), name='doctor_login'),  # Route for doctor login
    path('logout/', DoctorLogoutView.as_view(), name='doctor_logout'),  # Route for doctor logout
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),  # Route for OTP verification
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),  # Route for resending OTP
    path('change-password/<int:user_id>/', ChangePasswordView.as_view(), name='change_password'),  # Route for changing password

    # Password reset. Ordinary, readable URLs: the reset itself is protected by
    # a single-use signed token, the login throttle, and the form's captcha —
    # not by the address being hard to guess. These used to carry a random
    # prefix and suffix from the environment, which meant the same link had a
    # different shape in every environment and a stale env file could break
    # the emails.
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
