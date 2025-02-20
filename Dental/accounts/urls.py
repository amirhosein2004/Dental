from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import DoctorLoginView, DoctorLogoutView, VerifyOTPView
from .forms import PasswordResetCaptchaForm, SetPasswordCaptchaForm

app_name = 'accounts'
urlpatterns = [
    path('login/', DoctorLoginView.as_view(), name='doctor_login'),
    path('logout/', DoctorLogoutView.as_view(), name='doctor_logout'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    
    # reset password
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             success_url=reverse_lazy('accounts:password_reset_done'),
             form_class=PasswordResetCaptchaForm
         ), 
         name='password_reset'),
    
    path('password_reset_done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url=reverse_lazy('accounts:password_reset_complete'),
             form_class=SetPasswordCaptchaForm

         ), 
         name='password_reset_confirm'),
    
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]