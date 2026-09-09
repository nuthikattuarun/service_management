import logging
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser

from .models import Attachment
from .serializers import AttachmentSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(tags=["Attachments"], summary="List all attachments"),
    create=extend_schema(
        tags=["Attachments"],
        summary="Upload attachment for a service request",
        description="Upload logs, screenshots, or PDF documents associated with a ticket.",
    ),
    retrieve=extend_schema(tags=["Attachments"], summary="Get attachment details by ID"),
    update=extend_schema(tags=["Attachments"], summary="Update attachment"),
    partial_update=extend_schema(tags=["Attachments"], summary="Partially update attachment"),
    destroy=extend_schema(tags=["Attachments"], summary="Delete attachment"),
)
class AttachmentViewSet(viewsets.ModelViewSet):
    """
    Handles multi-part binary file uploads linked to service requests.
    Validates ownership and access permissions against the parent ticket.
    """

    queryset = Attachment.objects.select_related("service_request", "uploaded_by")
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if not user.is_support_staff:
            qs = qs.filter(service_request__created_by=user)

        request_id = self.request.query_params.get("service_request")
        if request_id:
            qs = qs.filter(service_request_id=request_id)

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        service_request = serializer.validated_data.get("service_request")

        if not user.is_support_staff and service_request.created_by != user:
            raise PermissionDenied("You cannot upload files to another user's service request.")

        uploaded_file = self.request.FILES.get("file")
        filename = uploaded_file.name if uploaded_file else ""

        instance = serializer.save(uploaded_by=user, original_name=filename)
        logger.info("File uploaded: '%s' for request %s", filename, instance.service_request.request_number)