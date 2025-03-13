from utils.common_imports import path
from .views.clinic_view import DetailClinicView, AddClinicView, UpdateClinicView, DeleteClinicView
from .views.category_view import CategoryView, AddCategoryView,UpdateCategoryView, RemoveCategoryView
from .views.manage_view import ManageView

app_name = 'core'

# URLهای مربوط به کلینیک‌ها
clinic_patterns = [
    path('clinic/detail/<int:pk>/', DetailClinicView.as_view(), name='detail_clinic'),
    path('clinic/add/', AddClinicView.as_view(), name='add_clinic'),
    path('clinic/update/<int:pk>/', UpdateClinicView.as_view(), name='update_clinic'),
    path('clinic/delete/<int:pk>/', DeleteClinicView.as_view(), name='delete_clinic'),
]

# URL های مربوط به دسته بندی ها
category_patterns = [
    path('category/', CategoryView.as_view(), name='category'),  
    path('category/add/', AddCategoryView.as_view(), name='add_category'), 
    path('category/update/<int:pk>/', UpdateCategoryView.as_view(), name='update_category'),
    path('category/remove/<int:pk>/', RemoveCategoryView.as_view(), name='remove_category'), 
]

urlpatterns = [
    path('manage/', ManageView.as_view(), name='manage'),  
] + clinic_patterns + category_patterns