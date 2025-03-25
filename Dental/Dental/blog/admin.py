# Project-specific imports from common_imports
from utils.common_imports import admin  

# Imports from local models
from .models import BlogPost  

admin.site.register(BlogPost)