from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Category
from .serializers import CategorySerializer


@extend_schema_view(
    list=extend_schema(tags=["Categories"], summary="List all categories"),
    create=extend_schema(tags=["Categories"], summary="Create a new category"),
    retrieve=extend_schema(tags=["Categories"], summary="Get category details by ID"),
    update=extend_schema(tags=["Categories"], summary="Update category by ID"),
    partial_update=extend_schema(tags=["Categories"], summary="Partially update category by ID"),
    destroy=extend_schema(tags=["Categories"], summary="Delete category by ID"),
)
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]