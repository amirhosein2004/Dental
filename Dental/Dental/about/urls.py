from utils.common_imports import path  # Importing path for defining URL patterns
from .views import AboutView  

app_name = 'about'  

urlpatterns = [
    path('', AboutView.as_view(), name='about'),  
]
