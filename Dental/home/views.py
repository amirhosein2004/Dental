from django.http import Http404
from django.views import View
from django.shortcuts import render
from .models import Banner

class HomeView(View):

    template_name = 'home/home.html'

    def get(self, request, *args, **kwargs):
        try:
            banners = Banner.objects.all()
        except Banner.DoesNotExist:
            raise Http404("No banners found.")
        return render(request, self.template_name, {'banners': banners})