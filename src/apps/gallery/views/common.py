"""
Shared between the public and staff gallery views.

Lives apart so `manage_view` does not have to import `public_view` (or the
reverse) just to reach a queryset helper — an import cycle waiting to happen
the first time one of them needs something from the other.
"""
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from utils.http.mixins import DoctorOrSuperuserRequiredMixin, require_staff, user_owns

from ..models import Gallery


class _GalleryOwnerAccessMixin(DoctorOrSuperuserRequiredMixin):
    """
    Fetch the target gallery from the URL and enforce ownership rules.
    Superusers can act on any gallery (including a superuser who is also a
    doctor); doctors only on their own. See :func:`utils.http.mixins.user_owns`.
    """

    gallery_queryset = None

    def dispatch(self, request, *args, **kwargs):
        # Staff gate first — this override precedes DoctorOrSuperuserRequiredMixin
        # in the MRO, so an ownership check placed first would 403 anonymous
        # users and leak that the gallery id exists.
        require_staff(request)
        queryset = self.gallery_queryset or Gallery.objects.select_related('doctor__user')
        self.gallery = get_object_or_404(queryset, pk=kwargs['pk'])
        if not user_owns(request.user, self.gallery.doctor):
            raise PermissionDenied("شما فقط می‌توانید گالری‌های خودتان را ویرایش کنید")
        return super().dispatch(request, *args, **kwargs)



GALLERY_PAGE_SIZE = 4

# Masonry rhythm. Applied by absolute position so tiles appended by "load more"
# continue the pattern instead of restarting it.
MASONRY_SPANS = ('tall', 'wide', 'normal', 'normal', 'tall', 'normal')


def _galleries_queryset():
    return (
        Gallery.objects
        .select_related('category', 'doctor__user')
        .prefetch_related('images')
    )


def _page(queryset, offset, size):
    """
    Slice one page of galleries and report whether anything follows.

    Fetches one row past the page and trims it, rather than inferring
    ``has_more`` from a full page: when the total is an exact multiple of the
    page size that guess costs the user one dead click that appends nothing.
    """
    window = list(queryset[offset:offset + size + 1])
    return window[:size], len(window) > size


def _with_masonry_spans(galleries, offset=0):
    """
    Tag each gallery with the span its position implies, and drop empty ones
    (a tile with no images renders as a blank box).
    """
    kept = []
    for index, gallery in enumerate(galleries, start=offset):
        if not gallery.images.all():
            continue
        gallery.masonry_span = MASONRY_SPANS[index % len(MASONRY_SPANS)]
        kept.append(gallery)
    return kept


