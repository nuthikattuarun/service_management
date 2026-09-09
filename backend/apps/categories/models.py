from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    """
    Departmental or functional taxonomy category used to route and prioritize tickets.
    """

    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, help_text="Summary of request types belonging to this category.")
    is_active = models.BooleanField(default=True, help_text="Controls visibility in ticket creation forms.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "categories"
        ordering = ["name"]
        verbose_name = "Ticket Category"
        verbose_name_plural = "Ticket Categories"

    def clean(self):
        super().clean()
        if self.name:
            self.name = self.name.strip()

    @property
    def total_requests(self) -> int:
        return self.service_requests.count()

    def __str__(self):
        return self.name