from utils.common_imports import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser

class UserAdmin(BaseUserAdmin):
    """
    Custom admin class for managing CustomUser model in the Django admin interface.
    Inherits from Django's built-in UserAdmin.
    """
    
    # Define the fields to be used in displaying the User model.
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'image')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_doctor', 'is_active')}),
    )
    
    # Define the fields to be used when adding a new user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2',
                       'image', 'is_staff', 'is_superuser', 'is_doctor', 'is_active'
            ),
        }),
    )
    
    # Fields to be displayed in the list view of the admin interface.
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff',
        'is_superuser', 'is_doctor', 'is_active', 'date_joined', 'last_login'
    )
    
    # Fields that can be searched in the admin interface.
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    # Default ordering for the list view.
    ordering = ('-date_joined',)
    
    # Filters to be displayed in the admin interface.
    list_filter = ('is_staff', 'is_superuser', 'is_doctor', 'is_active')

# Register the CustomUser model with the custom UserAdmin.
admin.site.register(CustomUser, UserAdmin)