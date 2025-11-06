# user/forms.py

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.forms import AuthenticationForm

# Obtenemos tu modelo de usuario personalizado
User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        # Especificamos los campos que queremos en el formulario.
        # Si usas login con email, los campos serían:
        fields = ('email', 'first_name', 'last_name', 'birth_date')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_classes = 'w-full rounded-full py-3 px-4 text-gray-900 bg-white border-gray-300 focus:border-blue-500 focus:ring-blue-500'
        # Apply the same classes and placeholders to each field
        if 'email' in self.fields:
            self.fields['email'].widget.attrs.update({
                'class': base_classes,
                'placeholder': 'you@example.com',
                'type': 'email'
            })
        for name in ('first_name', 'last_name'):
            if name in self.fields:
                self.fields[name].widget.attrs.update({
                    'class': base_classes,
                    'placeholder': self.fields[name].label
                })
        if 'birth_date' in self.fields:
            self.fields['birth_date'].widget.attrs.update({
                'class': base_classes,
                'placeholder': 'YYYY-MM-DD',
                'type': 'date'
            })
        # Actualizar los campos de contraseña
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({
                'class': base_classes,
                'placeholder': 'Contraseña'
            })
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'class': base_classes,
                'placeholder': 'Confirmar contraseña'
            })

class EmailAuthenticationForm(AuthenticationForm):
    """Authentication form that uses the email field as the username."""
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'class': '[&]:text-gray-900 w-full rounded-lg py-3 px-5 text-sm bg-white placeholder-blue-400 border border-blue-100 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 transition-all',
            'placeholder': 'tu@email.com',
            'style': 'color: #1a365d !important;'  # Forzar color azul oscuro
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget.attrs.update({
            'class': '[&]:text-gray-900 w-full rounded-lg py-3 px-5 text-sm bg-white placeholder-blue-400 border border-blue-100 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 transition-all',
            'placeholder': 'Tu contraseña',
            'style': 'color: #1a365d !important;'  # Forzar color azul oscuro
        })

    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full rounded-full py-3 px-4 text-sm',
            'placeholder': 'Your password'
        })
    )