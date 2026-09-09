from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.service_requests.models import ServiceRequest


class Comment(models.Model):
    """
    Message record within a ticket discussion thread.
    Chronologically tracks replies between customers and support staff.
    """

    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "comments"
        ordering = ["created_at"]
        verbose_name = "Ticket Comment"
        verbose_name_plural = "Ticket Comments"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        # Touch the parent ticket updated_at timestamp when a new comment is posted
        if is_new and self.service_request_id:
            ServiceRequest.objects.filter(pk=self.service_request_id).update(updated_at=timezone.now())

    def __str__(self):
        return f"Comment on {self.service_request.request_number} by {self.user.email}"