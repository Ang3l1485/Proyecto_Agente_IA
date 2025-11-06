# users/urls.py

from django.urls import path
from django.contrib.auth.views import LoginView
from . import views
from .forms import EmailAuthenticationForm

app_name = 'user'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', LoginView.as_view(
        template_name='user/login.html',
        authentication_form=EmailAuthenticationForm
    ), name='login'),
    path('logout/', views.logout_view, name='logout'),
]