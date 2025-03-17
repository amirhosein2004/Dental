from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

@receiver([post_save, post_delete])  # هر دو سیگنال رو با هم مدیریت می‌کنه
def invalidate_cache_on_change(sender, **kwargs):
    cache.clear()