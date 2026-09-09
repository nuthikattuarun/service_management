from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "total_requests", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    ordering = ("name",)

    def total_requests(self, obj):
        return obj.service_requests.count()
    total_requests.short_description = "Total Requests"
