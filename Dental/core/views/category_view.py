from django.views import View
from django.shortcuts import render, redirect
from django.http import Http404
from django.contrib import messages
from core.forms import CategoryForm
from core.models import Category

class CategoryView(View):
    form_class = CategoryForm
    template_name = 'core/category.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        form = self.form_class()
        return render(request, self.template_name, {'categories': categories, 'form': form})
    
class AddCategoryView(View):
    form_class = CategoryForm
    template_name = 'core/add_category.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "دسته‌بندی جدید با موفقیت ایجاد شد.")
            return redirect('core:category')
        messages.error(request, "خطا در ایجاد دسته‌بندی. لطفاً دوباره تلاش کنید.")
        return render(request, self.template_name, {'form': form})

class RemoveCategoryView(View):
    template_name = 'core/remove_category.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_doctor or request.user.is_superuser):
            return super().dispatch(request, *args, **kwargs)
        raise Http404("صفحه مورد نظر یافت نشد.")
    
    def post(self, request, *args, **kwargs):
        category = Category.objects.get(pk=kwargs['pk'])
        category.delete()
        messages.success(request, "دسته‌بندی با موفقیت حذف شد.")
        return redirect('core:category')