from django.contrib import admin

from .models import Appointment, AvailabilitySlot


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'get_weekday_display', 'time', 'is_active')
    list_filter = ('weekday', 'is_active', 'doctor')
    ordering = ('doctor', 'weekday', 'time')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'slot', 'week_start', 'status')
    list_filter = ('status', 'week_start')
    search_fields = ('full_name', 'phone', 'national_code')
    # Bookings are patient records, not staff-authored content: editing them
    # by hand would desync the schedule from what the patient was told.
    readonly_fields = ('created_at',)
