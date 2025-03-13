# Imports from Django
from django.db.models.signals import post_save  
from django.dispatch import receiver  

# Imports from local models
from users.models import CustomUser  
from .models import Doctor  

@receiver(post_save, sender=CustomUser)
def create_doctor_profile(sender, instance, created, **kwargs):
    if instance.is_doctor:
        # اگر is_doctor تیک خورده و پروفایل Doctor وجود ندارد، بساز
        if not hasattr(instance, 'doctor'):
            Doctor.objects.create(user=instance)
    else:
        # اگر is_doctor تیک ندارد و پروفایل Doctor وجود دارد، حذف کن
        if hasattr(instance, 'doctor'):
            instance.doctor.delete()