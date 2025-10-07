# users/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        
        if form.is_valid():
            form.save()
            
            messages.success(request, '¡Tu cuenta ha sido creada exitosamente! Ya puedes iniciar sesión.')
            
            return redirect('users:login')
            
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'users/signup.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, '¡Has cerrado sesión exitosamente!')
    return redirect('users:login')