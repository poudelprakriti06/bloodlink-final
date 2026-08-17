from django.contrib import admin
from .models import BloodRequest


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "blood_group",
        "hospital",
        "units_required",
        "district",
        "urgency",
        "status",
        "required_date",
    )

    list_filter = ("status", "urgency", "district")

    search_fields = (
        "hospital__user__username",
        "blood_group",
        "contact_person",
    )