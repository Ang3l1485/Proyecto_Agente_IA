from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'name',
            'description',
        ]
        labels = {
            'name': 'Nombre del Negocio',
            'description': 'Descripción',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border rounded px-2 py-1'}),
            'description': forms.Textarea(attrs={'class': 'w-full border rounded px-2 py-1', 'rows': 4}),
        }
