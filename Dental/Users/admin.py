from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser

class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'image')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_doctor')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'image', 'is_staff', 'is_superuser', 'is_doctor'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_doctor')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    list_filter = ('is_staff', 'is_superuser', 'is_doctor')

admin.site.register(CustomUser, UserAdmin)
