from django.db import models

class WorkingHoursManager(models.Manager):
    def get_queryset(self):
        # ترتیب بر اساس روز هفته (از شنبه به جمعه)
        return super().get_queryset().order_by('day')