from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "service_request",
            "user",
            "user_name",
            "message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "user_name",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(serializers.CharField)
    def get_user_name(self, obj) -> str:
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
        return ""