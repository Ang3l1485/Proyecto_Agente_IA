from django import forms
from .models import Agent, Prompt, Document

class AgentCreateForm(forms.ModelForm):
    class Meta:
        model = Agent
        fields = ["business", "name", "description"]

class PromptForm(forms.ModelForm):
    class Meta:
        model = Prompt
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 6}),
        }

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["file"]