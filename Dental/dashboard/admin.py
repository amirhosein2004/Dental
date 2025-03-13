from utils.common_imports import admin
from .models import Doctor

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'created_at', 'updated_at')  # فیلدهای نمایش در لیست
    list_select_related = ('user',)  # بهینه‌سازی برای لود user