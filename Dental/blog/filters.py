# Project-specific imports from common_imports
from utils.common_imports import forms  

# Imports from local models
from .models import BlogPost, Category  

# Third-party imports
import django_filters  
from django.db.models import Q


class BlogPostFilter(django_filters.FilterSet):
    writer = django_filters.CharFilter(method='filter_by_writer_name', label='نویسنده')

    category = django_filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.all(),
        field_name='categories',
        label='دسته‌بندی',
        method='filter_by_categories',
        widget=forms.CheckboxSelectMultiple
    )

    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains', label='عنوان')

    class Meta:
        model = BlogPost
        fields = ['writer', 'category', 'title']

    def filter_by_writer_name(self, queryset, name, value):
        """فیلتر کردن بر اساس نام و فامیل نویسنده"""
        if value:
            return queryset.filter(
                Q(writer__user__first_name__icontains=value) |
                Q(writer__user__last_name__icontains=value)
            ).distinct()
        return queryset

    def filter_by_categories(self, queryset, name, value):
        if value:
            return queryset.filter(categories__in=value).distinct()
        return queryset

    def filter_queryset(self, queryset):
        queryset = queryset.select_related('writer').prefetch_related('categories')
        return super().filter_queryset(queryset)