import os
from django.conf import settings
from django.db import models
from apps.service_requests.models import ServiceRequest


def attachment_upload_path(instance, filename: str) -> str:
    """Organizes ticket uploads cleanly into yearly/request subdirectories."""
    ticket_num = instance.service_request.request_number if instance.service_request_id else "misc"
    return f"attachments/{ticket_num}/{filename}"


class Attachment(models.Model):
    """
    Uploaded file evidence or documentation attached to a Service Request.
    """

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
    file = models.FileField(upload_to=attachment_upload_path)
    original_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "attachments"
        ordering = ["-uploaded_at"]
        verbose_name = "Ticket Attachment"
        verbose_name_plural = "Ticket Attachments"

    @property
    def extension(self) -> str:
        _, ext = os.path.splitext(self.original_name)
        return ext.lower().lstrip(".")

    @property
    def file_size_display(self) -> str:
        try:
            bytes_size = self.file.size
            if bytes_size < 1024:
                return f"{bytes_size} B"
            elif bytes_size < 1024 * 1024:
                return f"{bytes_size / 1024:.1f} KB"
            return f"{bytes_size / (1024 * 1024):.1f} MB"
        except Exception:
            return "N/A"

    def save(self, *args, **kwargs):
        if not self.original_name and self.file:
            self.original_name = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.original_name} ({self.service_request.request_number})"