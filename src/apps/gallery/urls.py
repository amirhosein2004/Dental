from django.urls import path

from .views.manage_view import (
    AddGalleryImagesView,
    AddGalleryView,
    ClearGalleryImagesView,
    DeleteGalleryImageView,
    DeleteGalleryView,
    UpdateGalleryCategoryView,
    UpdateGalleryView,
)
from .views.public_view import GalleryView, LoadMoreGalleriesView

app_name = 'gallery'

urlpatterns = [
    path('', GalleryView.as_view(), name='gallery_list'),
    path('load-more-gallery/', LoadMoreGalleriesView.as_view(), name='load_more_galleries'),

    path('add/', AddGalleryView.as_view(), name='add_gallery'),

    path('update/<int:pk>/', UpdateGalleryView.as_view(), name='update_gallery'),
    path('update/<int:pk>/category/', UpdateGalleryCategoryView.as_view(), name='update_gallery_category'),
    path('update/<int:pk>/images/add/', AddGalleryImagesView.as_view(), name='add_gallery_images'),
    path('update/<int:pk>/images/<int:image_id>/delete/', DeleteGalleryImageView.as_view(), name='delete_gallery_image'),
    path('update/<int:pk>/images/clear/', ClearGalleryImagesView.as_view(), name='clear_gallery_images'),

    path('delete/<int:pk>/', DeleteGalleryView.as_view(), name='delete_gallery'),
]
