from django.db import models
from django.contrib.auth.models import User


class HospitalProfile(models.Model):
    DISTRICT_CHOICES = [
        ('Kathmandu', 'Kathmandu'),
        ('Lalitpur', 'Lalitpur'),
        ('Bhaktapur', 'Bhaktapur'),
        ('Kaski', 'Kaski'),
        ('Chitwan', 'Chitwan'),
        ('Butwal', 'Butwal'),
        ('Biratnagar', 'Biratnagar'),
        ('Birgunj', 'Birgunj'),
        ('Dharan', 'Dharan'),
        ('Hetauda', 'Hetauda'),
        ('Other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='hospital_profile')
    hospital_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES)
    address = models.TextField()
    license_number = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.hospital_name
