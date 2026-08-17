from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(
            donor__user=self.request.user
        ).order_by('-sent_at')


class NotificationDetailView(generics.RetrieveAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(donor__user=self.request.user)


class MarkNotificationReadView(APIView):

    def put(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            donor__user=request.user
        )
        notification.is_read = True
        notification.save()
        return Response(NotificationSerializer(notification).data)
