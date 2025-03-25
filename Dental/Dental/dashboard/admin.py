from utils.common_imports import admin
from .models import Doctor

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    """
    Admin interface options for the Doctor model.
    """
    # Fields to display in the list view
    list_display = ('__str__', 'created_at', 'updated_at')
    
    # Optimize loading of related user objects
    list_select_related = ('user',)