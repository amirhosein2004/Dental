# Third-party imports
import django_filters  

# Imports from local models
from .models import Gallery  
from core.models import Category  

class GalleryFilter(django_filters.FilterSet):
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        label="دسته‌بندی",
        empty_label="همه دسته‌بندی‌ها"
    )

    class Meta:
        model = Gallery
        fields = ['category']
