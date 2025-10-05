from django.urls import path
from . import views

app_name = 'pricing'

urlpatterns = [
    # Public pricing list view
    path('', views.PricingListView.as_view(), name='pricing_list'),
    path('add/', views.AddPricingItemView.as_view(), name='add_pricing_item'),
    path('update/<int:pk>/', views.UpdatePricingItemView.as_view(), name='update_pricing_item'),
    path('delete/<int:pk>/', views.DeletePricingItemView.as_view(), name='delete_pricing_item'),
]
