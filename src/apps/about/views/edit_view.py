"""Staff-only editing of the About singleton (the clinic profile)."""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from utils.http.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

from ..forms import AboutForm
from ..models import About


class AboutEditView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """Singleton edit for the About row (clinic profile)."""
    template_name = 'about/about_edit.html'
    form_class = AboutForm

    def _instance(self):
        return About.get_solo()

    def get(self, request, *args, **kwargs):
        instance = self._instance()
        return render(request, self.template_name, {
            'form': self.form_class(instance=instance),
            'about': instance,
            'has_about': instance is not None,
        })

    def post(self, request, *args, **kwargs):
        instance = self._instance()
        form = self.form_class(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'اطلاعات درباره ما با موفقیت ذخیره شد')
            return redirect('about:about_edit')
        return render(request, self.template_name, {
            'form': form,
            'about': instance,
            'has_about': instance is not None,
        })
