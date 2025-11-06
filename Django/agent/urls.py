from django.urls import path
from . import views

app_name = "agent"

urlpatterns = [
    path("", views.agent_home, name="index"),
    path("<int:conversation_id>/", views.agent_index, name="detail"),
    path("<int:conversation_id>/save_prompt/", views.save_prompt, name="save_prompt"),
    path("<int:conversation_id>/upload/", views.upload_to_conversation, name="upload"),
]
