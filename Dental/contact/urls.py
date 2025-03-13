from utils.common_imports import path
from .views import ContactView,ContactMessagesView,MarkAsReadView,MarkAllAsReadView, DetailWorkingHoursView, AddWorkingHoursView, UpdateWorkingHoursView, DeleteWorkingHoursView


app_name = 'contact'
urlpatterns = [
    # Contact form related paths
    path('', ContactView.as_view(), name='contact'),

   # Message related paths
    path('messages/', ContactMessagesView.as_view(), name='messages'),
    path('messages/read/<int:pk>/', MarkAsReadView.as_view(), name='mark_as_read'),
    path('messages/mark-all-read/', MarkAllAsReadView.as_view(), name='mark_all_read'),

    # Working hours related paths
    path('workinghours/detail/<int:pk>/', DetailWorkingHoursView.as_view(), name='detail_workinghours'),
    path('workinghours/add/', AddWorkingHoursView.as_view(), name='add_workinghours'),
    path('workinghours/update/<int:pk>/', UpdateWorkingHoursView.as_view(), name='update_workinghours'),
    path('workinghours/delete/<int:pk>/', DeleteWorkingHoursView.as_view(), name='delete_workinghours'),
]
