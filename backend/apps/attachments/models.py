from django.conf import settings
from django.db import models

from apps.service_requests.models import ServiceRequest


class Attachment(models.Model):
    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_attachments",
    )

    file = models.FileField(upload_to="service_requests/attachments/")
    original_name = models.CharField(max_length=255)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "attachments"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.original_name