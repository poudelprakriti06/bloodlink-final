from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
import uuid
from .services import get_coordinates
from blood_requests.models import BloodRequest


class DonorBadge(models.Model):
    donor = models.ForeignKey(
        'DonorProfile',
        on_delete=models.CASCADE,
        related_name='badges'
    )
    badge_key = models.CharField(max_length=50)
    badge_name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    claimed = models.BooleanField(default=True)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('donor', 'badge_key')

    def __str__(self):
        return f"{self.badge_name} for {self.donor}"


class DonorProfile(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    DISTRICT_CHOICES = [
          ('Achham', 'Achham'),
    ('Arghakhanchi', 'Arghakhanchi'),
    ('Baglung', 'Baglung'),
    ('Baitadi', 'Baitadi'),
    ('Bajhang', 'Bajhang'),
    ('Bajura', 'Bajura'),
    ('Banke', 'Banke'),
    ('Bara', 'Bara'),
    ('Bardiya', 'Bardiya'),
    ('Bhaktapur', 'Bhaktapur'),
    ('Bhojpur', 'Bhojpur'),
    ('Chitwan', 'Chitwan'),
    ('Dadeldhura', 'Dadeldhura'),
    ('Dailekh', 'Dailekh'),
    ('Dang', 'Dang'),
    ('Darchula', 'Darchula'),
    ('Dhading', 'Dhading'),
    ('Dhankuta', 'Dhankuta'),
    ('Dhanusha', 'Dhanusha'),
    ('Dolakha', 'Dolakha'),
    ('Dolpa', 'Dolpa'),
    ('Doti', 'Doti'),
    ('Eastern Rukum', 'Eastern Rukum'),
    ('Gorkha', 'Gorkha'),
    ('Gulmi', 'Gulmi'),
    ('Humla', 'Humla'),
    ('Ilam', 'Ilam'),
    ('Jajarkot', 'Jajarkot'),
    ('Jhapa', 'Jhapa'),
    ('Jumla', 'Jumla'),
    ('Kailali', 'Kailali'),
    ('Kalikot', 'Kalikot'),
    ('Kanchanpur', 'Kanchanpur'),
    ('Kapilvastu', 'Kapilvastu'),
    ('Kaski', 'Kaski'),
    ('Kathmandu', 'Kathmandu'),
    ('Kavrepalanchok', 'Kavrepalanchok'),
    ('Khotang', 'Khotang'),
    ('Lalitpur', 'Lalitpur'),
    ('Lamjung', 'Lamjung'),
    ('Mahottari', 'Mahottari'),
    ('Makwanpur', 'Makwanpur'),
    ('Manang', 'Manang'),
    ('Morang', 'Morang'),
    ('Mugu', 'Mugu'),
    ('Mustang', 'Mustang'),
    ('Myagdi', 'Myagdi'),
    ('Nawalpur', 'Nawalpur'),
    ('Nuwakot', 'Nuwakot'),
    ('Okhaldhunga', 'Okhaldhunga'),
    ('Palpa', 'Palpa'),
    ('Panchthar', 'Panchthar'),
    ('Parbat', 'Parbat'),
    ('Parsa', 'Parsa'),
    ('Pyuthan', 'Pyuthan'),
    ('Ramechhap', 'Ramechhap'),
    ('Rasuwa', 'Rasuwa'),
    ('Rautahat', 'Rautahat'),
    ('Rolpa', 'Rolpa'),
    ('Rupandehi', 'Rupandehi'),
    ('Salyan', 'Salyan'),
    ('Sankhuwasabha', 'Sankhuwasabha'),
    ('Saptari', 'Saptari'),
    ('Sarlahi', 'Sarlahi'),
    ('Sindhuli', 'Sindhuli'),
    ('Sindhupalchok', 'Sindhupalchok'),
    ('Siraha', 'Siraha'),
    ('Solukhumbu', 'Solukhumbu'),
    ('Sunsari', 'Sunsari'),
    ('Surkhet', 'Surkhet'),
    ('Syangja', 'Syangja'),
    ('Tanahun', 'Tanahun'),
    ('Taplejung', 'Taplejung'),
    ('Terhathum', 'Terhathum'),
    ('Udayapur', 'Udayapur'),
    ('Western Rukum', 'Western Rukum'),
       
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='donor_profile')
    phone = models.CharField(max_length=15)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES)
    municipality = models.CharField(max_length=100,null=True,blank=True)
    ward = models.PositiveSmallIntegerField(null=True,blank=True)
    area = models.CharField(max_length=100,null=True,blank=True)
    last_donation_date = models.DateField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    profile_picture = models.ImageField(upload_to='donor_pics/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.blood_group}"

    def is_eligible(self):
        if not self.last_donation_date:
            return True
        days_since = (timezone.now().date() - self.last_donation_date).days
        return days_since >= 90

    def days_until_eligible(self):
        if not self.last_donation_date:
            return 0
        days_since = (timezone.now().date() - self.last_donation_date).days
        return max(0, 90 - days_since)

    @property
    def total_donations(self):
        return self.donations.count()

    def award_badges(self):
        donation_count = self.total_donations
        badge_definitions = [
            (
                'first_timer',
                'First Timer',
                'Completed your first blood donation.',
                donation_count >= 1,
            ),
            (
                'gallon_grad',
                'Gallon Grad',
                'Reached 8 pints / 1 gallon donated.',
                donation_count >= 8,
            ),
            (
                'decade_donor',
                'Decade Donor',
                'Donated for 10+ years of ongoing support.',
                False,
            ),
        ]

        for badge_key, badge_name, description, is_unlocked in badge_definitions:
            if not is_unlocked:
                continue
            if not self.badges.filter(badge_key=badge_key).exists():
                DonorBadge.objects.create(
                    donor=self,
                    badge_key=badge_key,
                    badge_name=badge_name,
                    description=description,
                    claimed=True,
                )

    def save(self, *args, **kwargs):
        location_fields = ['district', 'municipality', 'ward', 'area']
        location_changed = False

        if self.pk:
            try:
                old = DonorProfile.objects.get(pk=self.pk)
                location_changed = any(
                    getattr(old, f) != getattr(self, f) for f in location_fields
                )
            except DonorProfile.DoesNotExist:
                location_changed = True
        else:
            location_changed = True

        if location_changed and self.district and self.municipality and self.ward and self.area:
            coordinates = get_coordinates(
                district=self.district,
                municipality=self.municipality,
                ward=self.ward,
                area=self.area
            )
            if coordinates:
                self.latitude = coordinates["latitude"]
                self.longitude = coordinates["longitude"]

        super().save(*args, **kwargs)

class Donation(models.Model):
    STATUS_CHOICES = [
        ('collected', 'Collected'),
        ('processing', 'Processing'),
        ('testing', 'Testing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]

    donor = models.ForeignKey(
        DonorProfile,
        on_delete=models.CASCADE,
        related_name='donations'
    )

    blood_request = models.ForeignKey(
        BloodRequest,
        on_delete=models.CASCADE,
        related_name='donations',
        null=True,
        blank=True
    )

    hospital_name = models.CharField(max_length=200)
    destination_hospital = models.CharField(max_length=200, blank=True, null=True)
    donation_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='collected')
    batch_code = models.CharField(max_length=80, unique=True, blank=True, null=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def journey_steps(self):
        steps = [
            {'key': 'collected', 'label': 'Donation', 'done': False},
            {'key': 'processing', 'label': 'Processing', 'done': False},
            {'key': 'testing', 'label': 'Testing', 'done': False},
            {'key': 'shipped', 'label': 'Distribution', 'done': False},
            {'key': 'delivered', 'label': 'Delivered', 'done': False},
        ]
        status_order = [step['key'] for step in steps]
        current_index = status_order.index(self.status) if self.status in status_order else -1

        for index, step in enumerate(steps):
            if index <= current_index:
                step['done'] = True

        return steps

    @property
    def progress_percentage(self):
        steps = self.journey_steps
        current = next((index for index, step in enumerate(steps) if step['key'] == self.status), 0)
        return int(((current + 1) / len(steps)) * 100)

    def __str__(self):
        return f"{self.donor} donated on {self.donation_date} [{self.status}]"

    def save(self, *args, **kwargs):
        if not self.batch_code:
            self.batch_code = f"BL-{uuid.uuid4().hex[:10].upper()}"

        super().save(*args, **kwargs)

        if self.status == 'delivered':
            self.donor.award_badges()
