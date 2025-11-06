from django.contrib import admin
from .models import Business


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "code", "created_at")
    search_fields = ("name", "slug", "code", "description")


# Documents now belong to the Agent app
