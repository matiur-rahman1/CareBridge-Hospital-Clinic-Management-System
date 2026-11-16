from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models.deletion import ProtectedError
from accounts.models import User
from accounts.permissions import IsAdminOrReceptionist
from .models import Doctor, DoctorAvailability
from .serializers import DoctorAvailabilitySerializer, DoctorSerializer


class DoctorViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorSerializer
    filterset_fields = ["specialization", "is_active"]
    search_fields = ["doctor_id", "full_name", "specialization", "qualifications", "email"]
    ordering_fields = ["full_name", "consultation_fee", "specialization"]

    def get_queryset(self):
        user = self.request.user
        qs = Doctor.objects.prefetch_related("availabilities")
        if user.role in {User.Role.ADMIN, User.Role.RECEPTIONIST}:
            return qs
        if user.role == User.Role.PATIENT:
            return qs.filter(is_active=True)
        if user.role == User.Role.DOCTOR:
            return qs.filter(user=user)
        return qs.none()

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrReceptionist()]

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as exc:
            raise ValidationError("This doctor has linked appointments or prescriptions. Deactivate the profile instead of deleting it.") from exc


class DoctorAvailabilityViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorAvailabilitySerializer
    filterset_fields = ["doctor", "weekday", "is_active"]
    ordering_fields = ["weekday", "start_time"]

    def get_queryset(self):
        qs = DoctorAvailability.objects.select_related("doctor", "doctor__user")
        user = self.request.user
        if user.role == User.Role.DOCTOR:
            return qs.filter(doctor__user=user)
        if user.role in {User.Role.ADMIN, User.Role.RECEPTIONIST, User.Role.PATIENT}:
            return qs
        return qs.none()

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        doctor = serializer.validated_data["doctor"]
        if user.role not in {User.Role.ADMIN, User.Role.RECEPTIONIST} and not (user.role == User.Role.DOCTOR and doctor.user_id == user.id):
            raise PermissionDenied("You cannot manage availability for this doctor.")
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        doctor = serializer.instance.doctor
        requested_doctor = serializer.validated_data.get("doctor", doctor)
        if user.role == User.Role.DOCTOR and requested_doctor.user_id != user.id:
            raise PermissionDenied("You cannot transfer availability to another doctor.")
        if user.role not in {User.Role.ADMIN, User.Role.RECEPTIONIST} and not (user.role == User.Role.DOCTOR and doctor.user_id == user.id):
            raise PermissionDenied("You cannot manage availability for this doctor.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if user.role not in {User.Role.ADMIN, User.Role.RECEPTIONIST} and not (user.role == User.Role.DOCTOR and instance.doctor.user_id == user.id):
            raise PermissionDenied("You cannot manage availability for this doctor.")
        instance.delete()
