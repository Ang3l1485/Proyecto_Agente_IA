from django import forms

from .models import Business


class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
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
