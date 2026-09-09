from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.categories.models import Category


class RequestPriority(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    URGENT = "URGENT", "Urgent"


class RequestStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    ASSIGNED = "ASSIGNED", "Assigned"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    RESOLVED = "RESOLVED", "Resolved"
    CLOSED = "CLOSED", "Closed"
    CANCELLED = "CANCELLED", "Cancelled"


class ServiceRequest(models.Model):
    """
    Core entity representing a customer service ticket.
    Manages complete request lifecycle, categorization, and ownership.
    """

    request_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        db_index=True,
        help_text="Format: SR-YYYY-NNNNNN",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="service_requests",
        help_text="Primary category classifying the request.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_requests",
    )

    priority = models.CharField(
        max_length=10,
        choices=RequestPriority.choices,
        default=RequestPriority.MEDIUM,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.OPEN,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "service_requests"
        ordering = ["-created_at"]
        verbose_name = "Service Request"
        verbose_name_plural = "Service Requests"

    def clean(self):
        super().clean()
        if not self.title or not self.title.strip():
            raise ValidationError({"title": "A descriptive title is required."})

    def save(self, *args, **kwargs):
        # Auto-generate request sequence number on initial creation
        if not self.request_number:
            year = timezone.now().year
            prefix = f"SR-{year}-"
            
            with transaction.atomic():
                last_record = (
                    ServiceRequest.objects
                    .select_for_update()
                    .filter(request_number__startswith=prefix)
                    .order_by("-id")
                    .first()
                )

                seq = 1
                if last_record and last_record.request_number:
                    try:
                        seq = int(last_record.request_number.split("-")[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1

                self.request_number = f"{prefix}{seq:06d}"

        super().save(*args, **kwargs)

    @property
    def is_closed(self) -> bool:
        return self.status in {RequestStatus.CLOSED, RequestStatus.CANCELLED}

    @property
    def is_resolved(self) -> bool:
        return self.status == RequestStatus.RESOLVED

    @property
    def is_active(self) -> bool:
        return self.status not in {RequestStatus.RESOLVED, RequestStatus.CLOSED, RequestStatus.CANCELLED}

    def can_transition_to(self, target_status: str) -> bool:
        """Enforces clean lifecycle progression rules."""
        if self.status == target_status:
            return True

        valid_transitions = {
            RequestStatus.OPEN: {RequestStatus.ASSIGNED, RequestStatus.IN_PROGRESS, RequestStatus.CANCELLED},
            RequestStatus.ASSIGNED: {RequestStatus.IN_PROGRESS, RequestStatus.RESOLVED, RequestStatus.CANCELLED, RequestStatus.OPEN},
            RequestStatus.IN_PROGRESS: {RequestStatus.RESOLVED, RequestStatus.ASSIGNED, RequestStatus.CANCELLED},
            RequestStatus.RESOLVED: {RequestStatus.CLOSED, RequestStatus.IN_PROGRESS},
            RequestStatus.CLOSED: {RequestStatus.OPEN},
            RequestStatus.CANCELLED: {RequestStatus.OPEN},
        }
        return target_status in valid_transitions.get(self.status, set())

    def mark_resolved(self, commit: bool = True):
        self.status = RequestStatus.RESOLVED
        self.resolved_at = timezone.now()
        if commit:
            self.save(update_fields=["status", "resolved_at", "updated_at"])

    def mark_closed(self, commit: bool = True):
        self.status = RequestStatus.CLOSED
        self.closed_at = timezone.now()
        if commit:
            self.save(update_fields=["status", "closed_at", "updated_at"])

    def __str__(self):
        return f"{self.request_number} — {self.title}"