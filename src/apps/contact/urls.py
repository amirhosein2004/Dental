from django.urls import path

from .views.contact_view import ContactView
from .views.messages_view import (
    CleanupOldMessagesView,
    ContactMessagesView,
    MarkAllAsReadView,
    MarkAsReadView,
)

app_name = 'contact'

urlpatterns = [
    path('', ContactView.as_view(), name='contact'),
    path('messages/', ContactMessagesView.as_view(), name='messages'),
    path('messages/read/<int:pk>/', MarkAsReadView.as_view(), name='mark_as_read'),
    path('messages/mark-all-read/', MarkAllAsReadView.as_view(), name='mark_all_read'),
    path('messages/cleanup/', CleanupOldMessagesView.as_view(), name='cleanup_old'),
]
