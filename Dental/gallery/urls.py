from utils.common_imports import path
from .views import GalleryView, AddGalleryView, UpdateGalleryView, DeleteGalleryView

# Define the application namespace
app_name = 'gallery'

# URL patterns for the gallery app
urlpatterns = [
    # URL pattern for the gallery list view
    path('', GalleryView.as_view(), name='gallery_list'),
    
    # URL pattern for adding a new gallery
    path('add/', AddGalleryView.as_view(), name='add_gallery'),
    
    # URL pattern for updating an existing gallery
    path('update/<int:pk>/', UpdateGalleryView.as_view(), name='update_gallery'),
    
    # URL pattern for deleting an existing gallery
    path('delete/<int:pk>/', DeleteGalleryView.as_view(), name='delete_gallery'),
]
