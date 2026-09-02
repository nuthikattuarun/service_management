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

    def get_assigned_to_name(self, obj):
        return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}"

    def get_assigned_by_name(self, obj):
        return f"{obj.assigned_by.first_name} {obj.assigned_by.last_name}"