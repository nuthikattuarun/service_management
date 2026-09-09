import csv
import logging
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.assignments.models import Assignment
from apps.attachments.models import Attachment
from apps.categories.models import Category
from apps.comments.models import Comment
from apps.notifications.models import Notification
from apps.service_requests.models import RequestPriority, RequestStatus, ServiceRequest
from apps.users.models import User, UserRole

logger = logging.getLogger(__name__)

CACHE_TTL_SHORT = 30
CACHE_TTL_MEDIUM = 60


# ==============================================================================
# CACHE & CONTEXT UTILITIES
# ==============================================================================

def invalidate_user_notification_cache(user_id: int):
    """Evicts cached unread badge count when notifications change."""
    cache.delete(f"unread_notifications_count_{user_id}")


def get_cached_active_categories():
    """Returns active categories from cache, falling back to database."""
    categories = cache.get("active_categories_list")
    if categories is None:
        categories = list(Category.objects.filter(is_active=True).only("id", "name"))
        cache.set("active_categories_list", categories, timeout=CACHE_TTL_MEDIUM)
    return categories


def get_cached_staff_users():
    """Returns list of assignable support personnel from cache."""
    staff = cache.get("staff_users_list")
    if staff is None:
        staff = list(
            User.objects.filter(
                role__in=[UserRole.SUPPORT_STAFF, UserRole.MANAGER, UserRole.ADMIN],
                is_active=True,
            ).only("id", "first_name", "last_name", "email", "role")
        )
        cache.set("staff_users_list", staff, timeout=CACHE_TTL_MEDIUM)
    return staff


def get_common_context(request, active_tab: str = "dashboard") -> dict:
    """Provides common context variables across all template views."""
    unread_count = 0
    if request.user.is_authenticated:
        cache_key = f"unread_notifications_count_{request.user.id}"
        unread_count = cache.get(cache_key)
        if unread_count is None:
            unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
            cache.set(cache_key, unread_count, timeout=CACHE_TTL_SHORT)

    return {
        "active_tab": active_tab,
        "unread_notifications_count": unread_count,
    }


# ==============================================================================
# AUTHENTICATION PORTAL
# ==============================================================================

def ui_login(request):
    """Handles web login for customers and staff."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not email or not password:
            messages.error(request, "Please enter both your email address and password.")
            return render(request, "login.html")

        user = authenticate(request, username=email, password=password)
        if user is None:
            # Fallback password check
            try:
                candidate = User.objects.get(email=email)
                if candidate.check_password(password):
                    user = candidate
            except User.DoesNotExist:
                user = None

        if user is not None:
            if not user.is_active:
                messages.error(request, "Your account has been deactivated. Please contact support.")
                return render(request, "login.html")

            login(request, user)
            logger.info("User %s logged into Web UI", user.email)
            messages.success(request, f"Welcome back, {user.first_name}!")
            next_target = request.GET.get("next") or "dashboard"
            return redirect(next_target)

        messages.error(request, "Invalid email or password.")

    return render(request, "login.html")


def ui_register(request):
    """Customer self-registration portal."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        phone = request.POST.get("phone", "").strip()

        if not all([email, password, first_name, last_name]):
            messages.error(request, "Please fill in all required registration fields.")
            return render(request, "register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email address already exists.")
            return render(request, "register.html")

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=UserRole.CUSTOMER,
        )
        login(request, user)
        logger.info("New web registration completed: %s", user.email)
        messages.success(request, "Your account has been created. Welcome to ServiceDesk!")
        return redirect("dashboard")

    return render(request, "register.html")


