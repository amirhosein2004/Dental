from django.contrib import admin

from .models import Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    """
    The CV behind each public profile page.

    Grouped by what the page renders rather than by field type, because the
    person filling this in is usually looking at the page they want to change.
    """
    list_display = ('__str__', 'slug', 'specialty', 'is_published', 'order')
    list_editable = ('is_published', 'order')
    list_filter = ('is_published', 'branches')
    search_fields = (
        'user__first_name', 'user__last_name', 'specialty', 'license_number',
    )
    filter_horizontal = ('services', 'branches')
    fieldsets = (
        (None, {'fields': ('user', 'slug', 'is_published', 'order')}),
        ('معرفی', {'fields': ('headline', 'description')}),
        ('اعتبار حرفه‌ای', {
            'fields': ('specialty', 'degree', 'license_number', 'experience_years'),
            'description': (
                'شماره نظام پزشکی و مدرک، در داده ساختاریافته‌ی صفحه هم منتشر '
                'می‌شود و قوی‌ترین سیگنال اعتماد یک صفحه‌ی پزشکی است.'
            ),
        }),
        ('رزومه', {
            'fields': ('education', 'experience', 'certifications', 'memberships'),
            'description': 'هر مورد را در یک خط جداگانه بنویسید.',
        }),
        ('ارتباط با بقیه سایت', {'fields': ('services', 'branches')}),
        ('شبکه‌های اجتماعی', {
            'fields': ('instagram', 'telegram', 'twitter', 'linkedin'),
            'classes': ('collapse',),
        }),
        ('سئو', {
            'fields': ('meta_description',),
            'description': 'خالی بگذارید تا از عنوان کوتاه و تخصص ساخته شود.',
            'classes': ('collapse',),
        }),
    )
