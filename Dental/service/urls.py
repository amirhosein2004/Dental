from django.urls import path
from .views import ServiceView, ServiceDetailView, AddServiceView, UpdateServiceView, RemoveServiceView

app_name = 'service'
urlpatterns = [
    path('', ServiceView.as_view(), name='service'),
    path('service_detail/<int:pk>/', ServiceDetailView.as_view(), name='service_detail'),
    path('add_service', AddServiceView.as_view(), name='add_service'),
    path('update_service/<int:pk>/', UpdateServiceView.as_view(), name='update_service'),
    path('remove_service/<int:pk>/', RemoveServiceView.as_view(), name='remove_service'),
]