from rest_framework.permissions import BasePermission
from apps.users.models import UserRole


class IsAdmin(BasePermission):
    """Allows access exclusively to administrator accounts."""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.ADMIN
        )


class IsManager(BasePermission):
    """Allows access to Managers and Administrators."""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in {UserRole.MANAGER, UserRole.ADMIN}
        )


class IsSupportStaff(BasePermission):
    """Allows access to support staff, managers, and system admins."""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in {UserRole.SUPPORT_STAFF, UserRole.MANAGER, UserRole.ADMIN}
        )


class IsCustomer(BasePermission):
    """Allows access exclusively to customer accounts."""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.CUSTOMER
        )