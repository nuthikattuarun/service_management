from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from apps.service_requests.models import RequestStatus, ServiceRequest


class Assignment(models.Model):
    """
    Represents the operational allocation of a Service Request to a specific support technician.
    Tracks both the assigned assignee and the delegating manager.
    """

    service_request = models.OneToOneField(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name="assignment",
        help_text="The ticket allocated to a technician.",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments",
        help_text="The technician responsible for resolving the ticket.",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_assignments",
        help_text="The manager or dispatcher who created this assignment.",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assignments"
        ordering = ["-assigned_at"]
        verbose_name = "Ticket Assignment"
        verbose_name_plural = "Ticket Assignments"

    def clean(self):
        super().clean()
        # Technicians cannot be customers
        if hasattr(self, "assigned_to") and self.assigned_to and not self.assigned_to.is_support_staff:
            raise ValidationError({"assigned_to": "Tickets can only be assigned to support staff or managers."})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Advance ticket status to ASSIGNED if currently OPEN
        if self.service_request.status == RequestStatus.OPEN:
            self.service_request.status = RequestStatus.ASSIGNED
            self.service_request.save(update_fields=["status", "updated_at"])

    def __str__(self):
        return f"{self.service_request.request_number} -> {self.assigned_to.email}"