def ui_logout(request):
    """Logs out current user session."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("ui_login")


# ==============================================================================
# DASHBOARD & ANALYTICS
# ==============================================================================

@login_required
def dashboard(request):
    """Executive metrics and operational dashboard."""
    user = request.user
    base_qs = ServiceRequest.objects.filter(created_by=user) if user.is_customer else ServiceRequest.objects.all()

    stats = base_qs.aggregate(
        total=Count("id"),
        open_count=Count("id", filter=Q(status=RequestStatus.OPEN)),
        assigned_count=Count("id", filter=Q(status=RequestStatus.ASSIGNED)),
        in_progress_count=Count("id", filter=Q(status=RequestStatus.IN_PROGRESS)),
        resolved_count=Count("id", filter=Q(status=RequestStatus.RESOLVED)),
        closed_count=Count("id", filter=Q(status=RequestStatus.CLOSED)),
        cancelled_count=Count("id", filter=Q(status=RequestStatus.CANCELLED)),
        p_low=Count("id", filter=Q(priority=RequestPriority.LOW)),
        p_med=Count("id", filter=Q(priority=RequestPriority.MEDIUM)),
        p_high=Count("id", filter=Q(priority=RequestPriority.HIGH)),
        p_urg=Count("id", filter=Q(priority=RequestPriority.URGENT)),
    )

    total = stats["total"] or 0
    resolved_total = (stats["resolved_count"] or 0) + (stats["closed_count"] or 0)
    active_workload = (stats["assigned_count"] or 0) + (stats["in_progress_count"] or 0)
    resolution_rate = round((resolved_total / total * 100), 1) if total > 0 else 0

    recent_requests = (
        base_qs.select_related("category", "created_by")
        .only("id", "request_number", "title", "priority", "status", "created_at", "category_id", "created_by_id")
        .order_by("-created_at")[:8]
    )

    recent_notifications = (
        Notification.objects.filter(user=user)
        .only("id", "title", "message", "is_read", "created_at")
        .order_by("-created_at")[:5]
    )

    categories_chart = list(
        Category.objects.filter(is_active=True)
        .annotate(ticket_count=Count("service_requests"))
        .values("name", "ticket_count")
    )

    context = {
        **get_common_context(request, active_tab="dashboard"),
        "total_requests": total,
        "open_requests": stats["open_count"] or 0,
        "assigned_requests": stats["assigned_count"] or 0,
        "in_progress_requests": stats["in_progress_count"] or 0,
        "resolved_requests": stats["resolved_count"] or 0,
        "closed_requests": stats["closed_count"] or 0,
        "cancelled_requests": stats["cancelled_count"] or 0,
        "active_workload": active_workload,
        "resolved_total": resolved_total,
        "resolution_rate": resolution_rate,
        "p_low": stats["p_low"] or 0,
        "p_med": stats["p_med"] or 0,
        "p_high": stats["p_high"] or 0,
        "p_urg": stats["p_urg"] or 0,
        "recent_requests": recent_requests,
        "recent_notifications": recent_notifications,
        "categories_chart": categories_chart,
    }
    return render(request, "dashboard.html", context)


# ==============================================================================
# SERVICE REQUESTS VIEWS
# ==============================================================================

@login_required
def requests_export_csv(request):
    """Exports filtered service request dataset as a CSV spreadsheet."""
    user = request.user
    qs = ServiceRequest.objects.filter(created_by=user) if user.is_customer else ServiceRequest.objects.all()

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="service_requests_export.csv"'

    writer = csv.writer(response)
    writer.writerow(["Ticket #", "Title", "Category", "Priority", "Status", "Requester", "Created At", "Resolved At"])

    for req in qs.select_related("category", "created_by"):
        writer.writerow([
            req.request_number,
            req.title,
            req.category.name if req.category else "",
            req.get_priority_display(),
            req.get_status_display(),
            req.created_by.email,
            req.created_at.strftime("%Y-%m-%d %H:%M"),
            req.resolved_at.strftime("%Y-%m-%d %H:%M") if req.resolved_at else "N/A",
        ])

    return response


@login_required
def requests_list(request):
    """Searchable, filterable list of service requests."""
    user = request.user
    qs = ServiceRequest.objects.filter(created_by=user) if user.is_customer else ServiceRequest.objects.all()

    status_filter = request.GET.get("status")
    priority_filter = request.GET.get("priority")
    category_filter = request.GET.get("category")
    search_query = request.GET.get("search", "").strip()

    if status_filter:
        qs = qs.filter(status=status_filter)
    if priority_filter:
        qs = qs.filter(priority=priority_filter)
    if category_filter:
        qs = qs.filter(category_id=category_filter)
    if search_query:
        qs = qs.filter(
            Q(request_number__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    requests = (
        qs.select_related("category", "created_by")
        .only(
            "id", "request_number", "title", "priority", "status", "created_at",
            "category__name", "created_by__first_name", "created_by__last_name"
        )
        .order_by("-created_at")
    )

    context = {
        **get_common_context(request, active_tab="requests"),
        "requests": requests,
        "categories": get_cached_active_categories(),
        "status_choices": RequestStatus.choices,
        "priority_choices": RequestPriority.choices,
        "selected_status": status_filter,
        "selected_priority": priority_filter,
        "selected_category": category_filter,
        "search_query": search_query,
    }
    return render(request, "requests/list.html", context)


@login_required
def request_create(request):
    """Ticket submission form."""
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        category_id = request.POST.get("category")
        priority = request.POST.get("priority", RequestPriority.MEDIUM)

        if not all([title, description, category_id]):
            messages.error(request, "Please provide all required ticket details.")
        else:
            category = get_object_or_404(Category, id=category_id)
            service_request = ServiceRequest.objects.create(
                title=title,
                description=description,
                category=category,
                priority=priority,
                created_by=request.user,
                status=RequestStatus.OPEN,
            )
            logger.info("Service request created: %s by %s", service_request.request_number, request.user.email)
            messages.success(request, f"Service request {service_request.request_number} submitted successfully.")
            return redirect("request_detail", pk=service_request.id)

    context = {
        **get_common_context(request, active_tab="requests"),
        "categories": get_cached_active_categories(),
        "priority_choices": RequestPriority.choices,
    }
    return render(request, "requests/create.html", context)


@login_required
def request_detail(request, pk: int):
    """Comprehensive ticket view with discussion thread and attachments."""
    user = request.user
    if user.is_customer:
        service_request = get_object_or_404(ServiceRequest, pk=pk, created_by=user)
    else:
        service_request = get_object_or_404(ServiceRequest, pk=pk)

    comments = (
        service_request.comments
        .select_related("user")
        .only("id", "message", "created_at", "updated_at", "user__first_name", "user__last_name", "user__role", "user__email")
        .order_by("created_at")
    )

    attachments = (
        service_request.attachments
        .select_related("uploaded_by")
        .only("id", "original_name", "file", "uploaded_at", "uploaded_by__first_name", "uploaded_by__last_name")
        .order_by("-uploaded_at")
    )

    assignment = getattr(service_request, "assignment", None)
    staff_users = get_cached_staff_users() if user.is_support_staff else []

    context = {
        **get_common_context(request, active_tab="requests"),
        "request_obj": service_request,
        "comments": comments,
        "attachments": attachments,
        "assignment": assignment,
        "status_choices": RequestStatus.choices,
        "staff_users": staff_users,
    }
    return render(request, "requests/detail.html", context)


@login_required
def request_update_status(request, pk: int):
    """Transitions ticket status and notifies the requester."""
    if request.method == "POST":
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        new_status = request.POST.get("status")

        if new_status in dict(RequestStatus.choices):
            service_request.status = new_status
            if new_status == RequestStatus.RESOLVED and not service_request.resolved_at:
                service_request.resolved_at = timezone.now()
            elif new_status == RequestStatus.CLOSED and not service_request.closed_at:
                service_request.closed_at = timezone.now()
            service_request.save()

            if request.user != service_request.created_by:
                Notification.objects.create(
                    user=service_request.created_by,
                    title=f"Request {service_request.request_number} Updated",
                    message=f"Status changed to {service_request.get_status_display()}.",
                )
                invalidate_user_notification_cache(service_request.created_by_id)

            messages.success(request, f"Status updated to {service_request.get_status_display()}.")
        else:
            messages.error(request, "Invalid status choice selected.")

    return redirect("request_detail", pk=pk)


@login_required
def request_add_comment(request, pk: int):
    """Appends a comment to the ticket discussion."""
    if request.method == "POST":
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        message_text = request.POST.get("message", "").strip()

        if message_text:
            Comment.objects.create(
                service_request=service_request,
                user=request.user,
                message=message_text,
            )
            messages.success(request, "Comment posted.")
        else:
            messages.error(request, "Comment cannot be blank.")

    return redirect("request_detail", pk=pk)


@login_required
def request_add_attachment(request, pk: int):
    """Uploads a file attachment to the active ticket."""
    if request.method == "POST":
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        uploaded_file = request.FILES.get("file")

        if uploaded_file:
            Attachment.objects.create(
                service_request=service_request,
                uploaded_by=request.user,
                file=uploaded_file,
                original_name=uploaded_file.name,
            )
            messages.success(request, f"File '{uploaded_file.name}' attached successfully.")
        else:
            messages.error(request, "Please select a valid file to upload.")

    return redirect("request_detail", pk=pk)


# ==============================================================================
# ASSIGNMENTS & DISPATCH
# ==============================================================================

@login_required
def assignments_list(request):
    """Technician assignment tracking dashboard."""
    assignments = (
        Assignment.objects.select_related("service_request", "assigned_to", "assigned_by")
        .only(
            "id", "assigned_at", "service_request__id", "service_request__request_number",
            "assigned_to__id", "assigned_to__first_name", "assigned_to__last_name", "assigned_to__email",
            "assigned_by__first_name", "assigned_by__last_name"
        )
        .order_by("-assigned_at")
    )

    unassigned_requests = (
        ServiceRequest.objects.filter(
            assignment__isnull=True,
            status__in=[RequestStatus.OPEN, RequestStatus.IN_PROGRESS],
        )
        .only("id", "request_number", "title")
        .order_by("-created_at")
    )

    context = {
        **get_common_context(request, active_tab="assignments"),
        "assignments": assignments,
        "unassigned_requests": unassigned_requests,
        "staff_users": get_cached_staff_users(),
    }
    return render(request, "assignments/list.html", context)


@login_required
def assignment_create(request):
    """Allocates an unassigned ticket to a designated technician."""
    if request.method == "POST":
        request_id = request.POST.get("service_request")
        assigned_to_id = request.POST.get("assigned_to")

        if not request_id or not assigned_to_id:
            messages.error(request, "Please select both a service request and a technician.")
            return redirect("assignments_list")

        service_request = get_object_or_404(ServiceRequest, id=request_id)
        assigned_to = get_object_or_404(User, id=assigned_to_id)

        with transaction.atomic():
            assignment, _ = Assignment.objects.update_or_create(
                service_request=service_request,
                defaults={
                    "assigned_to": assigned_to,
                    "assigned_by": request.user,
                },
            )
            if service_request.status == RequestStatus.OPEN:
                service_request.status = RequestStatus.ASSIGNED
                service_request.save(update_fields=["status", "updated_at"])

        Notification.objects.create(
            user=assigned_to,
            title="New Ticket Assigned",
            message=f"You have been assigned to service request {service_request.request_number}.",
        )
        invalidate_user_notification_cache(assigned_to.id)

        messages.success(request, f"Request {service_request.request_number} assigned to {assigned_to.email}.")

    return redirect("assignments_list")


# ==============================================================================
# ATTACHMENTS & COMMENTS OVERVIEW
# ==============================================================================

@login_required
def attachments_list(request):
    """Global attachment repository."""
    attachments = (
        Attachment.objects.select_related("service_request", "uploaded_by")
        .only(
            "id", "original_name", "file", "uploaded_at",
            "service_request__id", "service_request__request_number",
            "uploaded_by__first_name", "uploaded_by__last_name"
        )
        .order_by("-uploaded_at")
    )
    requests = ServiceRequest.objects.only("id", "request_number", "title").order_by("-created_at")[:30]

    context = {
        **get_common_context(request, active_tab="attachments"),
        "attachments": attachments,
        "requests": requests,
    }
    return render(request, "attachments/list.html", context)


@login_required
def attachment_create(request):
    """Direct attachment upload."""
    if request.method == "POST":
        request_id = request.POST.get("service_request")
        uploaded_file = request.FILES.get("file")

        if not request_id or not uploaded_file:
            messages.error(request, "Please choose a ticket and select a file.")
            return redirect("attachments_list")

        service_request = get_object_or_404(ServiceRequest, id=request_id)
        Attachment.objects.create(
            service_request=service_request,
            uploaded_by=request.user,
            file=uploaded_file,
            original_name=uploaded_file.name,
        )
        messages.success(request, f"Attachment '{uploaded_file.name}' uploaded.")

    return redirect("attachments_list")


@login_required
def comments_list(request):
    """Global comments feed."""
    comments = (
        Comment.objects.select_related("service_request", "user")
        .only(
            "id", "message", "created_at",
            "service_request__id", "service_request__request_number",
            "user__first_name", "user__last_name", "user__role", "user__email"
        )
        .order_by("-created_at")
    )
    requests = ServiceRequest.objects.only("id", "request_number", "title").order_by("-created_at")[:30]

    context = {
        **get_common_context(request, active_tab="comments"),
        "comments": comments,
        "requests": requests,
    }
    return render(request, "comments/list.html", context)


@login_required
def comment_create(request):
    """Direct comment submission."""
    if request.method == "POST":
        request_id = request.POST.get("service_request")
        message_text = request.POST.get("message", "").strip()

        if not request_id or not message_text:
            messages.error(request, "Please choose a ticket and enter your message.")
            return redirect("comments_list")

        service_request = get_object_or_404(ServiceRequest, id=request_id)
        Comment.objects.create(
            service_request=service_request,
            user=request.user,
            message=message_text,
        )
        messages.success(request, f"Comment posted on {service_request.request_number}.")

    return redirect("comments_list")


# ==============================================================================
# NOTIFICATIONS
# ==============================================================================

@login_required
def notifications_list(request):
    """In-app notifications feed."""
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")

    context = {
        **get_common_context(request, active_tab="notifications"),
        "notifications": notifications,
    }
    return render(request, "notifications/list.html", context)


@login_required
def notification_mark_read(request, pk: int):
    """Marks an individual alert as acknowledged."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    invalidate_user_notification_cache(request.user.id)
    messages.success(request, "Notification marked as read.")
    return redirect("notifications_list")


@login_required
def notifications_mark_all_read(request):
    """Bulk acknowledges all active notifications."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    invalidate_user_notification_cache(request.user.id)
    messages.success(request, "All notifications marked as read.")
    return redirect("notifications_list")


# ==============================================================================
# CATEGORIES MANAGEMENT
# ==============================================================================

@login_required
def categories_list(request):
    """Ticket taxonomy categories list."""
    categories = Category.objects.annotate(request_count=Count("service_requests")).order_by("name")

    context = {
        **get_common_context(request, active_tab="categories"),
        "categories": categories,
    }
    return render(request, "categories/list.html", context)


@login_required
def category_create(request):
    """Adds a new ticket classification category."""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        is_active = request.POST.get("is_active") == "on"

        if not name:
            messages.error(request, "Category name is required.")
        elif Category.objects.filter(name__iexact=name).exists():
            messages.error(request, f"A category named '{name}' already exists.")
        else:
            Category.objects.create(name=name, description=description, is_active=is_active)
            cache.delete("active_categories_list")
            messages.success(request, f"Category '{name}' created successfully.")

    return redirect("categories_list")