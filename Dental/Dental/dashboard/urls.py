from utils.common_imports import path
from .views import DashboardView, DashboardListView

app_name = 'dashboard'

urlpatterns = [
    # Doctor-specific dashboard
    # This URL pattern maps to the DashboardView and expects an integer doctor_id as a parameter
    path('<int:doctor_id>/', DashboardView.as_view(), name='dashboard_doctor'),
    
    # List of dashboards of doctors
    # This URL pattern maps to the DashboardListView and does not require any parameters
    path('list/', DashboardListView.as_view(), name='dashboard_list'),
]
