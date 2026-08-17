from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'donor',
        'blood_request',
        'is_read',
        'sent_at',
    )

    list_filter = (
        'is_read',
        'sent_at',
    )

    search_fields = (
        'donor__user__username',
        'message',
    )

    ordering = ('-sent_at',)