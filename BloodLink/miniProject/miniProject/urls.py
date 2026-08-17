from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('accounts/', include('accounts.urls')),
    path('donors/', include('donors.urls')),
    path('hospitals/', include('hospitals.urls')),
    path('blood-requests/', include('blood_requests.urls')),
    path('notifications/', include('notifications.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('bloodbank/', include('bloodbank.urls')),
]



