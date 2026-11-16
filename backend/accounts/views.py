from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    CareBridgeTokenObtainPairSerializer,
    ChangePasswordSerializer,
    RegisterSerializer,
    UserSerializer,
)


class CareBridgeTokenObtainPairView(TokenObtainPairView):
    serializer_class = CareBridgeTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @transaction.atomic
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Keep the clinical directory name in sync with the account name shown
        # in the header and patient/doctor portals.
        full_name = user.get_full_name()
        if hasattr(user, "patient_profile"):
            user.patient_profile.full_name = full_name
            user.patient_profile.save(update_fields=["full_name", "updated_at"])
        if hasattr(user, "doctor_profile"):
            user.doctor_profile.full_name = full_name
            user.doctor_profile.save(update_fields=["full_name", "updated_at"])
        return Response(UserSerializer(user).data)

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)
