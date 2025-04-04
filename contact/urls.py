from utils.common_imports import path
from .views import ContactView, ContactMessagesView, MarkAsReadView, MarkAllAsReadView

app_name = 'contact'

# URL patterns for the contact app
urlpatterns = [
    # Contact form related paths
    path('', ContactView.as_view(), name='contact'),  # Path for the contact form view

    # Message related paths
    path('messages/', ContactMessagesView.as_view(), name='messages'),  # Path for viewing contact messages
    path('messages/read/<int:pk>/', MarkAsReadView.as_view(), name='mark_as_read'),  # Path for marking a message as read
    path('messages/mark-all-read/', MarkAllAsReadView.as_view(), name='mark_all_read'),  # Path for marking all messages as read
]
