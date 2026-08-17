from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from .forms import RegisterForm
from .models import UserProfile

from donors.models import DonorProfile
from hospitals.models import HospitalProfile


def home(request):
    return render(request, 'home.html')


def redirect_user_dashboard(user):
    # Hospital user
    if hasattr(user, 'hospital_profile'):
        return redirect('hospital_dashboard')

    # Donor user
    if hasattr(user, 'donor_profile'):
        return redirect('dashboard')

    # User has no donor or hospital profile
    return redirect('home')


def register_view(request):
    if request.user.is_authenticated:
        return redirect_user_dashboard(request.user)

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            UserProfile.objects.create(user=user)

            DonorProfile.objects.create(
                user=user,
                blood_group=form.cleaned_data['blood_group'],
                district=form.cleaned_data['district'],
                municipality=form.cleaned_data['municipality'],
                ward=form.cleaned_data['ward'],
                area=form.cleaned_data['area'],
                phone=form.cleaned_data['phoneno'],
                gender=form.cleaned_data['gender'],
                date_of_birth=form.cleaned_data.get(
                    'date_of_birth'
                ) or '2000-01-01',
                is_available=True
            )

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            messages.success(
                request,
                f'Welcome, {user.first_name}! Your account was created successfully.'
            )

            return redirect_user_dashboard(user)

        else:
            messages.error(
                request,
                'Please fix the errors below.'
            )

    else:
        form = RegisterForm()

    return render(
        request,
        'register.html',
        {'form': form}
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect_user_dashboard(request.user)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            messages.success(
                request,
                f'Welcome back, {user.first_name}!'
            )

            return redirect_user_dashboard(user)

        else:
            messages.error(
                request,
                'Invalid username or password.'
            )

    return render(request, 'login.html')


def logout_view(request):
    logout(request)

    messages.success(
        request,
        'You have been logged out successfully'
    )

    return redirect('home')
