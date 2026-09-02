from rest_framework import serializers

from .models import Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = [
            "id",
            "service_request",
            "uploaded_by",
            "file",
            "original_name",
            "uploaded_at",
        ]
        read_only_fields = [
            "id",
            "uploaded_by",
            "original_name",
            "uploaded_at",
        ]