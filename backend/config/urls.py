from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .views import (
    assignment_create,
    assignments_list,
    attachment_create,
    attachments_list,
    categories_list,
    category_create,
    comment_create,
    comments_list,
    dashboard,
    notification_mark_read,
    notifications_list,
    notifications_mark_all_read,
    request_add_attachment,
    request_add_comment,
    request_create,
    request_detail,
    request_update_status,
    requests_list,
    ui_login,
    ui_logout,
    ui_register,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # ==================== OpenAPI / Swagger API Docs ====================
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # ==================== REST API Endpoints ====================
    path("api/auth/", include("apps.authentication.urls")),
    path("api/", include("apps.categories.urls")),
    path("api/", include("apps.service_requests.urls")),
    path("api/", include("apps.assignments.urls")),
    path("api/", include("apps.comments.urls")),
    path("api/", include("apps.attachments.urls")),
    path("api/", include("apps.notifications.urls")),

    # ==================== Backend Django Template UI ====================
    # Dashboard
    path("", dashboard, name="dashboard"),

    # Auth UI
    path("ui/login/", ui_login, name="ui_login"),
    path("ui/register/", ui_register, name="ui_register"),
    path("ui/logout/", ui_logout, name="ui_logout"),

    # Requests UI
    path("ui/requests/", requests_list, name="requests_list"),
    path("ui/requests/create/", request_create, name="request_create"),
    path("ui/requests/<int:pk>/", request_detail, name="request_detail"),
    path("ui/requests/<int:pk>/status/", request_update_status, name="request_update_status"),
    path("ui/requests/<int:pk>/comment/", request_add_comment, name="request_add_comment"),
    path("ui/requests/<int:pk>/attachment/", request_add_attachment, name="request_add_attachment"),

    # Assignments UI
    path("ui/assignments/", assignments_list, name="assignments_list"),
    path("ui/assignments/create/", assignment_create, name="assignment_create"),

    # Attachments UI
    path("ui/attachments/", attachments_list, name="attachments_list"),
    path("ui/attachments/create/", attachment_create, name="attachment_create"),

    # Comments UI
    path("ui/comments/", comments_list, name="comments_list"),
    path("ui/comments/create/", comment_create, name="comment_create"),

    # Notifications UI
    path("ui/notifications/", notifications_list, name="notifications_list"),
    path("ui/notifications/<int:pk>/read/", notification_mark_read, name="notification_mark_read"),
    path("ui/notifications/read-all/", notifications_mark_all_read, name="notifications_mark_all_read"),

    # Categories UI
    path("ui/categories/", categories_list, name="categories_list"),
    path("ui/categories/create/", category_create, name="category_create"),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT,
)