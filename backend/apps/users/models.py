from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    CUSTOMER = "CUSTOMER", "Customer"
    SUPPORT_STAFF = "SUPPORT_STAFF", "Support Staff"
    MANAGER = "MANAGER", "Manager"
    ADMIN = "ADMIN", "Admin"


class UserManager(BaseUserManager):
    """Custom user manager supporting email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email address is required to register an account.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Primary user identity model.
    Utilizes email as the unique identifier across web and API sessions.
    """

    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
        help_text="Role determining permissions and portal access level.",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this user account should be treated as active.",
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the user can log into the Django admin site.",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    @property
    def full_name(self) -> str:
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email

    @property
    def is_customer(self) -> bool:
        return self.role == UserRole.CUSTOMER

    @property
    def is_support_staff(self) -> bool:
        return self.role in {UserRole.SUPPORT_STAFF, UserRole.MANAGER, UserRole.ADMIN}

    @property
    def is_manager(self) -> bool:
        return self.role in {UserRole.MANAGER, UserRole.ADMIN}

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"