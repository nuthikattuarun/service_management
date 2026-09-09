from django.conf import settings
from django.db import models


class NotificationQuerySet(models.QuerySet):
    def unread(self):
        return self.filter(is_read=False)

    def mark_all_as_read(self):
        return self.filter(is_read=False).update(is_read=True)


class Notification(models.Model):
    """
    In-app alert delivered to users for ticket updates, reassignments, or comments.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="Recipient of the notification alert.",
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = NotificationQuerySet.as_manager()

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def mark_as_read(self, commit: bool = True):
        self.is_read = True
        if commit:
            self.save(update_fields=["is_read"])

    def __str__(self):
        status_label = "Read" if self.is_read else "Unread"
        return f"[{status_label}] {self.user.email}: {self.title}"