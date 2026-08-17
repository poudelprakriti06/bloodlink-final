from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import DonorProfile
from .services import get_coordinates


@receiver(post_save, sender=DonorProfile)
def generate_donor_coordinates(sender, instance, created, **kwargs):

    if not created:
        return

    if not instance.latitude and not instance.longitude:

        coordinates = get_coordinates(
            district=instance.district,
            municipality=instance.municipality,
            ward=instance.ward,
            area=instance.area
        )

        if coordinates:
            instance.latitude = coordinates["latitude"]
            instance.longitude = coordinates["longitude"]
            instance.save(update_fields=["latitude", "longitude"])
