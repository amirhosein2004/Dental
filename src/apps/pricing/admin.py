from django.contrib import admin

from .models import PricingCategory, PricingItem


@admin.register(PricingCategory)
class PricingCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'created_at')
    list_editable = ('order',)
    ordering = ('order', 'name')
    search_fields = ('name',)


@admin.register(PricingItem)
class PricingItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'updated_at')
    list_filter = ('category',)
    list_select_related = ('category',)
    search_fields = ('title',)
    autocomplete_fields = ('category',)
