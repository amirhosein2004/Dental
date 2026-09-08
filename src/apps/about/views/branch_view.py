"""
Staff CRUD for the practices themselves.

``Branch`` carries everything that differs between the two locations — the
address, the phone numbers, the hours, the map link — and every one of those
is rendered on every page of the site through the footer. Until this module
existed the only way to fix a wrong phone number was the Django admin, i.e. a
superuser account, which is exactly the wrong requirement for the field most
likely to need correcting.
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from utils.http.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

from ..forms import BranchForm
from ..models import Branch


class BranchListView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """Every practice, as cards, with the add/edit/delete entry points."""
    template_name = 'about/branch_list.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'branch_rows': Branch.objects.all(),
        })


class BranchCreateView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """Add a practice."""
    template_name = 'about/branch_form.html'
    form_class = BranchForm

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'form': self.form_class(),
            'is_create': True,
        })

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'مطب جدید ثبت شد')
            return redirect('about:branch_list')
        messages.error(request, 'خطا در ثبت مطب — فرم را بررسی کنید')
        return render(request, self.template_name, {
            'form': form,
            'is_create': True,
        })


class BranchUpdateView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """Edit one practice."""
    template_name = 'about/branch_form.html'
    form_class = BranchForm

    def dispatch(self, request, *args, **kwargs):
        self.branch = get_object_or_404(Branch, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'form': self.form_class(instance=self.branch),
            'branch': self.branch,
            'is_create': False,
        })

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, instance=self.branch)
        if form.is_valid():
            form.save()
            messages.success(request, 'اطلاعات مطب ذخیره شد')
            return redirect('about:branch_list')
        messages.error(request, 'خطا در ذخیره مطب — فرم را بررسی کنید')
        return render(request, self.template_name, {
            'form': form,
            'branch': self.branch,
            'is_create': False,
        })


class BranchDeleteView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    Remove a practice.

    POST-only: a GET that deletes is one crawler visit away from wiping the
    site's contact details, and this URL is reachable by every doctor account.
    """

    def get(self, request, *args, **kwargs):
        return redirect('about:branch_list')

    def post(self, request, *args, **kwargs):
        branch = get_object_or_404(Branch, pk=kwargs['pk'])
        branch.delete()
        messages.success(request, 'مطب حذف شد')
        return redirect('about:branch_list')
