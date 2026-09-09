from django.contrib import admin
from .models import Assignment


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("service_request", "assigned_to", "assigned_by", "assigned_at")
    list_filter = ("assigned_at",)
    search_fields = (
        "service_request__request_number",
        "service_request__title",
        "assigned_to__email",
        "assigned_by__email",
    )
    raw_id_fields = ("service_request", "assigned_to", "assigned_by")
    readonly_fields = ("assigned_at",)
