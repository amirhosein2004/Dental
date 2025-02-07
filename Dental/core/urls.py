from django.urls import path
from .views import CategoryView, AddCategoryView, RemoveCategoryView

app_name = 'core'
urlpatterns = [
    path('', CategoryView.as_view(), name='category'),
    path('add_category', AddCategoryView.as_view(), name='add_category'),
    path('remove_category/<int:pk>', RemoveCategoryView.as_view(), name='remove_category'),
]