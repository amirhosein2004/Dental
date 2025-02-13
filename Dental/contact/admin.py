from django.contrib import admin
from .models import WorkingHours, ContactMessage
from django.forms import TimeInput
from django.db import models


class WorkingHoursAdmin(admin.ModelAdmin):
    formfield_overrides = {
        # اعمال ویجت سفارشی برای تمامی فیلدهای TimeField
        models.TimeField: {'widget': TimeInput(format='%H:%M')},
    }

admin.site.register(WorkingHours, WorkingHoursAdmin)
admin.site.register(ContactMessage)