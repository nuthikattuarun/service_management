from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import ServiceRequest


class ServiceRequestSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "request_number",
            "title",
            "description",
            "category",
            "category_name",
            "created_by",
            "created_by_name",
            "priority",
            "status",
            "created_at",
            "updated_at",
            "resolved_at",
            "closed_at",
        ]
        read_only_fields = [
            "id",
            "request_number",
            "created_by",
            "created_by_name",
            "status",
            "created_at",
            "updated_at",
            "resolved_at",
            "closed_at",
        ]

    @extend_schema_field(serializers.CharField)
    def get_created_by_name(self, obj) -> str:
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.email
        return ""