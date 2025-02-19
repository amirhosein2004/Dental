from django.urls import path
from .views import DasboardView, EditProfileDashboardView, DashboardListView

app_name = 'dashboard'
urlpatterns = [
    path('<int:doctor_id>/', DasboardView.as_view(), name='dashboard_doctor'),
    path('edit_profile/<int:doctor_id>/', EditProfileDashboardView.as_view(), name='edit_profile'),
    path('dashboard_list', DashboardListView.as_view(), name='dashboard_list')
]