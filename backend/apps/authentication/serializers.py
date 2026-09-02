from rest_framework import serializers
from apps.users.models import User, UserRole


class UserResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
        ]
        read_only_fields = fields


class RegisterRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, help_text="User email address")
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text="User password",
    )
    first_name = serializers.CharField(max_length=100, required=True)
    last_name = serializers.CharField(max_length=100, required=True)
    phone = serializers.CharField(max_length=20, required=False, default="", allow_blank=True)


class RegisterResponseSerializer(serializers.Serializer):
    message = serializers.CharField(default="User registered successfully")
    user = UserResponseSerializer()


class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, help_text="User email address")
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text="User password",
    )


class LoginResponseSerializer(serializers.Serializer):
    message = serializers.CharField(default="Login successful")
    access = serializers.CharField(help_text="JWT access token")
    refresh = serializers.CharField(help_text="JWT refresh token")
    user = UserResponseSerializer()
