from django.db import models
from hospitals.models import HospitalProfile
from donors.services import get_coordinates







class BloodRequest(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    URGENCY_CHOICES = [
        ('Normal', 'Normal'),
        ('Urgent', 'Urgent'),
        ('Critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Fulfilled','Fulfilled')
    ]

    DISTRICT_CHOICES = ([
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
    ('Western Rukum', 'Western Rukum')])
    

    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name='blood_requests')
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    units_required = models.PositiveIntegerField()
    units_fulfilled = models.PositiveIntegerField(default=0)
    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES)
    contact_person = models.CharField(max_length=100)
    municipality = models.CharField(max_length=100,null=True,blank=True)
    ward = models.PositiveSmallIntegerField(null=True,blank=True)
    area = models.CharField(max_length=100,null=True,blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    contact_number = models.CharField(max_length=15)
    required_date = models.DateField()
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='Normal')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')

   

    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.blood_group} - {self.hospital} ({self.status})"

    @property
    def units_remaining(self):
        return self.units_required - self.units_fulfilled


    

    def save(self, *args, **kwargs):
        location_fields = ['district', 'municipality', 'ward', 'area']
        location_changed = False

        if self.pk:
            try:
                old = BloodRequest.objects.get(pk=self.pk)
                location_changed = any(
                    getattr(old, f) != getattr(self, f) for f in location_fields
                )
            except BloodRequest.DoesNotExist:
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
