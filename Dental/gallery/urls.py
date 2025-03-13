from utils.common_imports import path
from .views import GalleryView, AddGalleryView, UpdateGalleryView, DeleteGalleryView

app_name = 'gallery'
urlpatterns = [
    path('', GalleryView.as_view(), name='gallery_list'),
    path('add/', AddGalleryView.as_view(), name='add_gallery'),
    path('update/<int:pk>/', UpdateGalleryView.as_view(), name='update_gallery'),
    path('delete/<int:pk>/', DeleteGalleryView.as_view(), name='delete_gallery'),
]
