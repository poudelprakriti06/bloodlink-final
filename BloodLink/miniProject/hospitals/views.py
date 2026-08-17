from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from blood_requests.models import BloodRequest
from notifications.models import Notification


def hospital_login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'hospital_profile'):
            return redirect('hospital_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and hasattr(user, 'hospital_profile'):
            login(request, user)
            messages.success(request, f'Welcome, {user.hospital_profile.hospital_name}!')
            return redirect('hospital_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not a hospital account.')

    return render(request, 'hospital_login.html')


@login_required
def hospital_dashboard_view(request):

    if not hasattr(request.user, 'hospital_profile'):
        return redirect('dashboard')
    hospital = request.user.hospital_profile

    blood_requests = BloodRequest.objects.filter(
        hospital=hospital
    ).order_by('-created_at')

    request_data = []
    for blood_request in blood_requests:
        notifications = Notification.objects.filter(
            blood_request=blood_request
        ).select_related('donor', 'donor__user')
        request_data.append({
            'blood_request': blood_request,
            'notifications': notifications,
        })

    total_count = blood_requests.count()
    active_count = blood_requests.filter(status__in=['Pending', 'Accepted']).count()
    fulfilled_count = blood_requests.filter(status='Fulfilled').count()

    return render(
        request,
        'hospital_dashboard.html',
        {
            'hospital': hospital,
            'request_data': request_data,
            'total_count': total_count,
            'active_count': active_count,
            'fulfilled_count': fulfilled_count,
        }
    )


hospital_dashboard = hospital_dashboard_view
