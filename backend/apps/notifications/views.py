from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Notifications"],
        summary="List user notifications",
        description="Returns notification stream for the currently authenticated user.",
    ),
    retrieve=extend_schema(tags=["Notifications"], summary="Get notification by ID"),
    update=extend_schema(tags=["Notifications"], summary="Update notification read status"),
    partial_update=extend_schema(tags=["Notifications"], summary="Partially update notification"),
    destroy=extend_schema(tags=["Notifications"], summary="Delete notification"),
)
class NotificationViewSet(viewsets.ModelViewSet):
    """
    User notification hub.
    Allows users to read, acknowledge, or clear their alerts.
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Notifications are system-dispatched and cannot be posted directly via API."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        """Bulk acknowledges all unread notifications for the active user."""
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"detail": f"Acknowledged {updated} notifications.", "marked_count": updated})