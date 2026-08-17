from django.db import models
from donors.models import DonorProfile
from blood_requests.models import BloodRequest


class Notification(models.Model):

    RESPONSE_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Declined', 'Declined'),
        ('Completed', 'Completed'),
        ('Received', 'Received'),
    ]

    donor = models.ForeignKey(
        DonorProfile,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    blood_request = models.ForeignKey(
        BloodRequest,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    response = models.CharField(
        max_length=10,
        choices=RESPONSE_CHOICES,
        default='Pending'
    )

    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.donor} - {self.sent_at.strftime('%Y-%m-%d')}"