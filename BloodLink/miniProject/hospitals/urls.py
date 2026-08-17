from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.hospital_login_view, name='hospital_login'),
    path('dashboard/', views.hospital_dashboard_view, name='hospital_dashboard'),
]
