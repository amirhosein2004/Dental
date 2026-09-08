import django_filters
from django import forms

from apps.core.models import Category
from apps.dashboard.models import Doctor

from .models import BlogPost


class BlogPostFilter(django_filters.FilterSet):
    """
    Filter class for BlogPost model to filter blog posts based on writer, category, and title.
    """
    # A picker, not a text box.
    #
    # It used to be a free-text field matched with `icontains` against the
    # writer's first *or* last name, so "بابایی" worked, "دکتر بابایی" matched
    # nothing, and a typo silently returned an empty page with no hint that
    # the name was the problem. The clinic has a handful of doctors and they
    # are the only people who can write a post, so the whole set fits in a
    # dropdown and every option is guaranteed to return something.
    writer = django_filters.ModelChoiceFilter(
        field_name='writer',
        queryset=Doctor.objects.select_related('user').order_by(
            'order', 'user__first_name', 'user__last_name',
        ),
        label='نویسنده',
        empty_label='همه‌ی نویسندگان',
        widget=forms.Select,
    )

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

    @property
    def selected_writer(self):
        """
        The chosen doctor, or ``None``.

        The picker's trigger has to print the current choice, and the raw
        querystring value is a primary key. A stale or hand-edited one is
        answered with ``None`` — the same "all authors" state the unfiltered
        page shows — rather than an exception on a public URL.
        """
        value = (self.data or {}).get('writer')
        if not value:
            return None
        try:
            return self.form.fields['writer'].queryset.filter(pk=value).first()
        except (ValueError, TypeError):
            return None

    def filter_by_categories(self, queryset, name, value):
        """
        Filter the queryset by selected categories.

        Args:
            queryset: The initial queryset of BlogPost objects.
            name: The name of the filter field.
            value: The value to filter by.

        Returns:
            Filtered queryset containing BlogPost objects that belong to the selected categories.
        """
        if value:
            return queryset.filter(categories__in=value).distinct()
        return queryset