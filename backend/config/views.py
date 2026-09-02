from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.http import condition

from apps.assignments.models import Assignment
from apps.attachments.models import Attachment
from apps.categories.models import Category
from apps.comments.models import Comment
from apps.notifications.models import Notification
from apps.service_requests.models import RequestPriority, RequestStatus, ServiceRequest
from apps.users.models import User, UserRole


# Helper context processor / injector for unread notifications count
def get_common_context(request, active_tab="dashboard"):
    unread_count = 0
    if request.user.is_authenticated:
        # Use only() to optimize query - load only needed field
        unread_count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).only('id').count()
    return {
        "active_tab": active_tab,
        "unread_notifications_count": unread_count,
    }


# ==============================================================================
# AUTHENTICATION UI
# ==============================================================================
def ui_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        if not email or not password:
            messages.error(request, "Please provide both email and password.")
            return render(request, "login.html")

        # Custom user model uses email as USERNAME_FIELD
        user = authenticate(request, username=email, password=password)
        if user is None:
            # Fallback check if user exists and check_password directly
            try:
                u = User.objects.get(email=email)
                if u.check_password(password):
                    user = u
            except User.DoesNotExist:
                user = None

        if user is not None:
            if not user.is_active:
                messages.error(request, "Your account is inactive. Please contact support.")
                return render(request, "login.html")
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            next_url = request.GET.get("next") or "dashboard"
            return redirect(next_url)
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, "login.html")


