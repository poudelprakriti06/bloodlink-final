from django.urls import path
from . import views


urlpatterns = [

    path('', views.BloodRequestListCreateView.as_view(), name='blood-request-list-create'),
    path('<int:pk>/', views.BloodRequestDetailView.as_view(), name='blood-request-detail'),
    path('<int:id>/accept/', views.AcceptBloodRequestView.as_view(), name='accept_blood_request'),
    path('<int:id>/decline/', views.DeclineBloodRequestView.as_view(), name='decline_blood_request'),
    path('<int:id>/complete-donation/', views.CompleteDonationView.as_view(), name='complete_donation'),
    path('<int:id>/confirm-received/', views.ConfirmBloodReceivedView.as_view(), name='confirm_blood_received'),
    path('<int:id>/cancel/', views.CancelBloodRequestView.as_view(), name='cancel_blood_request'),
    path('<int:id>/delete/', views.DeleteBloodRequestView.as_view(), name='delete_blood_request'),
    path('remove-donor/<int:id>/', views.RemoveDonorView.as_view(), name='remove_donor'),
]
