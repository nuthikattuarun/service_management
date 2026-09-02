from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from .models import Attachment
from .serializers import AttachmentSerializer


@extend_schema_view(
    list=extend_schema(tags=["Attachments"], summary="List all attachments"),
    create=extend_schema(
        tags=["Attachments"],
        summary="Upload an attachment for a service request",
        description="Upload files such as screenshots, logs, or documents associated with a service request.",
    ),
    retrieve=extend_schema(tags=["Attachments"], summary="Get attachment details by ID"),
    update=extend_schema(tags=["Attachments"], summary="Update attachment by ID"),
    partial_update=extend_schema(tags=["Attachments"], summary="Partially update attachment by ID"),
    destroy=extend_schema(tags=["Attachments"], summary="Delete attachment by ID"),
)
class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.select_related(
        "service_request",
        "uploaded_by",
    )
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def perform_create(self, serializer):
        uploaded_file = self.request.FILES.get("file")

        serializer.save(
            uploaded_by=self.request.user,
            original_name=uploaded_file.name if uploaded_file else "",
        )