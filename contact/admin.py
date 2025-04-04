from utils.common_imports import admin  
from .models import ContactMessage  


# Register the ContactMessage model with the default admin interface
admin.site.register(ContactMessage)