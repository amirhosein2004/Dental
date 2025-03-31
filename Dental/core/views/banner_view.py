from utils.common_imports import View, redirect, render, messages, get_object_or_404
from utils.mixins import RateLimitMixin, DoctorOrSuperuserRequiredMixin
from core.models import Banner
from core.forms import BannerForm


class BannerView(DoctorOrSuperuserRequiredMixin, View):
    """
    View to display all banners and a form to add a new banner.
    """
    template_name = 'core/banner.html'
    form_class = BannerForm

    def get(self, request, *args, **kwargs):
        banners = Banner.objects.all()
        form = self.form_class()
        return render(request, self.template_name, {'form': form ,'banners': banners})

class AddBannerView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle adding a new banner.
    """
    template_name = 'core/banner.html'
    form_class = BannerForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        banners = Banner.objects.all()
        context = {'form': form, 'banners': banners}
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        banners = Banner.objects.all()
        context = {'form': form, 'banners': banners}
        if form.is_valid():
            form.save()
            messages.success(request, 'بنر با موفقیت اضافه شد')
            return redirect('core:banner')
        
        return render(request, self.template_name, context)

class RemoveBannerView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle removing an existing banner.
    """

    def post(self, request, *args, **kwargs):
        banner = get_object_or_404(Banner, pk=kwargs['pk'])
        banner.delete()
        messages.success(request, "بنر با موفقیت حذف شد")
        return redirect('core:banner')