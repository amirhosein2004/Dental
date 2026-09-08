"""
Public doctor profiles.

The ``Doctor`` model itself stays in ``apps.dashboard`` — it has been there
since the beginning and ``blog.BlogPost.writer`` points at it, so moving it
would mean a migration across three apps to gain nothing. What lives here is
the *public* half: a CV page per doctor, at a URL a patient searching a name
can actually land on. ``/dashboard/`` is the staff area and is excluded from
indexing; these pages are the opposite of that.
"""
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import render
from django.views import View

from apps.about.models import Branch
from apps.dashboard.models import Doctor
from utils.http.cache import get_cache_key


class DoctorListView(View):
    """Every published doctor — the hub that links to each CV page."""

    template_name = 'doctors/doctor_list.html'

    def get(self, request, *args, **kwargs):
        cache_key = get_cache_key(
            request, cache_view='doctorlist_data', group='doctors', public=True,
        )
        cached = cache.get(cache_key)
        if cached is None:
            cached = {
                'doctors': list(
                    Doctor.objects
                    .filter(is_published=True, user__is_active=True)
                    .select_related('user')
                    .prefetch_related('branches')
                ),
                'branches': list(Branch.objects.all()),
            }
            cache.set(cache_key, cached, 86400)

        return render(request, self.template_name, cached)


class DoctorDetailView(View):
    """
    One doctor's CV.

    Unpublished profiles 404 rather than redirect: a redirect would hand the
    ranking the profile had accumulated to whatever it pointed at, and a
    profile is usually unpublished because it is half-written, not because it
    moved.
    """

    template_name = 'doctors/doctor_detail.html'

    def get(self, request, slug, *args, **kwargs):
        cache_key = get_cache_key(
            request, cache_view=f'doctordetail_{slug}', group='doctors', public=True,
        )
        cached = cache.get(cache_key)

        if cached is None:
            try:
                doctor = (
                    Doctor.objects
                    .select_related('user')
                    .prefetch_related('branches', 'services')
                    .get(slug=slug, is_published=True, user__is_active=True)
                )
            except Doctor.DoesNotExist:
                raise Http404("چنین پزشکی یافت نشد")

            cached = {
                'doctor': doctor,
                'branches': list(doctor.branches.all()) or list(Branch.objects.all()),
                'services': list(doctor.services.all()),
                'posts': list(
                    doctor.blog_posts.only('title', 'slug', 'image', 'updated_at')[:3]
                ),
            }
            cache.set(cache_key, cached, 86400)

        return render(request, self.template_name, cached)
