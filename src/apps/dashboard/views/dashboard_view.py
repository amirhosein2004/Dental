from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views import View

from apps.users.forms import CustomUserDoctorUpdateForm
from utils.http.mixins import (
    DoctorOrSuperuserRequiredMixin,
    RateLimitMixin,
    require_staff,
    user_owns,
)

from ..forms import DoctorForm, DoctorResumeForm
from ..models import Doctor


User = get_user_model()

class DashboardView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View for displaying and updating the doctor's dashboard.
    """
    template_name = 'dashboard/dashboard.html'
    form_class_doctor = DoctorForm
    form_class_user = CustomUserDoctorUpdateForm
    form_class_password = PasswordChangeForm
    form_class_resume = DoctorResumeForm

    # Three independent forms post back to this one URL. The hidden marker
    # says which; anything else is treated as the profile form, so a client
    # that never sent one — a script, the existing tests — keeps working.
    RESUME_MARKER = 'resume'

    def dispatch(self, request, *args, **kwargs):
        """
        Handle the request and ensure the user has permission to view the dashboard.

        Superusers reach every dashboard — including a superuser who is *also*
        flagged as a doctor. The previous check keyed off ``is_doctor`` alone,
        which locked doctor-superusers out of their colleagues' dashboards.
        """
        # Gate on staff-ness before touching the DB: this override runs ahead
        # of DoctorOrSuperuserRequiredMixin in the MRO, so without this the
        # ownership check below would answer anonymous users with 403.
        require_staff(request)

        # Fetch the doctor object with related blog posts and galleries
        self.doctor = get_object_or_404(
            Doctor.objects.select_related('user').prefetch_related(
                'blog_posts', 'doctor_galleries__images'
            ),
            id=kwargs['doctor_id']
        )
        self.blogs = self.doctor.blog_posts.all()
        self.galleries = self.doctor.doctor_galleries.all()

        if not user_owns(request.user, self.doctor):
            raise PermissionDenied("شما فقط می‌توانید داشبورد خودتان را مشاهده کنید")

        return super().dispatch(request, *args, **kwargs)

    def _context(self, **forms):
        context = {
            'doctor': self.doctor,
            'blogs': self.blogs,
            'galleries': self.galleries,
            'doctor_form': self.form_class_doctor(instance=self.doctor),
            'user_form': self.form_class_user(instance=self.doctor.user),
            'resume_form': self.form_class_resume(
                instance=self.doctor, user=self.request.user,
            ),
            'password_form': self._password_form(),
        }
        # A bound form replaces its unbound twin, so the fields the user just
        # typed — and their errors — survive the re-render.
        context.update(forms)
        return context

    def _password_form(self):
        """
        The change-password block, with Django's autofocus taken back off.

        ``PasswordChangeForm`` marks ``old_password`` ``autofocus=True``, which
        is right on the standalone change-password page where that field is the
        only thing on screen. Here it is the fourth card down, and the browser
        honours autofocus by scrolling to it — so opening the dashboard jumped
        straight past the profile, the CV and the hero to the password form.
        """
        form = self.form_class_password(user=self.doctor.user)
        form.fields['old_password'].widget.attrs.pop('autofocus', None)
        return form

    def get(self, request, *args, **kwargs):
        """Render the dashboard with every form unbound."""
        return render(request, self.template_name, self._context())
    
    def post(self, request, *args, **kwargs):
        """Save whichever of the two editable forms was submitted."""
        if request.POST.get('form_kind') == self.RESUME_MARKER:
            return self._post_resume(request)
        return self._post_profile(request)

    def _post_profile(self, request):
        user_form = self.form_class_user(request.POST, request.FILES, instance=self.doctor.user)
        doctor_form = self.form_class_doctor(request.POST, instance=self.doctor)

        if user_form.is_valid() and doctor_form.is_valid():
            with transaction.atomic():
                user_form.save()
                doctor_form.save()
                messages.success(request, "تغییرات با موفقیت ذخیره شدند")
        else:
            messages.error(request, "خطا در اعتبارسنجی فرم‌ها")

        return render(request, self.template_name, self._context(
            doctor_form=doctor_form, user_form=user_form,
        ))

    def _post_resume(self, request):
        """
        The CV block.

        Saved on its own rather than merged into the profile form: they edit
        the same row but are two screens' worth of fields, and a validation
        error in one would otherwise discard everything typed in the other.
        """
        resume_form = self.form_class_resume(
            request.POST, instance=self.doctor, user=request.user,
        )

        if resume_form.is_valid():
            resume_form.save()
            messages.success(request, "رزومه با موفقیت ذخیره شد")
        else:
            messages.error(request, "خطا در اعتبارسنجی فرم رزومه")

        return render(request, self.template_name, self._context(resume_form=resume_form))

class DashboardListView(View):
    """
    View for displaying a list of all doctors for superusers.
    """
    template_name = 'dashboard/dashboard_list.html'

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_superuser):
            raise Http404("صفحه مورد نظر یافت نشد.")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        doctors = Doctor.objects.select_related('user').all()
        return render(request, self.template_name, {'doctors': doctors})