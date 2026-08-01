from rest_framework import serializers

from ..models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["public_id", "email", "first_name", "last_name", "is_staff"]


class MeSerializer(serializers.Serializer):
    """The /auth/me contract the SPA uses to render nav and guard routes (see architecture-spec.md §7.3)."""

    user = UserSerializer()
    permissions = serializers.ListField(child=serializers.CharField())


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=10)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(username=validated_data["email"], **validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
