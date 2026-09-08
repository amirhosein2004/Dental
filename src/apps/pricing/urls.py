from django.urls import path

from .views.manage_view import (
    AddPricingCategoryView,
    AddPricingItemView,
    DeletePricingCategoryView,
    DeletePricingItemView,
    PricingCategoryListView,
    UpdatePricingCategoryView,
    UpdatePricingItemView,
)
from .views.pricing_view import PricingListView

app_name = 'pricing'

urlpatterns = [
    # Public pricing list
    path('', PricingListView.as_view(), name='pricing_list'),

    # Item CRUD
    path('add/', AddPricingItemView.as_view(), name='add_pricing_item'),
    path('update/<int:pk>/', UpdatePricingItemView.as_view(), name='update_pricing_item'),
    path('delete/<int:pk>/', DeletePricingItemView.as_view(), name='delete_pricing_item'),

    # Category CRUD (staff-only)
    path('categories/', PricingCategoryListView.as_view(), name='pricing_category_list'),
    path('categories/add/', AddPricingCategoryView.as_view(), name='add_pricing_category'),
    path('categories/update/<int:pk>/', UpdatePricingCategoryView.as_view(), name='update_pricing_category'),
    path('categories/delete/<int:pk>/', DeletePricingCategoryView.as_view(), name='delete_pricing_category'),
]
