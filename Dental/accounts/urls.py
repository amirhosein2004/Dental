# Project-specific imports from common_imports
from utils.common_imports import path, settings

# Imports from local views and forms
from .views.auth_view import DoctorLoginView, DoctorLogoutView, VerifyOTPView, ResendOTPView, ChangePasswordView
from accounts.views.password_reset_view import (
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView
)


app_name = 'accounts'
urlpatterns = [
    path('login/SB/fuckyoudoc', DoctorLoginView.as_view(), name='doctor_login'),
    path('logout/', DoctorLogoutView.as_view(), name='doctor_logout'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('change-password/<int:user_id>/', ChangePasswordView.as_view(), name='change_password'),

    path(f'{settings.RESET_PREFIX}/', CustomPasswordResetView.as_view(), name='password_reset'),
    path(f'{settings.RESET_PREFIX}/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path(f'{settings.RESET_PREFIX}/confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path(f'{settings.RESET_PREFIX}/complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]