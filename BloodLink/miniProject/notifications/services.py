from .models import Notification


def create_notification(donor, blood_request, message):

    notification = Notification.objects.create(
        donor=donor,
        blood_request=blood_request,
        message=message
    )

    return notification