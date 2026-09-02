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

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"