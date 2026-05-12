from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages

from .models import Company
from .forms import CompanyForm

class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff status for views"""
    def test_func(self):
        return self.request.user.is_staff

class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin to require superuser status for views"""
    def test_func(self):
        return self.request.user.is_superuser

class CompanyDetailView(LoginRequiredMixin, DetailView):
    """View to display company details"""
    model = Company
    template_name = 'company/company_detail.html'
    context_object_name = 'company'

    def get_object(self, queryset=None):
        # Get the first company or create one if none exists
        return Company.get_solo()

class CompanyCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    """View to create a new company"""
    model = Company
    form_class = CompanyForm
    template_name = 'company/company_form.html'

    def get_success_url(self):
        messages.success(self.request, 'Company information created successfully.')
        # Redirect to the detail view after successful creation
        return reverse_lazy('company_detail')

class CompanyUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """View to update company information"""
    model = Company
    form_class = CompanyForm
    template_name = 'company/company_form.html'

    def get_object(self, queryset=None):
        # Get the first company or create one if none exists
        return Company.get_solo()

    def get_success_url(self):
        messages.success(self.request, 'Company information updated successfully.')
        # Redirect to the detail view after successful update
        return reverse_lazy('company_detail')
