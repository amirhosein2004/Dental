from django.contrib import admin

from .models import About, Branch


@admin.register(About)
class AboutAdmin(admin.ModelAdmin):
    """
    Singleton admin — hide "add" once the row exists, and forbid delete so
    consumers (footer, about page, contact page) always have data to render.
    """
    list_display = ('name', 'email', 'updated_at')

    def has_add_permission(self, request):
        return not About.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    """
    The practices. Every field that differs between locations lives here,
    opening hours included — there is no site-wide hours row to fall back to.
    """
    list_display = ('city', 'phone', 'order', 'updated_at')
    list_editable = ('order',)
    fieldsets = (
        (None, {'fields': ('city', 'title', 'order')}),
        ('تماس و نشانی', {
            'fields': ('address', 'postal_code', 'phone', 'extra_phones', 'hours'),
        }),
        ('نقشه', {
            'fields': ('map_embed_url', 'map_link', 'latitude', 'longitude'),
            'description': (
                'مختصات هم روی نقشه‌ی صفحه‌ی تماس و هم در داده ساختاریافته '
                'استفاده می‌شود؛ بدون آن، مکان این مطب روی نقشه نمایش داده نمی‌شود.'
            ),
        }),
    )
