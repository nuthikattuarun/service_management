from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Comment
from .serializers import CommentSerializer


@extend_schema_view(
    list=extend_schema(tags=["Comments"], summary="List all comments"),
    create=extend_schema(tags=["Comments"], summary="Post a comment on a service request"),
    retrieve=extend_schema(tags=["Comments"], summary="Get comment details by ID"),
    update=extend_schema(tags=["Comments"], summary="Update comment by ID"),
    partial_update=extend_schema(tags=["Comments"], summary="Partially update comment by ID"),
    destroy=extend_schema(tags=["Comments"], summary="Delete comment by ID"),
)
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related(
        "service_request",
        "user",
    )
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)