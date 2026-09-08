from django.urls import path

from .views.push_view import SubscribeView, UnsubscribeView
from .views.sms_view import (
    BulkSmsView,
    ContactGroupDeleteView,
    ContactGroupEditView,
    ContactGroupListView,
    NotificationLogView,
)

app_name = 'notifications'

urlpatterns = [
    path('bulk-sms/', BulkSmsView.as_view(), name='bulk_sms'),
    path('logs/', NotificationLogView.as_view(), name='logs'),

    # Reusable recipient lists
    path('groups/', ContactGroupListView.as_view(), name='groups'),
    path('groups/<int:pk>/edit/', ContactGroupEditView.as_view(), name='group_edit'),
    path('groups/<int:pk>/delete/', ContactGroupDeleteView.as_view(), name='group_delete'),

    # Browser push: a staff device registers itself here, and forgets itself
    # again when notifications are switched off.
    path('push/subscribe/', SubscribeView.as_view(), name='push_subscribe'),
    path('push/unsubscribe/', UnsubscribeView.as_view(), name='push_unsubscribe'),
]
