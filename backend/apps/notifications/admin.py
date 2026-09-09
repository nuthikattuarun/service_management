from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("title", "message", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("created_at",)
    actions = ["mark_selected_as_read"]

    def mark_selected_as_read(self, request, queryset):
        count = queryset.update(is_read=True)
        self.message_user(request, f"Successfully marked {count} notifications as read.")
    mark_selected_as_read.short_description = "Mark selected notifications as read"
