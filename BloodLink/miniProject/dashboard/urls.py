from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path(
        'toggle-availability/',
        views.toggle_availability,
        name='toggle_availability'
    ),
]