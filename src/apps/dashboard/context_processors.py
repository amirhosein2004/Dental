from django.core.cache import cache

from .models import Doctor

_CLINIC_DOCTORS_CACHE_KEY = 'clinic_doctors_v1'
_CLINIC_DOCTORS_TTL = 60 * 60 * 6  # 6 hours; invalidated by dashboard.signals on Doctor writes


def clinic_doctors(request):
    """
    Expose the clinic's active doctors to every template so the footer / any
    layout can iterate them without a per-view query. Cached because every
    page loads it; invalidated when a Doctor row is written.
    """
    doctors = cache.get(_CLINIC_DOCTORS_CACHE_KEY)
    if doctors is None:
        doctors = list(
            Doctor.objects
            .select_related('user')
            .filter(user__is_active=True)
            .order_by('user__first_name', 'user__last_name')
        )
        cache.set(_CLINIC_DOCTORS_CACHE_KEY, doctors, _CLINIC_DOCTORS_TTL)
    return {'clinic_doctors': doctors}


def invalidate_clinic_doctors_cache():
    cache.delete(_CLINIC_DOCTORS_CACHE_KEY)
