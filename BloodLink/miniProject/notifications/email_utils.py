from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_blood_request_email(donor, blood_request):

    subject = "Emergency Blood Request - BloodLink"

    message = render_to_string(
        "emails/blood_request_notification.txt",
        {
            "donor": donor,
            "blood_request": blood_request,
            "dashboard_url": "http://127.0.0.1:8000/dashboard/",
        },
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[donor.user.email],
    )

    try:
        email.send(fail_silently=False)
        print(f"✅ EMAIL SENT TO: {donor.user.email}")
    except Exception as e:
        print(f"❌ EMAIL FAILED FOR {donor.user.email}: {e}")