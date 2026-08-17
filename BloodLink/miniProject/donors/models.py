from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
from .services import get_coordinates
from blood_requests.models import BloodRequest


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

    donation_date = models.DateField()

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.donor} donated on {self.donation_date}"
