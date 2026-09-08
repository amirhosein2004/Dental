"""
Cache-invalidation wiring for the About singleton and the practices.
Also bumps the shared cache groups so cross-app cached views (home, about,
contact) re-render immediately after edits.
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from utils.http.cache import invalidate_group

from .context_processors import invalidate_about_info_cache
from .models import About, Branch


@receiver([post_save, post_delete], sender=About)
def _bust_on_about_change(sender, **kwargs):
    invalidate_about_info_cache()
    invalidate_group('home')
    invalidate_group('about')
    invalidate_group('contact')


@receiver([post_save, post_delete], sender=Branch)
def _bust_on_branch_change(sender, **kwargs):
    # The footer renders every branch on every page, and that comes from the
    # context processor's own cache — bumping the view groups alone would
    # leave a stale address in the footer of every cached page.
    invalidate_about_info_cache()
    # Opening hours live here now, and the contact page caches them.
    invalidate_group('contact')
    invalidate_group('home')