def ui_register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        phone = request.POST.get("phone", "").strip()

        if not email or not password or not first_name or not last_name:
            messages.error(request, "All required fields must be filled.")
            return render(request, "register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
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
        messages.success(request, "Account created successfully! Welcome to Service Management.")
        return redirect("dashboard")

    return render(request, "register.html")


def ui_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("ui_login")


# ==============================================================================
# DASHBOARD
# ==============================================================================
@login_required
def dashboard(request):
    user = request.user
    
    # Queryset filtered by role
    if user.role == UserRole.CUSTOMER:
        base_qs = ServiceRequest.objects.filter(created_by=user)
    else:
        base_qs = ServiceRequest.objects.all()

    # Optimize: Get all counts in single annotated query
    from django.db.models import Case, When, IntegerField
    
    stats = base_qs.aggregate(
        total=Count('id'),
        pending=Count(Case(When(status=RequestStatus.OPEN, then=1), output_field=IntegerField())),
        assigned=Count(Case(When(status__in=[RequestStatus.ASSIGNED, RequestStatus.IN_PROGRESS], then=1), output_field=IntegerField())),
        resolved=Count(Case(When(status__in=[RequestStatus.RESOLVED, RequestStatus.CLOSED], then=1), output_field=IntegerField())),
    )

    # Prefetch related objects to avoid N+1 queries
    recent_requests = (
        base_qs.select_related("category", "created_by")
        .only("id", "request_number", "title", "priority", "status", "created_at", "category_id", "created_by_id")
        .order_by("-created_at")[:10]
    )

    recent_notifications = (
        Notification.objects.filter(user=user)
        .only("id", "title", "message", "is_read", "created_at")
        .order_by("-created_at")[:5]
    )

    context = {
        **get_common_context(request, active_tab="dashboard"),
        "total_requests": stats['total'],
        "pending_requests": stats['pending'],
        "assigned_requests": stats['assigned'],
        "resolved_requests": stats['resolved'],
        "recent_requests": recent_requests,
        "recent_notifications": recent_notifications,
    }
    return render(request, "dashboard.html", context)


# ==============================================================================
# SERVICE REQUESTS
# ==============================================================================
@login_required
def requests_list(request):
    user = request.user
    if user.role == UserRole.CUSTOMER:
        qs = ServiceRequest.objects.filter(created_by=user)
    else:
        qs = ServiceRequest.objects.all()

    # Filtering
    status_filter = request.GET.get("status")
    priority_filter = request.GET.get("priority")
    category_filter = request.GET.get("category")
    search_query = request.GET.get("search")

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
        .only("id", "request_number", "title", "priority", "status", "created_at", "category__name", "created_by__first_name", "created_by__last_name")
        .order_by("-created_at")
    )
    
    # Cache categories since they change infrequently
    categories = Category.objects.filter(is_active=True).only("id", "name")

    context = {
        **get_common_context(request, active_tab="requests"),
        "requests": requests,
        "categories": categories,
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
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        category_id = request.POST.get("category")
        priority = request.POST.get("priority", RequestPriority.MEDIUM)

        if not title or not description or not category_id:
            messages.error(request, "Please fill in all required fields.")
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
            messages.success(request, f"Service Request {service_request.request_number} created successfully!")
            return redirect("request_detail", pk=service_request.id)

    categories = Category.objects.filter(is_active=True)
    context = {
        **get_common_context(request, active_tab="requests"),
        "categories": categories,
        "priority_choices": RequestPriority.choices,
    }
    return render(request, "requests/create.html", context)


@login_required
def request_detail(request, pk):
    user = request.user
    if user.role == UserRole.CUSTOMER:
        service_request = get_object_or_404(ServiceRequest, pk=pk, created_by=user)
    else:
        service_request = get_object_or_404(ServiceRequest, pk=pk)

    # Optimize: Load related objects with select_related and only() for needed fields
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
    
    # Try to get assignment if exists
    assignment = getattr(service_request, "assignment", None)
    
    # Only load staff users if not a customer (optimization)
    if user.role != UserRole.CUSTOMER:
        staff_users = User.objects.filter(
            role__in=[UserRole.SUPPORT_STAFF, UserRole.MANAGER, UserRole.ADMIN],
            is_active=True,
        ).only("id", "first_name", "last_name", "email", "role")
    else:
        staff_users = []

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
def request_update_status(request, pk):
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

            # Create notification for creator if changed by staff
            if request.user != service_request.created_by:
                Notification.objects.create(
                    user=service_request.created_by,
                    title=f"Request {service_request.request_number} Updated",
                    message=f"Your request status has been updated to {service_request.get_status_display()}.",
                )

            messages.success(request, f"Status updated to {service_request.get_status_display()}.")
        else:
            messages.error(request, "Invalid status choice.")

    return redirect("request_detail", pk=pk)


@login_required
def request_add_comment(request, pk):
    if request.method == "POST":
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        message_text = request.POST.get("message", "").strip()

        if message_text:
            Comment.objects.create(
                service_request=service_request,
                user=request.user,
                message=message_text,
            )
            messages.success(request, "Comment added.")
        else:
            messages.error(request, "Comment cannot be empty.")

    return redirect("request_detail", pk=pk)


@login_required
def request_add_attachment(request, pk):
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
            messages.success(request, f"File '{uploaded_file.name}' uploaded successfully.")
        else:
            messages.error(request, "Please choose a file to upload.")

    return redirect("request_detail", pk=pk)


# ==============================================================================
# ASSIGNMENTS
# ==============================================================================
@login_required
def assignments_list(request):
    # Optimize: Load only needed fields
    assignments = (
        Assignment.objects.select_related("service_request", "assigned_to", "assigned_by")
        .only("id", "assigned_at", "service_request__id", "service_request__request_number", "assigned_to__id", "assigned_to__first_name", "assigned_to__last_name", "assigned_to__email", "assigned_by__first_name", "assigned_by__last_name")
        .order_by("-assigned_at")
    )

    # Optimize: Only fetch needed fields for unassigned requests
    unassigned_requests = (
        ServiceRequest.objects.filter(
            assignment__isnull=True,
            status__in=[RequestStatus.OPEN, RequestStatus.IN_PROGRESS],
        )
        .only("id", "request_number", "title")
        .order_by("-created_at")
    )

    staff_users = User.objects.filter(
        role__in=[UserRole.SUPPORT_STAFF, UserRole.MANAGER, UserRole.ADMIN],
        is_active=True,
    ).only("id", "first_name", "last_name", "email", "role")

    context = {
        **get_common_context(request, active_tab="assignments"),
        "assignments": assignments,
        "unassigned_requests": unassigned_requests,
        "staff_users": staff_users,
    }
    return render(request, "assignments/list.html", context)


@login_required
def assignment_create(request):
    if request.method == "POST":
        request_id = request.POST.get("service_request")
        assigned_to_id = request.POST.get("assigned_to")

        if not request_id or not assigned_to_id:
            messages.error(request, "Please select both a request and a technician.")
            return redirect("assignments_list")

        service_request = get_object_or_404(ServiceRequest, id=request_id)
        assigned_to = get_object_or_404(User, id=assigned_to_id)

        assignment, created = Assignment.objects.update_or_create(
            service_request=service_request,
            defaults={
                "assigned_to": assigned_to,
                "assigned_by": request.user,
            },
        )

        # Automatically update status if OPEN
        if service_request.status == RequestStatus.OPEN:
            service_request.status = RequestStatus.ASSIGNED
            service_request.save()

        # Notify technician
        Notification.objects.create(
            user=assigned_to,
            title="New Assignment",
            message=f"You have been assigned to service request {service_request.request_number}.",
        )

        messages.success(request, f"Request {service_request.request_number} assigned to {assigned_to.email}!")

    return redirect("assignments_list")


# ==============================================================================
# ATTACHMENTS
# ==============================================================================
@login_required
def attachments_list(request):
    # Optimize: Load only needed fields
    attachments = (
        Attachment.objects.select_related("service_request", "uploaded_by")
        .only("id", "original_name", "file", "uploaded_at", "service_request__id", "service_request__request_number", "uploaded_by__first_name", "uploaded_by__last_name")
        .order_by("-uploaded_at")
    )

    # Optimize: Only fetch needed fields for requests
    requests = (
        ServiceRequest.objects.only("id", "request_number", "title")
        .order_by("-created_at")[:30]
    )

    context = {
        **get_common_context(request, active_tab="attachments"),
        "attachments": attachments,
        "requests": requests,
    }
    return render(request, "attachments/list.html", context)


@login_required
def attachment_create(request):
    if request.method == "POST":
        request_id = request.POST.get("service_request")
        uploaded_file = request.FILES.get("file")

        if not request_id or not uploaded_file:
            messages.error(request, "Please select a service request and choose a file.")
            return redirect("attachments_list")

        service_request = get_object_or_404(ServiceRequest, id=request_id)
        Attachment.objects.create(
            service_request=service_request,
            uploaded_by=request.user,
            file=uploaded_file,
            original_name=uploaded_file.name,
        )
        messages.success(request, f"Attachment '{uploaded_file.name}' uploaded successfully.")

    return redirect("attachments_list")


# ==============================================================================
# COMMENTS
# ==============================================================================
@login_required
def comments_list(request):
    # Optimize: Load only needed fields
    comments = (
        Comment.objects.select_related("service_request", "user")
        .only("id", "message", "created_at", "service_request__id", "service_request__request_number", "user__first_name", "user__last_name", "user__role", "user__email")
        .order_by("-created_at")
    )
    
    # Optimize: Only fetch needed fields for requests
    requests = (
        ServiceRequest.objects.only("id", "request_number", "title")
        .order_by("-created_at")[:30]
    )

    context = {
        **get_common_context(request, active_tab="comments"),
        "comments": comments,
        "requests": requests,
    }
    return render(request, "comments/list.html", context)


@login_required
def comment_create(request):
    if request.method == "POST":
        request_id = request.POST.get("service_request")
        message_text = request.POST.get("message", "").strip()

        if not request_id or not message_text:
            messages.error(request, "Please select a request and enter a comment message.")
            return redirect("comments_list")

        service_request = get_object_or_404(ServiceRequest, id=request_id)
        Comment.objects.create(
            service_request=service_request,
            user=request.user,
            message=message_text,
        )
        messages.success(request, f"Comment posted on request {service_request.request_number}.")

    return redirect("comments_list")


# ==============================================================================
# NOTIFICATIONS
# ==============================================================================
@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")

    context = {
        **get_common_context(request, active_tab="notifications"),
        "notifications": notifications,
    }
    return render(request, "notifications/list.html", context)


@login_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    messages.success(request, "Notification marked as read.")
    return redirect("notifications_list")


@login_required
def notifications_mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("notifications_list")


# ==============================================================================
# CATEGORIES
# ==============================================================================
@login_required
def categories_list(request):
    categories = Category.objects.annotate(request_count=Count("service_requests")).order_by("name")

    context = {
        **get_common_context(request, active_tab="categories"),
        "categories": categories,
    }
    return render(request, "categories/list.html", context)


@login_required
def category_create(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        is_active = request.POST.get("is_active") == "on"

        if not name:
            messages.error(request, "Category name is required.")
        elif Category.objects.filter(name__iexact=name).exists():
            messages.error(request, f"A category named '{name}' already exists.")
        else:
            Category.objects.create(
                name=name,
                description=description,
                is_active=is_active,
            )
            messages.success(request, f"Category '{name}' created successfully.")

    return redirect("categories_list")