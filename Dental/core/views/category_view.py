from utils.common_imports import View, render, redirect, messages, get_object_or_404
from core.forms import CategoryForm
from core.models import Category
from utils.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

class CategoryView(DoctorOrSuperuserRequiredMixin, View):
    """
    View to display all categories and a form to add a new category.
    """
    form_class = CategoryForm
    template_name = 'core/category.html'

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        form = self.form_class()
        context = {'categories': categories, 'form': form}
        return render(request, self.template_name, context)
    
class AddCategoryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle adding a new category.
    """
    form_class = CategoryForm
    template_name = 'core/add_category.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {'form': form}
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        context = {'form': form}
        if form.is_valid():
            form.save()
            messages.success(request, "دسته‌بندی جدید با موفقیت ایجاد شد")
            return redirect('core:category')

        return render(request, self.template_name, context)
    
class UpdateCategoryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle updating an existing category.
    """
    form_class = CategoryForm
    template_name = 'core/update_category.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to get the category object.
        """
        self.category = get_object_or_404(Category, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs) 

    def get(self, request, *args, **kwargs):
        form = self.form_class(instance=self.category)
        context = {'form': form}
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, instance=self.category)
        context = {'form': form}
        if form.is_valid():
            form.save()
            messages.success(request, "دسته‌بندی با موفقیت بروز رسانی شد")
            return redirect('core:category')

        return render(request, self.template_name, context)

class RemoveCategoryView(RateLimitMixin, DoctorOrSuperuserRequiredMixin, View):
    """
    View to handle removing an existing category.
    """
    template_name = 'core/remove_category.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to get the category object.
        """
        self.category = get_object_or_404(Category, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs) 
    
    def post(self, request, *args, **kwargs):
        category = get_object_or_404(Category, pk=kwargs['pk'])
        category.delete()
        messages.success(request, "دسته‌بندی با موفقیت حذف شد")
        return redirect('core:category')