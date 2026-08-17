from django.contrib import admin
from .models import DonorProfile, Donation


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'blood_group', 'district', 'phone', 'is_available')
    list_filter = ('blood_group', 'district', 'is_available')
    search_fields = ('user__username', 'user__email', 'phone')


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor', 'hospital_name', 'donation_date')
    list_filter = ('donation_date',)
    search_fields = ('donor__user__username', 'hospital_name')
