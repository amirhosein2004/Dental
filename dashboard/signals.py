# Imports from Django
from django.db.models.signals import post_save  
from django.dispatch import receiver  

# Imports from local models
from users.models import CustomUser  
from .models import Doctor  

@receiver(post_save, sender=CustomUser)
def create_doctor_profile(sender, instance, created, **kwargs):
    """
    Signal receiver that creates or deletes a Doctor profile based on the CustomUser instance.

    Args:
        sender (class): The model class that sent the signal.
        instance (CustomUser): The instance of the sender model.
        created (bool): A boolean indicating whether a new record was created.
        **kwargs: Additional keyword arguments.
    """
    if instance.is_doctor:
        # If the user is marked as a doctor and does not have a Doctor profile, create one.
        if not hasattr(instance, 'doctor'):
            Doctor.objects.create(user=instance)
    else:
        # If the user is not marked as a doctor and has a Doctor profile, delete it.
        if hasattr(instance, 'doctor'):
            instance.doctor.delete()