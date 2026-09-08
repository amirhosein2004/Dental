from django.urls import path

from .views.home_view import HomeView

app_name = 'home'
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
]