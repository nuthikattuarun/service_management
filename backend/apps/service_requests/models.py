from django.conf import settings
from django.db import models
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
    request_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
    )

    title = models.CharField(max_length=200)
    description = models.TextField()

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="service_requests",
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
    )

    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.OPEN,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "service_requests"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.request_number:
            year = timezone.now().year
            last_request = (
                ServiceRequest.objects
                .filter(request_number__startswith=f"SR-{year}-")
                .order_by("-id")
                .first()
            )

            next_number = 1

            if last_request:
                try:
                    next_number = int(last_request.request_number.split("-")[-1]) + 1
                except (ValueError, IndexError):
                    next_number = 1

            self.request_number = f"SR-{year}-{next_number:06d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.request_number} - {self.title}"