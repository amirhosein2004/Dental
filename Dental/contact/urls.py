from utils.common_imports import path
from .views import (
    ContactView, ContactMessagesView, MarkAsReadView, MarkAllAsReadView, 
    DetailWorkingHoursView, AddWorkingHoursView, UpdateWorkingHoursView, DeleteWorkingHoursView
)

app_name = 'contact'

# URL patterns for the contact app
urlpatterns = [
    # Contact form related paths
    path('', ContactView.as_view(), name='contact'),  # Path for the contact form view

    # Message related paths
    path('messages/', ContactMessagesView.as_view(), name='messages'),  # Path for viewing contact messages
    path('messages/read/<int:pk>/', MarkAsReadView.as_view(), name='mark_as_read'),  # Path for marking a message as read
    path('messages/mark-all-read/', MarkAllAsReadView.as_view(), name='mark_all_read'),  # Path for marking all messages as read

    # Working hours related paths
    path('workinghours/detail/<int:pk>/', DetailWorkingHoursView.as_view(), name='detail_workinghours'),  # Path for viewing details of working hours
    path('workinghours/add/', AddWorkingHoursView.as_view(), name='add_workinghours'),  # Path for adding new working hours
    path('workinghours/update/<int:pk>/', UpdateWorkingHoursView.as_view(), name='update_workinghours'),  # Path for updating existing working hours
    path('workinghours/delete/<int:pk>/', DeleteWorkingHoursView.as_view(), name='delete_workinghours'),  # Path for deleting working hours
]
