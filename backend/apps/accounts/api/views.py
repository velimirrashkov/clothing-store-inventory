from django.contrib.auth import authenticate, login, logout
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, MeSerializer, RegisterSerializer, UserSerializer


class RegisterView(APIView):
    """POST /api/v1/auth/register — buyers only; staff accounts are provisioned via the admin group flow."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    POST /api/v1/auth/login. Generic error text — never reveal whether the email exists
    (see architecture-spec.md §6.4).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"error": {"code": "invalid_credentials", "message": "Invalid email or password.", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        if user.is_staff:
            request.session.set_expiry(60 * 60 * 8)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        permissions = sorted(user.get_all_permissions())
        data = MeSerializer({"user": user, "permissions": permissions}).data
        return Response(data)
