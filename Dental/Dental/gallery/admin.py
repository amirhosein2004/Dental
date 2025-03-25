from utils.common_imports import admin
from .models import Gallery, Image

# Register the Gallery model with the admin site
admin.site.register(Gallery)

# Register the Image model with the admin site
admin.site.register(Image)
