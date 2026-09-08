from django.urls import path

from .views.category_view import CategoryView, AddCategoryView, UpdateCategoryView, RemoveCategoryView
from .views.manage_view import ManageView

app_name = 'core'

category_patterns = [
    path('category/', CategoryView.as_view(), name='category'),
    path('category/add/', AddCategoryView.as_view(), name='add_category'),
    path('category/update/<int:pk>/', UpdateCategoryView.as_view(), name='update_category'),
    path('category/remove/<int:pk>/', RemoveCategoryView.as_view(), name='remove_category'),
]

urlpatterns = [
    path('manage/', ManageView.as_view(), name='manage'),
] + category_patterns
