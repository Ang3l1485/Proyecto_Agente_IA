from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    birth_date = models.DateField(null=True, blank=True)
    
    # Fechas automáticas
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.get_full_name()