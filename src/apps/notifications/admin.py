from django.contrib import admin

from .models import ContactGroup, NotificationLog


@admin.register(ContactGroup)
class ContactGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'member_count', 'created_by', 'updated_at')
    search_fields = ('name', 'description', 'numbers')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'kind', 'status', 'sent_count', 'recipient_count')
    list_filter = ('kind', 'status')
    search_fields = ('recipients', 'message')
    # A delivery log that can be edited is not a log.
    readonly_fields = tuple(f.name for f in NotificationLog._meta.fields)

    def has_add_permission(self, request):
        return False
