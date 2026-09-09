from django.contrib import admin
from .models import ServiceRequest


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("request_number", "title", "category", "priority", "status", "created_by", "created_at")
    list_filter = ("status", "priority", "category", "created_at")
    search_fields = ("request_number", "title", "description", "created_by__email")
    readonly_fields = ("request_number", "created_at", "updated_at", "resolved_at", "closed_at")
    ordering = ("-created_at",)
