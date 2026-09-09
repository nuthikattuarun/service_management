import logging
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from apps.users.permissions import IsSupportStaff
from .models import Assignment
from .serializers import AssignmentSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(tags=["Assignments"], summary="List all ticket assignments"),
    create=extend_schema(
        tags=["Assignments"],
        summary="Assign a service request to a technician",
        description="Creates an assignment linking an open service request to a support staff member.",
    ),
    retrieve=extend_schema(tags=["Assignments"], summary="Get assignment details by ID"),
    update=extend_schema(tags=["Assignments"], summary="Update technician assignment"),
    partial_update=extend_schema(tags=["Assignments"], summary="Partially update assignment"),
    destroy=extend_schema(tags=["Assignments"], summary="Unassign ticket"),
)
class AssignmentViewSet(viewsets.ModelViewSet):
    """
    Manages ticket dispatching and technician allocations.
    Restricted to support staff, managers, and administrators.
    """

    queryset = Assignment.objects.select_related("service_request", "assigned_to", "assigned_by")
    serializer_class = AssignmentSerializer
    permission_classes = [IsSupportStaff]

    def perform_create(self, serializer):
        # Automatically record current staff user as the assigner
        instance = serializer.save(assigned_by=self.request.user)
        logger.info(
            "Ticket %s assigned to %s by %s",
            instance.service_request.request_number,
            instance.assigned_to.email,
            self.request.user.email,
        )