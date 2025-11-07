from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from typing import cast

from .models import Client
from .forms import ClientForm
from django.contrib import messages
from .permissions import can_delete_client
from django.contrib.messages.views import SuccessMessageMixin

class ClientListView(ListView):
    model = Client
    template_name = "client/list.html"
    context_object_name = "clientes"
    # Meta.ordering already sorts by name; keep explicit for clarity
    queryset = Client.objects.all().order_by("name")
    paginate_by = 20  # Simple pagination for large lists

class ClientCreateView(SuccessMessageMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "client/create.html"
    success_message = "Negocio creado correctamente."

    def form_valid(self, form):
        # No owner attribute; proceed with default form handling
        return super().form_valid(form)

class ClientDetailView(DetailView):
    model = Client
    template_name = "client/detail.html"
    context_object_name = "client"
    slug_field = "slug"
    slug_url_kwarg = "slug"

class ClientDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Client
    slug_field = "slug"
    slug_url_kwarg = "slug"
    http_method_names = ["post"]  # keep delete as POST-only, no GET confirmation
    success_url = reverse_lazy('client:list')
    permission_denied_message = "No tienes permiso para eliminar este cliente."

    def test_func(self) -> bool:
        return can_delete_client(self.request.user, self.get_object())

    def handle_no_permission(self) -> HttpResponseRedirect:
        messages.error(self.request, "No tienes permiso para eliminar este cliente.")
        return cast(HttpResponseRedirect, redirect('client:list'))

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Cliente eliminado correctamente.")
        return response
