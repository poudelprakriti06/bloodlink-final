from django.db import models

# Create your models here.
from django.db import models

# --- Constants ---
BLOOD_GROUPS = [
    ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
]
REQUEST_STATUS = [
    ('fulfilled', 'Fulfilled'),
    ('pending', 'Pending'),
    ('cancelled', 'Cancelled'),
]

# --- YOUR NEW SYSTEM MODELS (Managed by Django) ---
class BloodStock(models.Model):
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS, unique=True)
    quantity = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.blood_group} - {self.quantity} units"

    class Meta:
        ordering = ['blood_group']


class BloodRequest(models.Model):
    requester_name = models.CharField(max_length=100)
    hospital_name = models.CharField(max_length=100)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS)
    quantity_needed = models.PositiveIntegerField()
    required_by_date = models.DateField()
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    fulfilled_from = models.ForeignKey(BloodStock, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.hospital_name} - {self.blood_group}"


# --- LEGACY SYSTEM MAPPING (Unmanaged / Read-Only) ---
# IMPORTANT: Change 'old_blood_table' to the EXACT table name in your legacy DB.
class LegacyBloodStock(models.Model):
    # Adjust these fields based on your legacy schema.
    # Run `python manage.py inspectdb --database=legacy` to see the exact columns.
    blood_type = models.CharField(max_length=3, db_column='blood_group')  
    total_units = models.IntegerField(db_column='quantity')              
    expiry = models.DateField(db_column='expiry_date')                  

    class Meta:
        managed = False                      
        db_table = 'old_blood_table'         # <--- CHANGE THIS TO YOUR LEGACY TABLE NAME
        ordering = ['blood_type']

    def __str__(self):
        return f"[Legacy] {self.blood_type} - {self.total_units}"