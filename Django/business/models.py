from django.db import models
from django.utils import timezone
from django.urls import reverse
from autoslug import AutoSlugField
import secrets
import string


class Client(models.Model):
    name = models.CharField(max_length=200)
    # Use django-autoslug to auto-populate and ensure unique slugs
    slug = AutoSlugField(populate_from='name', unique=True, max_length=220, always_update=False, blank=True)
    # Secure random code per client (password-like), generated automatically
    code = models.CharField(max_length=24, unique=True, editable=False, db_index=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Negocio'
        verbose_name_plural = 'Negocios'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


    def get_absolute_url(self):
        """Return canonical URL for this client using the slug."""
        return reverse('client:detail', args=[self.slug])

    @staticmethod
    def _generate_code(length: int = 12) -> str:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @classmethod
    def _generate_unique_code(cls, length: int = 12) -> str:
        # Try a few times to avoid rare collisions; unique constraint is the final guard
        for _ in range(5):
            candidate = cls._generate_code(length)
            if not cls.objects.filter(code=candidate).exists():
                return candidate
        # Fallback: keep generating until unique (very unlikely to loop long)
        candidate = cls._generate_code(length)
        while cls.objects.filter(code=candidate).exists():
            candidate = cls._generate_code(length)
        return candidate

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_unique_code()
        super().save(*args, **kwargs)