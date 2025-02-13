from django.urls import path
from .views.about_views import AboutView, EditAboutView
from .views.clinic_views import DetailClinicView, AddClinicView, UpdateClinicView, DeleteClinicView
from .views.service_views import DetailServiceView, AddServiceView, UpdateServiceView, DeleteServiceView
from .views.doctor_views import DetailDoctorView, AddDoctorView


app_name = 'about'

# URLهای مربوط به کلینیک‌ها
clinic_patterns = [
    path('clinic/detail/<int:pk>/', DetailClinicView.as_view(), name='detail_clinic'),
    path('clinic/add/', AddClinicView.as_view(), name='add_clinic'),
    path('clinic/update/<int:pk>/', UpdateClinicView.as_view(), name='update_clinic'),
    path('clinic/delete/<int:pk>/', DeleteClinicView.as_view(), name='delete_clinic'),
]

# URLهای مربوط به خدمات
service_patterns = [
    path('service/detail/<int:pk>/', DetailServiceView.as_view(), name='detail_service'),
    path('service/add/', AddServiceView.as_view(), name='add_service'),
    path('service/update/<int:pk>/', UpdateServiceView.as_view(), name='update_service'),
    path('service/delete/<int:pk>/', DeleteServiceView.as_view(), name='delete_service'),
]

# URLهای مربوط به پزشکان
doctor_patterns = [
    path('doctor/detail/<int:pk>/', DetailDoctorView.as_view(), name='detail_doctor'),
    path('doctor/add/', AddDoctorView.as_view(), name='add_doctor'),
]

urlpatterns = [
    path('', AboutView.as_view(), name='about'),
    path('edit/', EditAboutView.as_view(), name='edit_about'),
] + clinic_patterns + service_patterns + doctor_patterns 