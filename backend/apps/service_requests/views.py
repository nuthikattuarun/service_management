from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.permissions import IsSupportStaff
from .models import RequestPriority, RequestStatus, ServiceRequest
from .serializers import ServiceRequestSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Service Requests"],
        summary="List service requests",
        description=(
            "List service requests. Customers will only see their own requests. "
            "Staff, Managers, and Admins can see and filter all requests."
        ),
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                enum=[s.value for s in RequestStatus],
                description="Filter by service request status",
            ),
            OpenApiParameter(
                name="priority",
                type=str,
                enum=[p.value for p in RequestPriority],
                description="Filter by priority level",
            ),
            OpenApiParameter(
                name="category",
                type=int,
                description="Filter by category ID",
            ),
            OpenApiParameter(
                name="created_by",
                type=int,
                description="Filter by creator user ID",
            ),
        ],
    ),
    create=extend_schema(
        tags=["Service Requests"],
        summary="Create a service request",
        description="Customers can create new service requests. Request number is generated automatically.",
    ),
    retrieve=extend_schema(
        tags=["Service Requests"],
        summary="Get service request details by ID",
    ),
    update=extend_schema(
        tags=["Service Requests"],
        summary="Update service request by ID",
    ),
    partial_update=extend_schema(
        tags=["Service Requests"],
        summary="Partially update service request by ID",
    ),
    destroy=extend_schema(
        tags=["Service Requests"],
        summary="Delete service request by ID",
    ),
)
class ServiceRequestViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing service requests.

    Customers:
        - Can create requests.
        - Can view only their own requests.

    Support Staff / Managers / Admins:
        - Can view and manage all requests.
        - Can filter, search, and order requests.
    """

    serializer_class = ServiceRequestSerializer

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "request_number",
        "title",
        "description",
        "category__name",
    ]

    ordering_fields = [
        "created_at",
        "updated_at",
        "priority",
        "status",
        "title",
    ]

    ordering = ["-created_at"]

    def get_permissions(self):
        """
        Customers can create service requests.
        Other actions require support staff, manager, or admin.
        """

        if self.action == "create":
            return [IsAuthenticated()]

        return [IsSupportStaff()]

    def get_queryset(self):
        """
        Return service requests based on the logged-in user's role.
        """

        user = self.request.user

        queryset = (
            ServiceRequest.objects
            .select_related(
                "category",
                "created_by",
            )
            .all()
        )

        # Customers can see only their own requests.
        if user.role == "CUSTOMER":
            queryset = queryset.filter(
                created_by=user
            )

        # Filter by status
        status_value = self.request.query_params.get("status")

        if status_value:
            queryset = queryset.filter(
                status=status_value
            )

        # Filter by priority
        priority = self.request.query_params.get("priority")

        if priority:
            queryset = queryset.filter(
                priority=priority
            )

        # Filter by category
        category = self.request.query_params.get("category")

        if category:
            queryset = queryset.filter(
                category_id=category
            )

        # Filter by created user
        created_by = self.request.query_params.get("created_by")

        if created_by:
            queryset = queryset.filter(
                created_by_id=created_by
            )

        return queryset

    def perform_create(self, serializer):
        """
        Automatically assign the logged-in user
        as the creator of the service request.
        """

        serializer.save(
            created_by=self.request.user
        )

    def update(self, request, *args, **kwargs):
        """
        Prevent changing created_by and request_number
        through the API.
        """

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=False
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def partial_update(self, request, *args, **kwargs):
        """
        Allow partial updates.
        """

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )