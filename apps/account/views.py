from django.db import transaction

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import User, Address
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    ProfileSerializer,
    AddressSerializer
)


# =========================
# USER + AUTH
# =========================
class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action == "register":
            return [AllowAny()]
        return [IsAuthenticated()]

    # POST /users/register/
    @action(detail=False, methods=["post"])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )

    # GET/PUT/PATCH /users/me/
    @action(detail=False, methods=["get", "put", "patch"])
    def me(self, request):
        user = request.user

        if request.method == "GET":
            return Response(UserSerializer(user).data)

        serializer = UserSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


# =========================
# 🧠 PROFILE
# =========================
class ProfileViewSet(viewsets.GenericViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile

    # GET /profile/
    def list(self, request):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    # PATCH /profile/
    def partial_update(self, request):
        profile = self.get_object()

        serializer = self.get_serializer(
            profile,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


# =========================
# ADDRESS (Checkout critical)
# =========================
class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user

        has_address = Address.objects.filter(user=user).exists()

        serializer.save(
            user=user,
            is_default=not has_address
        )

    # POST /addresses/{id}/set_default/
    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        address = self.get_object()

        with transaction.atomic():
            Address.objects.filter(
                user=request.user,
                is_default=True
            ).update(is_default=False)

            address.is_default = True
            address.save()

        return Response(
            {"detail": "Default address set"},
            status=status.HTTP_200_OK
        )