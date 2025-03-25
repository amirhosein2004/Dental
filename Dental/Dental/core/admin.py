from utils.common_imports import admin
from .models import Category, Clinic

# Register the Category model with the admin site
admin.site.register(Category)

# Register the Clinic model with the admin site
admin.site.register(Clinic)