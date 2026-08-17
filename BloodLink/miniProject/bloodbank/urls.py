from django.urls import path
from . import views

app_name = 'bloodbank'  # Namespace to avoid conflicts with your existing app

urlpatterns = [
    path('', views.stock_list, name='stock_list'),
    path('add/', views.add_stock, name='add_stock'),
    path('request/', views.request_blood, name='request_blood'),
    path('requests/', views.request_list, name='request_list'),
    path('fulfill/<int:request_id>/', views.fulfill_pending_request, name='fulfill_request'),
    path('import/', views.import_legacy_to_new, name='import_legacy'),
]