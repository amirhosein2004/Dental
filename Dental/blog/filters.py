import django_filters
from django import forms
from django_filters import CharFilter, DateFilter, ModelMultipleChoiceFilter
from .models import BlogPost, Category

class BlogPostFilter(django_filters.FilterSet):
    writer = CharFilter(field_name='writer__username', lookup_expr='icontains', label='نویسنده')

    category = ModelMultipleChoiceFilter(
        queryset=Category.objects.all(),
        field_name='categories',
        label='دسته‌بندی',
        method='filter_by_categories',
        widget=forms.CheckboxSelectMultiple
    )

    text = CharFilter(field_name='content', lookup_expr='icontains', label='متن')

    class Meta:
        model = BlogPost
        fields = ['writer', 'category', 'text']

    def filter_by_categories(self, queryset, name, value):
        if value:
            return queryset.filter(categories__in=value).distinct()
        return queryset

    def filter_queryset(self, queryset):
        queryset = queryset.select_related('writer').prefetch_related('categories')
        return super().filter_queryset(queryset)

    