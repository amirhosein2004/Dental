from utils.common_imports import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser

class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'image')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_doctor', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2',
                       'image', 'is_staff', 'is_superuser', 'is_doctor', 'is_active'
        ),}),
    )
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff',
        'is_superuser', 'is_doctor', 'is_active', 'date_joined', 'last_login'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_filter = ('is_staff', 'is_superuser', 'is_doctor', 'is_active')

admin.site.register(CustomUser, UserAdmin)