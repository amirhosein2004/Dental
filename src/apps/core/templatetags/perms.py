"""
Template-side view of the ownership rule.

The buttons a template shows must match what the view actually allows. Both
sides now call :func:`utils.http.mixins.user_owns`, so the rule lives in exactly one
place and cannot drift.
"""
from django import template

from utils.http.mixins import user_owns

register = template.Library()


@register.filter(name='can_manage')
def can_manage(user, owner_doctor):
    """
    True when `user` may edit/delete content owned by `owner_doctor`.

    Usage::

        {% load perms %}
        {% if user|can_manage:blog.writer %} ... {% endif %}
        {% if user|can_manage:gallery.doctor %} ... {% endif %}

    `owner_doctor` may be None (orphaned content) — superusers still pass.
    """
    return user_owns(user, owner_doctor)
