from django.urls import path
from . import views

urlpatterns = [
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path(
    'donation-history/',
    views.donation_history,
    name='donation_history'
)
]
