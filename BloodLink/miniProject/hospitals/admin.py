from django.contrib import admin
from .models import HospitalProfile


@admin.register(HospitalProfile)
class HospitalProfileAdmin(admin.ModelAdmin):
    list_display = ('hospital_name', 'district', 'phone')
    list_filter = ('district',)
    search_fields = ('hospital_name', 'phone')
