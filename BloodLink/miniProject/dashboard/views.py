from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from notifications.models import Notification
from donors.models import Donation


BADGE_CATALOG = [
    {
        'key': 'first_timer',
        'name': 'First Timer',
        'description': 'Completed your first blood donation.',
        'icon': '🎉',
    },
    {
        'key': 'gallon_grad',
        'name': 'Gallon Grad',
        'description': 'Reached 8 pints / 1 gallon donated.',
        'icon': '🏆',
    },
    {
        'key': 'decade_donor',
        'name': 'Decade Donor',
        'description': 'Donated for 10+ years of support.',
        'icon': '🏅',
    },
]


@login_required
def dashboard(request):
    if hasattr(request.user, 'hospital_profile'):
        return redirect('hospital_dashboard')

    donor = request.user.donor_profile

    # Sync last_donation_date from actual Donation records
    latest_donation = Donation.objects.filter(donor=donor).order_by('-donation_date').first()
    if latest_donation and latest_donation.donation_date != donor.last_donation_date:
        donor.last_donation_date = latest_donation.donation_date
        donor.save(update_fields=['last_donation_date'])

    notifications = Notification.objects.filter(
        donor=donor
    ).select_related(
        'blood_request',
        'blood_request__hospital'
    ).order_by('-sent_at')

    completed_donations = set(
        Donation.objects.filter(
            donor=donor
        ).values_list(
            'blood_request_id',
            flat=True
        )
    )

    # Dashboard statistics
    total_notifications = notifications.count()
    unread_notifications = notifications.filter(is_read=False).count()

    accepted_requests = notifications.filter(
        response='Accepted'
    ).count()

    completed_requests = notifications.filter(
        response='Completed'
    ).count()

    received_requests = notifications.filter(
        response='Received'
    ).count()

    pending_requests = notifications.filter(
        response='Pending'
    ).count()

    declined_requests = notifications.filter(
        response='Declined'
    ).count()

    total_donations = Donation.objects.filter(
        donor=donor
    ).count()

    active_requests = notifications.exclude(
        response__in=['Declined', 'Received']
    ).count()

    donations = Donation.objects.filter(donor=donor).select_related('blood_request').order_by('-donation_date', '-created_at')
    earned_badges = set(donor.badges.values_list('badge_key', flat=True))
    badge_cards = []
    for badge in BADGE_CATALOG:
        badge_cards.append({
            **badge,
            'earned': badge['key'] in earned_badges,
        })

    return render(
        request,
        'dashboard.html',
        {
            'notifications': notifications,
            'completed_donations': completed_donations,
            # Dashboard statistics
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'accepted_requests': accepted_requests,
            'completed_requests': completed_requests,
            'received_requests': received_requests,
            'pending_requests': pending_requests,
            'declined_requests': declined_requests,
            'total_donations': total_donations,
            'active_requests': active_requests,
            'donations': donations,
            'badge_cards': badge_cards,
            'earned_badges': donor.badges.all(),

            # Donor information
            'donor': donor,
            'is_eligible': donor.is_eligible(),
            'days_until_eligible': donor.days_until_eligible(),
        }
    )


@login_required
def toggle_availability(request):
    if not hasattr(request.user, 'donor_profile'):
        return redirect('dashboard')

    if request.method == 'POST':
        donor = request.user.donor_profile
        donor.is_available = not donor.is_available
        donor.save()

    return redirect('dashboard')