from django.conf import settings
from django.db import models

from apps.service_requests.models import ServiceRequest


class Assignment(models.Model):
    service_request = models.OneToOneField(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name="assignment",
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments",
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_assignments",
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assignments"
        ordering = ["-assigned_at"]

    def __str__(self):
        return f"{self.service_request.request_number} → {self.assigned_to.email}"