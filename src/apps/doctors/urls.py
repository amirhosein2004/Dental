from django.urls import path

from .views import DoctorDetailView, DoctorListView

app_name = 'doctors'

urlpatterns = [
    # The hub. Links to every CV page and carries the "our doctors" query.
    path('', DoctorListView.as_view(), name='doctor_list'),

    # `str` rather than `slug`: slugs here are Persian, and the built-in
    # `slug` converter only matches [-a-zA-Z0-9_]+.
    path('<str:slug>/', DoctorDetailView.as_view(), name='doctor_detail'),
]
