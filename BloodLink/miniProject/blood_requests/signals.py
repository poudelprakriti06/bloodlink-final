from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import BloodRequest
from donors.models import DonorProfile
from notifications.services import create_notification
from notifications.email_utils import send_blood_request_email
from donors.utils import calculate_distance


@receiver(post_save, sender=BloodRequest)
def notify_donors_on_blood_request(sender, instance, created, **kwargs):

    if not created:
        return

    # Try distance-based matching first
    if instance.latitude and instance.longitude:
        matching_donors = DonorProfile.objects.filter(
            blood_group=instance.blood_group,
            is_available=True,
            latitude__isnull=False,
            longitude__isnull=False
        )

        nearby_donors = []
        for donor in matching_donors:
            if donor.is_eligible():
                distance = calculate_distance(
                    instance.latitude, instance.longitude,
                    donor.latitude, donor.longitude
                )
                nearby_donors.append((distance, donor))

        nearby_donors.sort(key=lambda x: x[0])
        top_donors = [donor for _, donor in nearby_donors[:10]]

    else:
        # Fallback: same-district matching
        top_donors = list(
            DonorProfile.objects.filter(
                blood_group=instance.blood_group,
                is_available=True,
                district=instance.district
            ).filter(
                last_donation_date__isnull=True
            ) | DonorProfile.objects.filter(
                blood_group=instance.blood_group,
                is_available=True,
                district=instance.district
            ).exclude(
                last_donation_date__isnull=True
            )
        )
        top_donors = [d for d in top_donors if d.is_eligible()][:10]

    for donor in top_donors:
        message = (
            f"Emergency blood request for {instance.blood_group} blood "
            f"at {instance.hospital.hospital_name} in {instance.district}."
        )
        create_notification(donor=donor, blood_request=instance, message=message)
        send_blood_request_email(donor, instance)
