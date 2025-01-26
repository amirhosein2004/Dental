from django.http import HttpResponse
from django.views import View
from django.shortcuts import render
from .models import Banner

class HomeView(View):

    def get(self, request, *args, **kwargs):
        banners = Banner.objects.all()
        return render(request, 'home/home.html', {'banners':banners})
    
    def post(self, request, *args, **kwargs):
        pass