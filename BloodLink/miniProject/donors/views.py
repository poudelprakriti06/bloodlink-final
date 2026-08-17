from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import DonorProfile, Donation
from django import forms


class DonorProfileForm(forms.ModelForm):

    class Meta:
        model = DonorProfile
        fields = [
            'phone',
            'blood_group',
            'gender',
            'date_of_birth',
            'district',
            'municipality',
            'ward',
            'area',
            'is_available',
            'profile_picture'
        ]

        widgets = {
            'date_of_birth': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }


@login_required
def edit_profile(request):

    profile = request.user.donor_profile

    if request.method == 'POST':

        form = DonorProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():
            form.save()
            return redirect('dashboard')

    else:

        form = DonorProfileForm(
            instance=profile
        )

    return render(
        request,
        'edit.html',
        {'form': form}
    )


@login_required
def donation_history(request):

    donor = request.user.donor_profile

    donations = Donation.objects.filter(
        donor=donor
    ).select_related(
        'blood_request',
        'blood_request__hospital'
    ).order_by(
        '-donation_date',
        '-created_at'
    )

    return render(
        request,
        'donation_history.html',
        {
            'donations': donations
        }
    )