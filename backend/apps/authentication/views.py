import logging
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User, UserRole
from .serializers import (
    LoginRequestSerializer,
    LoginResponseSerializer,
    RegisterRequestSerializer,
    RegisterResponseSerializer,
    UserResponseSerializer,
)

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """
    Public registration endpoint for new customer onboarding.
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Authentication"],
        summary="Register a new customer account",
        description="Creates a new customer user account with email and password.",
        request=RegisterRequestSerializer,
        responses={
            201: RegisterResponseSerializer,
            400: OpenApiResponse(description="Validation error or user already exists"),
        },
    )
    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")
        first_name = request.data.get("first_name", "").strip()
        last_name = request.data.get("last_name", "").strip()
        phone = request.data.get("phone", "").strip()

        if not all([email, password, first_name, last_name]):
            return Response(
                {"detail": "Email, password, first name, and last name are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "An account with this email address already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=UserRole.CUSTOMER,
        )

        logger.info("New customer registered: %s (ID: %s)", user.email, user.id)

        return Response(
            {
                "message": "Account created successfully.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    Exchanges valid user credentials for a JSON Web Token pair (access + refresh).
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Authentication"],
        summary="Authenticate and receive JWT tokens",
        description="Returns an access token (for Bearer headers) and a rotating refresh token.",
        request=LoginRequestSerializer,
        responses={
            200: LoginResponseSerializer,
            401: OpenApiResponse(description="Invalid email or password"),
            403: OpenApiResponse(description="Account is disabled"),
        },
    )
    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid credentials provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"detail": "Invalid credentials provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"detail": "This user account has been disabled. Please contact an administrator."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        logger.info("User logged in via API: %s", user.email)

        return Response(
            {
                "message": "Authentication successful.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                },
            }
        )


class MeView(APIView):
    """
    Returns identity and role profile for the currently authenticated session.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Authentication"],
        summary="Get active user profile",
        responses={200: UserResponseSerializer},
    )
    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "role": user.role,
            }
        )