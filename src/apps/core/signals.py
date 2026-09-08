"""
Cache-invalidation wiring for core models. Every model that participates in a
cached view is mapped to the cache groups it can affect. On save/delete, those
groups' versions are bumped, which invalidates the derived per-request keys.
"""
from django.db.models.signals import post_save, post_delete

from utils.http.cache import invalidate_group

from .context_processors import invalidate_ld_services_cache
from .models import Category


def _build_invalidation_map():
    """
    Build the {model: [groups]} map lazily so imports of models from other
    apps happen once the app registry is populated.
    """
    from apps.about.models import Branch
    from apps.blog.models import BlogPost
    from apps.dashboard.models import Doctor
    from apps.gallery.models import Gallery, Image
    from apps.pricing.models import PricingCategory, PricingItem
    from apps.service.models import Service, ServiceFAQ
    from apps.users.models import CustomUser

    return {
        # core
        Category: ['blog', 'gallery'],
        # cross-app
        # `doctors` too: a CV page lists the treatments that doctor performs,
        # by title, so renaming a service changes those pages as well.
        Service: ['home', 'about', 'service', 'doctors'],
        ServiceFAQ: ['service'],
        BlogPost: ['home', 'blog'],
        Gallery: ['home', 'gallery'],
        # `home` as well as `gallery`: the home page renders up to three images
        # per gallery tile, so adding one to an existing gallery changes it.
        Image: ['home', 'gallery'],
        PricingItem: ['pricing'],
        PricingCategory: ['pricing'],
        Doctor: ['home', 'about', 'gallery', 'doctors'],
        # Address and phone differ per practice and are rendered on the
        # contact page, on every CV page, and inside the LocalBusiness
        # JSON-LD that the service pages carry.
        Branch: ['home', 'about', 'contact', 'service', 'doctors'],
        # A doctor's name and photo live on the user row, not on Doctor, and
        # both the home and about pages render them. Editing a profile through
        # the dashboard writes here, so it has to invalidate the same groups a
        # Doctor write does.
        CustomUser: ['home', 'about', 'gallery', 'doctors'],
    }


def _invalidate(sender, **kwargs):
    for group in CACHE_INVALIDATION_MAP.get(sender, ()):
        invalidate_group(group)

    # The site-wide JSON-LD lists every treatment, on every page, from its own
    # cache. Bumping the view groups alone would leave a deleted service named
    # in the structured data of the whole site until the entry expired.
    if sender.__name__ == 'Service':
        invalidate_ld_services_cache()


CACHE_INVALIDATION_MAP = _build_invalidation_map()

for _model in CACHE_INVALIDATION_MAP:
    post_save.connect(_invalidate, sender=_model, weak=False)
    post_delete.connect(_invalidate, sender=_model, weak=False)
