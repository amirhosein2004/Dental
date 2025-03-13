from utils.common_imports import admin, models  
from .models import WorkingHours, ContactMessage  
from django.forms import TimeInput  

class WorkingHoursAdmin(admin.ModelAdmin):
    """
    Custom admin class for the WorkingHours model.
    Overrides the default form field widget for TimeField to use a custom TimeInput widget.
    """
    formfield_overrides = {
        # Apply custom widget for all TimeField fields
        models.TimeField: {'widget': TimeInput(format='%H:%M')},
    }

# Register the WorkingHours model with the custom admin class
admin.site.register(WorkingHours, WorkingHoursAdmin)

# Register the ContactMessage model with the default admin interface
admin.site.register(ContactMessage)