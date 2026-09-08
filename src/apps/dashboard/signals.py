from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.users.models import CustomUser
from .context_processors import invalidate_clinic_doctors_cache
from .models import Doctor


@receiver(post_save, sender=CustomUser)
def create_doctor_profile(sender, instance, created, **kwargs):
    """
    Create a Doctor profile the first time a user is flagged as a doctor.

    Deletion is intentionally NOT handled here: unsetting `is_doctor` no longer
    cascades a Doctor delete, so related content (blog posts, galleries) is not
    orphaned. Removing a Doctor must be done explicitly through the admin.
    """
    if instance.is_doctor and not Doctor.objects.filter(user=instance).exists():
        Doctor.objects.create(user=instance)


@receiver([post_save, post_delete], sender=Doctor)
def _bust_clinic_doctors_cache_on_doctor_change(sender, instance, **kwargs):
    invalidate_clinic_doctors_cache()


@receiver([post_save, post_delete], sender=CustomUser)
def _bust_clinic_doctors_cache_on_user_change(sender, instance, **kwargs):
    # `is_active` and profile fields live on the user; keep the footer roster fresh.
    if instance.is_doctor:
        invalidate_clinic_doctors_cache()
