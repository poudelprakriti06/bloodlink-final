from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Donation, DonorProfile


class DonationTrackingAndBadgeTest(TestCase):
    def test_first_timer_badge_is_awarded_for_first_delivered_donation(self):
        user = User.objects.create_user(
            username='donor1',
            email='donor1@example.com',
            password='StrongPass123!'
        )

        donor = DonorProfile.objects.create(
            user=user,
            phone='9800000001',
            blood_group='A+',
            gender='Male',
            date_of_birth='1995-05-10',
            district='Kathmandu',
            municipality='Kageshwori Manohara',
            ward=3,
            area='Nayabasti',
            is_available=True,
        )

        donation = Donation.objects.create(
            donor=donor,
            hospital_name='Grande International Hospital',
            donation_date=timezone.now().date(),
            batch_code='B-1001',
            status='delivered',
            destination_hospital='Grande International Hospital',
        )

        self.assertEqual(donation.status, 'delivered')
        self.assertTrue(donor.badges.filter(badge_key='first_timer').exists())
