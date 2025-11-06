from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from typing import cast

from .models import Business
from .forms import BusinessForm
from django.contrib import messages
from .permissions import can_delete_business
from django.contrib.messages.views import SuccessMessageMixin

class BusinessListView(ListView):
    model = Business
    template_name = "business/list.html"
    context_object_name = "businesses"
    # Meta.ordering already sorts by name; keep explicit for clarity
    queryset = Business.objects.all().order_by("name")
    paginate_by = 20  # Simple pagination for large lists

class BusinessCreateView(SuccessMessageMixin, CreateView):
    model = Business
    form_class = BusinessForm
    template_name = "business/create.html"
    success_message = "Negocio creado correctamente."

    def form_valid(self, form):
        # No owner attribute; proceed with default form handling
        return super().form_valid(form)

class BusinessDetailView(DetailView):
    model = Business
    template_name = "business/detail.html"
    context_object_name = "business"
    slug_field = "slug"
    slug_url_kwarg = "slug"

class BusinessDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Business
    slug_field = "slug"
    slug_url_kwarg = "slug"
    http_method_names = ["post"]  # keep delete as POST-only, no GET confirmation
    success_url = reverse_lazy('business:list')
    permission_denied_message = "No tienes permiso para eliminar este negocio."

    def test_func(self) -> bool:
        return can_delete_business(self.request.user, self.get_object())

    def handle_no_permission(self) -> HttpResponseRedirect:
        messages.error(self.request, "No tienes permiso para eliminar este negocio.")
        return cast(HttpResponseRedirect, redirect('business:list'))

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Negocio eliminado correctamente.")
        return response
