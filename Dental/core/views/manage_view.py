from utils.common_imports import View, render
from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

class ManageView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    ManageView handles the display of various management-related data for the dental clinic.
    It ensures that only doctors or superusers can access this view and applies rate limiting.
    """
    template_name = 'core/manage.html'
         
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
