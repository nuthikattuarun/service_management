import logging
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from .models import Comment
from .serializers import CommentSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(tags=["Comments"], summary="List all comments"),
    create=extend_schema(tags=["Comments"], summary="Post a comment on a ticket"),
    retrieve=extend_schema(tags=["Comments"], summary="Get comment details by ID"),
    update=extend_schema(tags=["Comments"], summary="Update comment"),
    partial_update=extend_schema(tags=["Comments"], summary="Partially update comment"),
    destroy=extend_schema(tags=["Comments"], summary="Delete comment"),
)
class CommentViewSet(viewsets.ModelViewSet):
    """
    CRUD API for discussion threads.
    Customers are scoped to comments on their own tickets.
    """

    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Comment.objects.select_related("service_request", "user").all()

        if not user.is_support_staff:
            qs = qs.filter(service_request__created_by=user)

        request_id = self.request.query_params.get("service_request")
        if request_id:
            qs = qs.filter(service_request_id=request_id)

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        service_request = serializer.validated_data.get("service_request")

        # Ensure customer cannot comment on another user's ticket
        if not user.is_support_staff and service_request.created_by != user:
            raise PermissionDenied("You cannot comment on a service request that you did not create.")

        instance = serializer.save(user=user)
        logger.info("Comment posted on %s by %s", instance.service_request.request_number, user.email)