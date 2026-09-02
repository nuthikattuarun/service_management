from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Notifications"],
        summary="List user notifications",
        description="Returns all notifications belonging to the logged-in user.",
    ),
    retrieve=extend_schema(tags=["Notifications"], summary="Get notification details by ID"),
    update=extend_schema(tags=["Notifications"], summary="Update notification (e.g. mark as read)"),
    partial_update=extend_schema(tags=["Notifications"], summary="Partially update notification (e.g. is_read)"),
    destroy=extend_schema(tags=["Notifications"], summary="Delete a notification"),
    create=extend_schema(
        tags=["Notifications"],
        summary="Create notification (Disabled for direct client creation)",
        responses={405: None},
    ),
)
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        )

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Notifications cannot be created through this endpoint."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)