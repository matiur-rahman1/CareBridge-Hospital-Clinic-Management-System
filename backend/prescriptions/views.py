from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied
from accounts.models import User
from .models import Prescription
from .serializers import PrescriptionSerializer


class PrescriptionViewSet(viewsets.ModelViewSet):
    serializer_class = PrescriptionSerializer
    filterset_fields = ["patient", "doctor", "prescription_date"]
    search_fields = ["patient__full_name", "patient__patient_id", "doctor__full_name", "diagnosis", "medicines__medicine_name"]
    ordering_fields = ["prescription_date", "created_at"]

    def get_queryset(self):
        qs = Prescription.objects.select_related("patient", "doctor", "appointment").prefetch_related("medicines")
        user = self.request.user
        if user.role in {User.Role.ADMIN, User.Role.RECEPTIONIST}:
            return qs
        if user.role == User.Role.DOCTOR:
            return qs.filter(doctor__user=user)
        if user.role == User.Role.PATIENT:
            return qs.filter(patient__user=user)
        return qs.none()

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in {User.Role.ADMIN, User.Role.DOCTOR}:
            raise PermissionDenied("Only doctors and administrators can create prescriptions.")
        if user.role == User.Role.DOCTOR:
            doctor = serializer.validated_data.get("doctor")
            if not doctor or doctor.user_id != user.id:
                raise PermissionDenied("Doctors can only create prescriptions under their own profile.")
        serializer.save()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role not in {User.Role.ADMIN, User.Role.DOCTOR}:
            raise PermissionDenied("You cannot edit prescriptions.")
        if request.user.role == User.Role.DOCTOR and instance.doctor.user_id != request.user.id:
            raise PermissionDenied("You can only edit your own prescriptions.")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.role != User.Role.ADMIN:
            raise PermissionDenied("Only administrators can delete prescriptions.")
        return super().destroy(request, *args, **kwargs)
