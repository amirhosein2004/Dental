from utils.common_imports import admin
from .models import OTP

# Register the OTP model with the admin site
admin.site.register(OTP)