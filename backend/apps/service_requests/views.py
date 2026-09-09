import logging
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.users.permissions import IsSupportStaff
from .models import RequestPriority, RequestStatus, ServiceRequest
from .serializers import ServiceRequestSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        tags=["Service Requests"],
        summary="List service requests",
        description="Fetch tickets. Customers see only their own requests; staff and managers view all tickets.",
        parameters=[
            OpenApiParameter(name="status", type=str, enum=[s.value for s in RequestStatus], description="Filter by status"),
            OpenApiParameter(name="priority", type=str, enum=[p.value for p in RequestPriority], description="Filter by priority"),
            OpenApiParameter(name="category", type=int, description="Filter by category ID"),
            OpenApiParameter(name="created_by", type=int, description="Filter by requester user ID"),
        ],
    ),
    create=extend_schema(
        tags=["Service Requests"],
        summary="Create a new service request",
        description="Customers submit new tickets. Ticket sequence number is automatically generated.",
    ),
    retrieve=extend_schema(tags=["Service Requests"], summary="Get service request details by ID"),
    update=extend_schema(tags=["Service Requests"], summary="Update service request"),
    partial_update=extend_schema(tags=["Service Requests"], summary="Partially update service request"),
    destroy=extend_schema(tags=["Service Requests"], summary="Delete service request"),
)
class ServiceRequestViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Service Requests.
    Enforces customer boundaries (can only see/create their own requests)
    while granting technicians and managers full operational visibility.
    """

    serializer_class = ServiceRequestSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["request_number", "title", "description", "category__name"]
    ordering_fields = ["created_at", "updated_at", "priority", "status", "title"]
    ordering = ["-created_at"]

    def get_permissions(self):
        # Any authenticated user can submit a ticket or view their own
        if self.action in {"create", "list", "retrieve"}:
            return [permissions.IsAuthenticated()]
        # Status changes, assignment, or deletion are restricted to staff
        return [IsSupportStaff()]

    def get_queryset(self):
        user = self.request.user
        qs = ServiceRequest.objects.select_related("category", "created_by").all()

        # Non-staff users are strictly limited to their own submitted tickets
        if not user.is_support_staff:
            qs = qs.filter(created_by=user)

        # Dynamic query param filters
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        priority_param = self.request.query_params.get("priority")
        if priority_param:
            qs = qs.filter(priority=priority_param)

        category_param = self.request.query_params.get("category")
        if category_param:
            qs = qs.filter(category_id=category_param)

        created_by_param = self.request.query_params.get("created_by")
        if created_by_param and user.is_support_staff:
            qs = qs.filter(created_by_id=created_by_param)

        return qs

    def perform_create(self, serializer):
        # Always bind creator to current authenticated session
        instance = serializer.save(created_by=self.request.user)
        logger.info("Service request created: %s by user %s", instance.request_number, self.request.user.email)

    def perform_update(self, serializer):
        instance = serializer.save()
        logger.info("Service request updated: %s [status=%s]", instance.request_number, instance.status)