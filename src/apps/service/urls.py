from django.urls import path

from .views.service_view import (
    AddServiceView,
    RemoveServiceView,
    ServiceDetailView,
    ServiceFAQHubView,
    ServiceView,
    UpdateServiceView,
)

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

    # Staff overview of which treatments carry questions and which do not.
    # The questions themselves are edited on the treatment's own form.
    path('faq/', ServiceFAQHubView.as_view(), name='faq_hub'),

    # One treatment per page. Declared last so the literal staff routes above
    # are matched first — otherwise `/service/add/` would resolve here as a
    # service whose slug happens to be "add".
    #
    # `str` rather than `slug`: slugs are Persian, and the built-in `slug`
    # converter only matches [-a-zA-Z0-9_]+.
    path('<str:slug>/', ServiceDetailView.as_view(), name='service_detail'),
]
