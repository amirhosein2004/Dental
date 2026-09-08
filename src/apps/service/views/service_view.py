from django.contrib import messages
from django.core.cache import cache
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin

from utils.http.cache import get_cache_key
from utils.http.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

from ..forms import ServiceFAQFormSet, ServiceForm, StandaloneServiceFAQForm
from ..models import Service


class ServiceView(View):
    """Public services list with a data-level cache."""
    template_name = 'service/service.html'

    def get(self, request, *args, **kwargs):
        # No vary_on: the services page reads nothing from the query string.
        cache_key = get_cache_key(
            request, cache_view='serviceview_data', group='service', public=True,
        )
        cached_data = cache.get(cache_key)
        if cached_data is None:
            cached_data = {'services': list(Service.objects.all())}
            cache.set(cache_key, cached_data, 86400)

        return render(request, self.template_name, {'services': cached_data['services']})


class ServiceDetailView(View):
    """
    One treatment, on its own page.

    The list page can only be the best answer to one query; every treatment
    sharing it meant none of them ranked for their own name. Each page here
    carries its own heading, its own body text and its own FAQ, which is what
    a search for that treatment can actually match.
    """
    template_name = 'service/service_detail.html'

    def get(self, request, slug, *args, **kwargs):
        cache_key = get_cache_key(
            request, cache_view=f'servicedetail_{slug}', group='service', public=True,
        )
        cached_data = cache.get(cache_key)

        if cached_data is None:
            try:
                service = (
                    Service.objects
                    .prefetch_related('faqs', 'doctors__user')
                    .get(slug=slug)
                )
            except Service.DoesNotExist:
                raise Http404("چنین خدمتی یافت نشد")

            cached_data = {
                'service': service,
                'faqs': list(service.faqs.all()),
                'doctors': list(service.doctors.filter(is_published=True)),
                # Sibling treatments, for internal linking. A visitor reading
                # about implants is a plausible reader of the bone-graft page,
                # and the link passes both a visitor and ranking signal.
                'related': list(Service.objects.exclude(pk=service.pk)[:4]),
            }
            cache.set(cache_key, cached_data, 86400)

        return render(request, self.template_name, cached_data)


class _ServiceFormsetMixin:
    """
    Shared create/update plumbing for the treatment form + its FAQ rows.

    The questions live on the treatment's own page — a standalone FAQ page
    would compete with these very treatments for the same searches — so they
    are edited here rather than anywhere else, and a formset is the only way
    to save the parent and its children in one submit.
    """
    model = Service
    form_class = ServiceForm
    faq_prefix = 'faqs'

    def get_form_kwargs(self):
        # `ServiceForm` drops the two SEO override boxes for anyone who is not
        # a superuser; it needs the user to decide that.
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'faq_formset' not in context:
            context['faq_formset'] = ServiceFAQFormSet(
                instance=self.object, prefix=self.faq_prefix,
            )
        # Same rule as the form, so the panel heading and its note do not
        # render around an empty space.
        context['show_seo_fields'] = self.request.user.is_superuser
        return context

    def _has_faq_data(self):
        """
        Whether this POST carried the FAQ formset at all.

        The questions are an optional block on the treatment form, so a submit
        that does not include them — a script, a test, a client that posts only
        the treatment fields — must still save the treatment. Without this
        check the absent ManagementForm reads as a tampered one and the whole
        submit is rejected with an error the caller never asked about.
        """
        return f'{self.faq_prefix}-TOTAL_FORMS' in self.request.POST

    def form_valid(self, form):
        if not self._has_faq_data():
            return super().form_valid(form)

        formset = ServiceFAQFormSet(
            self.request.POST, instance=form.instance, prefix=self.faq_prefix,
        )
        if not formset.is_valid():
            # Hand the bound formset back so the questions the user typed are
            # still on screen with their errors, rather than silently dropped.
            return self.render_to_response(
                self.get_context_data(form=form, faq_formset=formset)
            )

        # One transaction: a treatment saved without its questions, or the
        # reverse, is worse than the whole submit failing.
        with transaction.atomic():
            response = super().form_valid(form)
            formset.instance = self.object
            formset.save()
        return response

    def form_invalid(self, form):
        if not self._has_faq_data():
            return super().form_invalid(form)

        formset = ServiceFAQFormSet(
            self.request.POST, instance=self.object, prefix=self.faq_prefix,
        )
        return self.render_to_response(
            self.get_context_data(form=form, faq_formset=formset)
        )


class AddServiceView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, SuccessMessageMixin,
                     _ServiceFormsetMixin, CreateView):
    template_name = 'service/add_service.html'
    success_url = reverse_lazy('service:service_list')
    success_message = "سرویس جدید با موفقیت ایجاد شد"


class UpdateServiceView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, SuccessMessageMixin,
                        _ServiceFormsetMixin, UpdateView):
    template_name = 'service/update_service.html'
    context_object_name = 'service'
    success_url = reverse_lazy('service:service_list')
    success_message = "سرویس با موفقیت ویرایش شد"


class RemoveServiceView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Service
    template_name = 'service/remove_service.html'
    context_object_name = 'service'
    success_url = reverse_lazy('service:service_list')
    success_message = "سرویس با موفقیت حذف شد"


class ServiceFAQHubView(DoctorOrSuperuserRequiredMixin, View):
    """
    Every treatment with the number of questions it carries — and a form to
    write a new question straight from here.

    A ``ServiceFAQ`` cannot exist without a treatment, so the form's first
    field is which treatment it belongs to; picking one is what attaches the
    question to that treatment's page. The list underneath answers the other
    half of the job: which treatment still has no questions at all.

    The question is not given a page of its own. A site-wide FAQ page would
    compete with these very treatment pages for the same searches, so the
    answer always renders on the treatment it belongs to.
    """
    template_name = 'service/faq_hub.html'
    form_class = StandaloneServiceFAQForm

    def _context(self, form):
        return {
            'form': form,
            'services': Service.objects.prefetch_related('faqs'),
        }

    def get(self, request, *args, **kwargs):
        # `?service=<pk>` lets the "این خدمت سؤالی ندارد" rows link straight
        # into the form with the treatment already chosen.
        initial = {}
        service_pk = request.GET.get('service')
        if service_pk and service_pk.isdigit():
            initial['service'] = service_pk

        return render(request, self.template_name, self._context(self.form_class(initial=initial)))

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            faq = form.save()
            messages.success(
                request, f'سؤال به خدمت «{faq.service.title}» اضافه شد',
            )
            return redirect('service:faq_hub')

        messages.error(request, 'ثبت سؤال انجام نشد؛ خطاهای زیر را برطرف کنید')
        return render(request, self.template_name, self._context(form))
