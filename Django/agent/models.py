from django.db import models
from django.utils import timezone


class Agent(models.Model):
    """Un agente (bot) perteneciente a una empresa y con su propio conjunto de prompts y documentos."""
    business = models.ForeignKey('business.Business', on_delete=models.CASCADE, related_name='agents')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = ("business", "name")  # nombre único por empresa

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({getattr(self.business, 'name', 'sin empresa')})"


def agent_document_path(instance, filename: str) -> str:
    agent_id = getattr(instance, 'agent_id', None) or getattr(getattr(instance, 'agent', None), 'pk', 'unknown')
    return f"agent_documents/{agent_id}/{filename}"


class Document(models.Model):
    """Documento perteneciente a un agente específico."""
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to=agent_document_path)
    original_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:  # pragma: no cover
        return self.original_name or (self.file.name.split('/')[-1] if self.file else 'Documento')


class Prompt(models.Model):
    """Prompt del sistema asociado al agente. Puede haber historial; marca el activo con is_active."""
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='prompts')
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def save(self, *args, **kwargs):
        # Asegura que solo un prompt activo exista por agente
        super().save(*args, **kwargs)
        if self.is_active:
            Prompt.objects.filter(agent=self.agent).exclude(pk=self.pk).update(is_active=False)
