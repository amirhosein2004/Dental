from django.urls import path

from .views.about_view import AboutView
from .views.branch_view import (
    BranchCreateView,
    BranchDeleteView,
    BranchListView,
    BranchUpdateView,
)
from .views.edit_view import AboutEditView

app_name = 'about'

# The practices. Deliberately staff-only URLs — a `Branch` has no public page
# of its own (separate pages per city would be doorway pages); it is a model
# the footer, the contact page and the doctor profiles read from.
branch_patterns = [
    path('branches/', BranchListView.as_view(), name='branch_list'),
    path('branches/add/', BranchCreateView.as_view(), name='branch_add'),
    path('branches/<int:pk>/edit/', BranchUpdateView.as_view(), name='branch_edit'),
    path('branches/<int:pk>/delete/', BranchDeleteView.as_view(), name='branch_delete'),
]

urlpatterns = [
    path('', AboutView.as_view(), name='about'),
    path('edit/', AboutEditView.as_view(), name='about_edit'),
] + branch_patterns
