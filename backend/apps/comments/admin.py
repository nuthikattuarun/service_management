from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("service_request", "user", "message_preview", "created_at")
    list_filter = ("created_at",)
    search_fields = ("message", "user__email", "service_request__request_number")
    raw_id_fields = ("service_request", "user")
    readonly_fields = ("created_at", "updated_at")

    def message_preview(self, obj):
        return obj.message[:60] + "..." if len(obj.message) > 60 else obj.message
    message_preview.short_description = "Message Preview"
