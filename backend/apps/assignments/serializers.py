from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Assignment


class AssignmentSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()
    assigned_by_name = serializers.SerializerMethodField()
    request_number = serializers.CharField(
        source="service_request.request_number",
        read_only=True,
    )

    class Meta:
        model = Assignment
        fields = [
            "id",
            "service_request",
            "request_number",
            "assigned_to",
            "assigned_to_name",
            "assigned_by",
            "assigned_by_name",
            "assigned_at",
        ]
        read_only_fields = [
            "id",
            "assigned_by",
            "assigned_by_name",
            "assigned_at",
            "request_number",
        ]

    @extend_schema_field(serializers.CharField)
    def get_assigned_to_name(self, obj) -> str:
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip() or obj.assigned_to.email
        return ""

    @extend_schema_field(serializers.CharField)
    def get_assigned_by_name(self, obj) -> str:
        if obj.assigned_by:
            return f"{obj.assigned_by.first_name} {obj.assigned_by.last_name}".strip() or obj.assigned_by.email
        return ""