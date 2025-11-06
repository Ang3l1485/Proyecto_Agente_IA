from django.urls import path
from . import views

app_name = 'business'

urlpatterns = [
    path('', views.BusinessListView.as_view(), name='list'),
    path('create/', views.BusinessCreateView.as_view(), name='create'),
    path('<slug:slug>/', views.BusinessDetailView.as_view(), name='detail'),
    path('<slug:slug>/delete/', views.BusinessDeleteView.as_view(), name='delete'),
]
