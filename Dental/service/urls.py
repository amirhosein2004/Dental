from utils.common_imports import path
from .views import ServiceView, ServiceDetailView, AddServiceView, UpdateServiceView, RemoveServiceView

app_name = 'service'
urlpatterns = [
    path('', ServiceView.as_view(), name='service_list'),

    path('detail/<slug:slug>/', ServiceDetailView.as_view(), name='service_detail'),

    path('add/', AddServiceView.as_view(), name='add_service'),

    path('update/<int:pk>/', UpdateServiceView.as_view(), name='update_service'),

    path('remove/<int:pk>/', RemoveServiceView.as_view(), name='remove_service'),
]                     