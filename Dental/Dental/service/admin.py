from utils.common_imports import admin
from .models import Service

# Register the Service model with the admin site
admin.site.register(Service)