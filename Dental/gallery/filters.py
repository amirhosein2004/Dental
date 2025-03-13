# Third-party imports
import django_filters  

# Imports from local models
from .models import Gallery  
from core.models import Category  

class GalleryFilter(django_filters.FilterSet):
    """
    Filter class for Gallery model to filter by category.
    """
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        label="دسته‌بندی",  # Label for the filter field 
        empty_label="همه دسته‌بندی‌ها"  # Empty label option 
    )

    class Meta:
        model = Gallery  # The model to filter
        fields = ['category']  # Fields to filter by
