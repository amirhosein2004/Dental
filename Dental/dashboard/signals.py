from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import CustomUser
from .models import Doctor

@receiver(post_save, sender=CustomUser)
def create_doctor_profile(sender, instance, created, **kwargs):
    if created and instance.is_doctor:  # اگر کاربر جدید ساخته شده و پزشک است
        Doctor.objects.create(user=instance)