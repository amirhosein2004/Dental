from utils.common_imports import admin
from .models import PricingItem

# Register the PricingItem model with the admin site
admin.site.register(PricingItem)
