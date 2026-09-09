from django.contrib import admin
from .models import Attachment


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("original_name", "service_request", "uploaded_by", "file_size_display", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("original_name", "service_request__request_number", "uploaded_by__email")
    raw_id_fields = ("service_request", "uploaded_by")
    readonly_fields = ("uploaded_at",)
