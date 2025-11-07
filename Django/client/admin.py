from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "code", "created_at")
    search_fields = ("name", "slug", "code", "description")


# Documents now belong to the Agent app
