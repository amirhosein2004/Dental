from django.urls import path
from .views import ContactView,ContactMessagesView,MarkAsReadView,MarkAllAsReadView, DetailWorkingHoursView, AddWorkingHoursView, UpdateWorkingHoursView, DeleteWorkingHoursView


app_name = 'contact'
urlpatterns = [
    path('', ContactView.as_view(), name='contact'),
    path('messages/', ContactMessagesView.as_view(), name='contact_messages'),
    path('messages/read/<int:pk>/', MarkAsReadView.as_view(), name='mark_as_read'),
    path('messages/mark-all-read/', MarkAllAsReadView.as_view(), name='mark_all_read'),
    path('workinghours/detail/<int:pk>/', DetailWorkingHoursView.as_view(), name='detail_workinghours'),
    path('workinghours/add/', AddWorkingHoursView.as_view(), name='add_workinghours'),
    path('workinghours/update/<int:pk>/', UpdateWorkingHoursView.as_view(), name='update_workinghours'),
    path('workinghours/delete/<int:pk>/', DeleteWorkingHoursView.as_view(), name='delete_workinghours'),
]