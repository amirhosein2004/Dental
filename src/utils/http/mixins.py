from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

from django_ratelimit.decorators import ratelimit

from utils.security.sessions import validate_otp_token


def client_ip_rate_key(group, request):
    """
    Rate-limit key resolver used behind a reverse proxy (Nginx).

    django-ratelimit's built-in `key='ip'` reads REMOTE_ADDR, which behind
    Nginx is the proxy's own address — every real client would collapse onto
    a single bucket. Prefer the forwarded IP set by the proxy, falling back
    to REMOTE_ADDR only when no proxy header is present.
    """
    real_ip = request.META.get('HTTP_X_REAL_IP')
    if real_ip:
        return real_ip.strip()
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def require_staff(request):
    """
    Raise Http404 unless the user is a doctor or a superuser.

    404 rather than 403 on purpose: staff URLs should not confirm their own
    existence to the public. Call this *before* any ownership check — a
    subclass that overrides ``dispatch`` runs ahead of
    :class:`DoctorOrSuperuserRequiredMixin` in the MRO, so an ownership check
    placed first would answer anonymous requests with 403 and leak both the
    route and the validity of the object id in the URL.
    """
    user = request.user
    # `is_authenticated` is checked first so AnonymousUser never reaches the
    # `is_doctor` lookup (which it does not define).
    if not (user.is_authenticated and (user.is_doctor or user.is_superuser)):
        raise Http404("صفحه مورد نظر یافت نشد")


class DoctorOrSuperuserRequiredMixin:
    """Mixin to check if the user is logged in and is either a doctor or a superuser."""

    def dispatch(self, request, *args, **kwargs):
        require_staff(request)
        return super().dispatch(request, *args, **kwargs)


def user_owns(user, owner_doctor):
    """
    Single source of truth for "may this user act on content owned by
    ``owner_doctor``".

    Rules:
      * Superusers may act on anything — including a superuser who is *also*
        flagged as a doctor. The superuser check therefore comes first and is
        never gated behind ``is_doctor``.
      * A doctor may act only on their own content.
      * Orphaned content (``owner_doctor is None``, e.g. the owning Doctor row
        was deleted) is superuser-only. Returning False instead of touching
        ``owner_doctor.user`` avoids an AttributeError 500.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if owner_doctor is None:
        return False
    return user.pk == owner_doctor.user_id


def safe_next_url(request, fallback):
    """
    Return the request's ``next`` parameter only when it points back at this
    site, otherwise ``fallback``.

    Echoing an unvalidated ``next`` into ``redirect()`` is an open redirect:
    a crafted form post could bounce staff to an attacker-controlled page that
    imitates the clinic's login screen.
    """
    candidate = request.POST.get('next') or request.GET.get('next')
    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return fallback


def get_doctor_profile(user):
    """
    Return the user's :class:`dashboard.models.Doctor` row, or None.

    ``user.doctor`` raises ``Doctor.DoesNotExist`` when the flag is set but no
    profile row exists (e.g. the profile was deleted from the admin), which
    would surface as a 500. Callers get None and decide.
    """
    if not user.is_authenticated:
        return None
    try:
        return user.doctor
    except ObjectDoesNotExist:
        return None


class RedirectIfAuthenticatedMixin:
    """Mixin to redirect the user if they are already authenticated."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.error(request, "شما در حال حاضر وارد شده‌اید")
            return redirect('home:home')
        return super().dispatch(request, *args, **kwargs)


class RateLimitMixin:
    """Rate-limit view dispatches. IP-keyed and proxy-aware by default."""

    rate_limit = '20/m'
    method_limit = ['POST']
    # staticmethod wrapper so ``self.key_limit`` yields the plain function,
    # not a bound method (django-ratelimit calls it as ``key(group, request)``).
    key_limit = staticmethod(client_ip_rate_key)
    error_message = "حداکثر تعداد درخواست‌ها در دقیقه رسیده است. لطفاً کمی صبر کنید"

    def dispatch(self, request, *args, **kwargs):
        # Apply and count the rate limit exactly once; short-circuit if limited.
        probe = ratelimit(
            key=self.key_limit,
            rate=self.rate_limit,
            method=self.method_limit,
            block=False,
        )(lambda req, *a, **kw: None)
        probe(request, *args, **kwargs)

        if getattr(request, 'limited', False):
            return HttpResponse(self.error_message, status=429)

        return super().dispatch(request, *args, **kwargs)


class SessionValidatorMixin:
    """
    Validate the signed OTP session token before letting the view run.
    Expiry lives on :func:`utils.security.sessions.validate_otp_token` (single source
    of truth); this mixin only orchestrates redirects.
    """

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.error(request, "شما در حال حاضر وارد شده‌اید")
            return redirect('home:home')

        user, error = validate_otp_token(request)
        if error:
            request.session.flush()
            messages.error(request, error)
            return redirect('accounts:doctor_login')

        self.user = user
        return super().dispatch(request, *args, **kwargs)