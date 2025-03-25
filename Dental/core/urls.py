from utils.common_imports import path
from .views.clinic_view import ClinicView, AddClinicView, UpdateClinicView, DeleteClinicView
from .views.category_view import CategoryView, AddCategoryView, UpdateCategoryView, RemoveCategoryView
from .views.workinghours_view import WorkingHoursView, AddWorkingHoursView, UpdateWorkingHoursView, DeleteWorkingHoursView
from .views.manage_view import ManageView

app_name = 'core'

# URL patterns related to clinics
clinic_patterns = [
    path('clinic/', ClinicView.as_view(), name='clinic'),
    path('clinic/add/', AddClinicView.as_view(), name='add_clinic'),
    path('clinic/update/<int:pk>/', UpdateClinicView.as_view(), name='update_clinic'),
    path('clinic/delete/<int:pk>/', DeleteClinicView.as_view(), name='delete_clinic'),
]

# URL patterns related to categories
category_patterns = [
    path('category/', CategoryView.as_view(), name='category'),
    path('category/add/', AddCategoryView.as_view(), name='add_category'),
    path('category/update/<int:pk>/', UpdateCategoryView.as_view(), name='update_category'),
    path('category/remove/<int:pk>/', RemoveCategoryView.as_view(), name='remove_category'),
]

workinghours_patterns = [
    # Working hours related paths
    path('workinghours/', WorkingHoursView.as_view(), name='workinghours'),  # Path for viewing list of working hours
    path('workinghours/add/', AddWorkingHoursView.as_view(), name='add_workinghours'),  # Path for adding new working hours
    path('workinghours/update/<int:pk>/', UpdateWorkingHoursView.as_view(), name='update_workinghours'),  # Path for updating existing working hours
    path('workinghours/delete/<int:pk>/', DeleteWorkingHoursView.as_view(), name='delete_workinghours'),  # Path for deleting working hours
]

# Main URL patterns
urlpatterns = [
    path('manage/', ManageView.as_view(), name='manage'),
] + clinic_patterns + category_patterns + workinghours_patterns