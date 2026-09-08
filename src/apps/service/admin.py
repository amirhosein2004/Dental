from django.contrib import admin

from .models import Service, ServiceFAQ


class ServiceFAQInline(admin.TabularInline):
    """
    FAQs are edited on the service they belong to. They are never useful on
    their own — a question without its treatment has nowhere to render.
    """
    model = ServiceFAQ
    extra = 1
    fields = ('question', 'answer', 'order')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'order', 'updated_at')
    list_editable = ('order',)
    search_fields = ('title', 'description')
    # Left blank on purpose in the form: `Service.save` generates it from the
    # title. Shown here so an existing slug can be corrected, since changing
    # one breaks the URL that Google already has.
    prepopulated_fields = {}
    inlines = [ServiceFAQInline]
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'description', 'content', 'image', 'order')}),
        ('سئو', {
            'fields': ('meta_title', 'meta_description'),
            'description': 'خالی بگذارید تا از عنوان و توضیح کوتاه ساخته شود.',
            'classes': ('collapse',),
        }),
    )


@admin.register(ServiceFAQ)
class ServiceFAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'service', 'order')
    list_filter = ('service',)
    search_fields = ('question', 'answer')
