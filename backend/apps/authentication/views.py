from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from .serializers import (
    LoginRequestSerializer,
    LoginResponseSerializer,
    RegisterRequestSerializer,
    RegisterResponseSerializer,
    UserResponseSerializer,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

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
        email = request.data.get("email")
        password = request.data.get("password")
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")
        phone = request.data.get("phone", "")

        if not email or not password or not first_name or not last_name:
            return Response(
                {"detail": "email, password, first_name and last_name are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "User with this email already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
        )

        return Response(
            {
                "message": "User registered successfully",
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
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Authentication"],
        summary="User login",
        description="Authenticates a user with email and password, returning JWT access and refresh tokens.",
        request=LoginRequestSerializer,
        responses={
            200: LoginResponseSerializer,
            401: OpenApiResponse(description="Invalid email or password"),
            403: OpenApiResponse(description="User account is inactive"),
        },
    )
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"detail": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"detail": "User account is inactive"},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful",
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
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Authentication"],
        summary="Get current user profile",
        description="Returns details for the currently authenticated user.",
        responses={
            200: UserResponseSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided or invalid"),
        },
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