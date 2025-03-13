from utils.common_imports import path
from .views import HomeView

app_name = 'home'
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
]