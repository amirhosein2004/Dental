# Project-specific imports from common_imports
from utils.common_imports import admin, models  

# Imports from local models
from .models import WorkingHours, ContactMessage  

# Third-party imports (Django forms)
from django.forms import TimeInput  


class WorkingHoursAdmin(admin.ModelAdmin):
    formfield_overrides = {
        # اعمال ویجت سفارشی برای تمامی فیلدهای TimeField
        models.TimeField: {'widget': TimeInput(format='%H:%M')},
    }

admin.site.register(WorkingHours, WorkingHoursAdmin)
admin.site.register(ContactMessage)