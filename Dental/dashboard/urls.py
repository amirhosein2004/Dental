from utils.common_imports import path
from .views import DashboardView, DashboardListView

app_name = 'dashboard'
urlpatterns = [
    # Doctor-specific dashboard
    path('<int:doctor_id>/', DashboardView.as_view(), name='dashboard_doctor'),
    
    # List of dashboards of doctors
    path('list/', DashboardListView.as_view(), name='dashboard_list'),
]
