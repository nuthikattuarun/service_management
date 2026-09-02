from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Assignment
from .serializers import AssignmentSerializer


@extend_schema_view(
    list=extend_schema(tags=["Assignments"], summary="List all assignments"),
    create=extend_schema(
        tags=["Assignments"],
        summary="Assign a service request to a user",
        description="Creates an assignment linking a service request to staff/technician.",
    ),
    retrieve=extend_schema(tags=["Assignments"], summary="Get assignment details by ID"),
    update=extend_schema(tags=["Assignments"], summary="Update assignment by ID"),
    partial_update=extend_schema(tags=["Assignments"], summary="Partially update assignment by ID"),
    destroy=extend_schema(tags=["Assignments"], summary="Delete assignment by ID"),
)
class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.select_related(
        "service_request",
        "assigned_to",
        "assigned_by",
    )
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)