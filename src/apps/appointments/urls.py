from django.urls import path

from .views.booking_view import AppointmentBoardView, BookAppointmentView
from .views.manage_view import (
    AppointmentCancelView,
    AppointmentListView,
    SlotDeleteView,
    SlotManageView,
)

app_name = 'appointments'

urlpatterns = [
    # Public
    path('', AppointmentBoardView.as_view(), name='board'),
    path('book/<int:pk>/', BookAppointmentView.as_view(), name='book'),

    # Staff
    path('manage/', SlotManageView.as_view(), name='manage'),
    path('manage/delete/<int:pk>/', SlotDeleteView.as_view(), name='delete_slot'),
    path('list/', AppointmentListView.as_view(), name='list'),
    path('cancel/<int:pk>/', AppointmentCancelView.as_view(), name='cancel'),
]
