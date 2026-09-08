from django.views.generic import TemplateView

from utils.http.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin


class ManageView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, TemplateView):
    """Landing page for management shortcuts. Doctors and superusers only."""
    template_name = 'core/manage.html'
