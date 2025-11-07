from django.urls import path
from . import views

app_name = "agent"

urlpatterns = [
    path("", views.AgentHomeView.as_view(), name="index"),
    path("<int:conversation_id>/", views.AgentIndexView.as_view(), name="detail"),
    path("<int:conversation_id>/save_prompt/", views.SavePromptView.as_view(), name="save_prompt"),
    path("<int:conversation_id>/upload/", views.UploadToConversationView.as_view(), name="upload"),
]
