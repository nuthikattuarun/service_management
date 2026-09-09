from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets

from apps.users.permissions import IsSupportStaff
from .models import Category
from .serializers import CategorySerializer


@extend_schema_view(
    list=extend_schema(tags=["Categories"], summary="List ticket categories"),
    create=extend_schema(tags=["Categories"], summary="Create a new category (Staff only)"),
    retrieve=extend_schema(tags=["Categories"], summary="Get category details by ID"),
    update=extend_schema(tags=["Categories"], summary="Update category"),
    partial_update=extend_schema(tags=["Categories"], summary="Partially update category"),
    destroy=extend_schema(tags=["Categories"], summary="Delete category"),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for Category taxonomy.
    Read-only for regular customers; writable by staff and admins.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [permissions.IsAuthenticated()]
        return [IsSupportStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        # Customers only need to view active categories
        if not self.request.user.is_support_staff:
            return qs.filter(is_active=True)
        return qs