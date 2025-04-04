from utils.common_imports import path
from .views import ServiceView, AddServiceView, UpdateServiceView, RemoveServiceView

app_name = 'service'

# URL patterns for the service app
urlpatterns = [
    # URL pattern for the service list view
    path('', ServiceView.as_view(), name='service_list'),

    # URL pattern for adding a new service
    path('add/', AddServiceView.as_view(), name='add_service'),

    # URL pattern for updating an existing service
    path('update/<int:pk>/', UpdateServiceView.as_view(), name='update_service'),

    # URL pattern for removing an existing service
    path('remove/<int:pk>/', RemoveServiceView.as_view(), name='remove_service'),
]


