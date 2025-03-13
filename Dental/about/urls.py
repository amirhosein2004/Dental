from utils.common_imports import path
from .views import AboutView

# Define app namespace
app_name = 'about'

urlpatterns = [
    # About Us main page
    path('', AboutView.as_view(), name='about'),
]
