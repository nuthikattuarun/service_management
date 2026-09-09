import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.users.models import User, UserRole
from apps.categories.models import Category
from apps.service_requests.models import ServiceRequest, RequestPriority, RequestStatus
from apps.assignments.models import Assignment
from apps.comments.models import Comment
from apps.notifications.models import Notification
from django.utils import timezone


def populate():
    print("Seeding enterprise sample data for ServiceDesk Pro...")

    # 1. Ensure Admin User
    admin, _ = User.objects.get_or_create(
        email="arunnuthikattu@gmail.com",
        defaults={
            "first_name": "Arun",
            "last_name": "Nuthikattu",
            "role": UserRole.ADMIN,
            "is_staff": True,
            "is_superuser": True,
        }
    )
    admin.set_password("Admin@12345")
    admin.save()
    print("[OK] Admin user ready: arunnuthikattu@gmail.com")

    # 2. Support Staff & Managers
    staff_sarah, _ = User.objects.get_or_create(
        email="sarah.support@enterprise.com",
        defaults={
            "first_name": "Sarah",
            "last_name": "Jenkins",
            "role": UserRole.SUPPORT_STAFF,
            "is_staff": True,
        }
    )
    staff_sarah.set_password("Staff@12345")
    staff_sarah.save()

    staff_david, _ = User.objects.get_or_create(
        email="david.tech@enterprise.com",
        defaults={
            "first_name": "David",
            "last_name": "Chen",
            "role": UserRole.SUPPORT_STAFF,
            "is_staff": True,
        }
    )
    staff_david.set_password("Staff@12345")
    staff_david.save()

    manager_marcus, _ = User.objects.get_or_create(
        email="marcus.ops@enterprise.com",
        defaults={
            "first_name": "Marcus",
            "last_name": "Vance",
            "role": UserRole.MANAGER,
            "is_staff": True,
        }
    )
    manager_marcus.set_password("Manager@12345")
    manager_marcus.save()

    # 3. Customer Users
    customer_alice, _ = User.objects.get_or_create(
        email="alice.customer@clientcorp.com",
        defaults={
            "first_name": "Alice",
            "last_name": "Morgan",
            "role": UserRole.CUSTOMER,
        }
    )
    customer_alice.set_password("Customer@12345")
    customer_alice.save()

    customer_robert, _ = User.objects.get_or_create(
        email="robert.smith@acme.org",
        defaults={
            "first_name": "Robert",
            "last_name": "Smith",
            "role": UserRole.CUSTOMER,
        }
    )
    customer_robert.set_password("Customer@12345")
    customer_robert.save()

    print("[OK] Team members and customers ready.")

    # 4. Service Categories
    categories_data = [
        ("Cloud & Infrastructure", "AWS, Kubernetes, CDN, and high-availability server infrastructure."),
        ("Cybersecurity & Access", "SSO, VPN gateways, IAM permissions, and security incident response."),
        ("Hardware & Peripherals", "Workstations, monitor setups, docking stations, and mobile devices."),
        ("Enterprise Software & CRM", "ERP integrations, Salesforce CRM, Slack, and internal tooling."),
        ("Billing & Procurement", "Invoicing, hardware procurement, software license subscriptions."),
    ]

    cats = {}
    for name, desc in categories_data:
        cat, _ = Category.objects.get_or_create(
            name=name,
            defaults={"description": desc, "is_active": True}
        )
        cats[name] = cat
    print("[OK] Categories catalog ready.")

    # 5. Realistic Service Requests (if count < 6)
    if ServiceRequest.objects.count() < 5:
        tickets_data = [
            {
                "title": "Production Database Connection Pool Exhaustion",
                "description": "High connection pool wait times observed in US-East-2 cluster. Active microservices experiencing 504 gateway timeouts during peak query traffic.",
                "category": cats["Cloud & Infrastructure"],
                "priority": RequestPriority.URGENT,
                "status": RequestStatus.IN_PROGRESS,
                "created_by": customer_alice,
                "assigned_to": staff_david,
            },
            {
                "title": "VPN Gateway Certificate Expiration for Remote Engineering",
                "description": "GlobalProtect VPN handshake failing due to intermediate certificate expiration. 35 remote engineers unable to access staging clusters.",
                "category": cats["Cybersecurity & Access"],
                "priority": RequestPriority.HIGH,
                "status": RequestStatus.ASSIGNED,
                "created_by": customer_robert,
                "assigned_to": staff_sarah,
            },
            {
                "title": "Docking Station Triple-Display Flickering on M3 MacBooks",
                "description": "DisplayPort 1.4 daisy chaining fails intermittently when waking from sleep mode on MacOS 15.1.",
                "category": cats["Hardware & Peripherals"],
                "priority": RequestPriority.MEDIUM,
                "status": RequestStatus.OPEN,
                "created_by": customer_alice,
                "assigned_to": None,
            },
            {
                "title": "Salesforce OAuth2 Token Refresh Failure in Webhook Pipeline",
                "description": "Customer record webhook pipeline failed to refresh access token automatically. Manual sync required for pending invoice events.",
                "category": cats["Enterprise Software & CRM"],
                "priority": RequestPriority.HIGH,
                "status": RequestStatus.RESOLVED,
                "created_by": customer_robert,
                "assigned_to": staff_david,
            },
            {
                "title": "Q3 Cloud Hosting Invoice Discrepancy & Usage Report",
                "description": "Requesting detailed cost breakdown for multi-region backup storage tier before invoice sign-off.",
                "category": cats["Billing & Procurement"],
                "priority": RequestPriority.LOW,
                "status": RequestStatus.CLOSED,
                "created_by": customer_alice,
                "assigned_to": staff_sarah,
            },
            {
                "title": "Memory Leak in Real-time Telemetry Ingestion Worker",
                "description": "Worker pods consuming 98% memory within 4 hours of deployment. Suspected unclosed socket connections in streaming loop.",
                "category": cats["Cloud & Infrastructure"],
                "priority": RequestPriority.URGENT,
                "status": RequestStatus.OPEN,
                "created_by": customer_robert,
                "assigned_to": None,
            },
        ]

        for item in tickets_data:
            req = ServiceRequest.objects.create(
                title=item["title"],
                description=item["description"],
                category=item["category"],
                priority=item["priority"],
                status=item["status"],
                created_by=item["created_by"],
            )

            if item["status"] == RequestStatus.RESOLVED:
                req.resolved_at = timezone.now()
                req.save()
            elif item["status"] == RequestStatus.CLOSED:
                req.resolved_at = timezone.now()
                req.closed_at = timezone.now()
                req.save()

            if item["assigned_to"]:
                Assignment.objects.create(
                    service_request=req,
                    assigned_to=item["assigned_to"],
                    assigned_by=admin,
                )

            # Add comments
            Comment.objects.create(
                service_request=req,
                user=item["created_by"],
                message="Ticket logged with initial system logs and reproduction steps attached.",
            )

            if item["assigned_to"]:
                Comment.objects.create(
                    service_request=req,
                    user=item["assigned_to"],
                    message=f"Investigation initiated by {item['assigned_to'].first_name}. Running diagnostics now.",
                )

            # Notification
            Notification.objects.create(
                user=admin,
                title=f"New Ticket: {req.request_number}",
                message=f"'{req.title[:45]}' submitted under {req.category.name}.",
            )

        print("[OK] Enterprise service requests, comments, and assignments populated.")

    print("\nSeed data population completed successfully!")



if __name__ == "__main__":
    populate()
