from utils.common_imports import View, render
from .models import Banner

class HomeView(View):

    template_name = 'home/home.html'

    def get(self, request, *args, **kwargs):
        banners = Banner.objects.all()
        context = {'banners': banners}
        return render(request, self.template_name, context)