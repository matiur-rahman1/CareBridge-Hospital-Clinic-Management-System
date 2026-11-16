from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models.deletion import ProtectedError
from accounts.models import User
from accounts.permissions import IsAdminOrReceptionist
from .models import Patient
from .serializers import PatientSerializer


class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    filterset_fields = ["gender", "blood_group"]
    search_fields = ["patient_id", "full_name", "email", "phone"]
    ordering_fields = ["registration_date", "full_name", "patient_id"]

    def get_queryset(self):
        user = self.request.user
        qs = Patient.objects.select_related("user")
        if user.role in {User.Role.ADMIN, User.Role.RECEPTIONIST}:
            return qs
        if user.role == User.Role.DOCTOR:
            return qs.filter(appointments__doctor__user=user).distinct()
        if user.role == User.Role.PATIENT:
            return qs.filter(user=user)
        return qs.none()

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrReceptionist()]

    def perform_create(self, serializer):
        if self.request.user.role not in {User.Role.ADMIN, User.Role.RECEPTIONIST}:
            raise PermissionDenied("Only administrators and receptionists can register patients.")
        serializer.save()

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as exc:
            raise ValidationError("This patient has linked appointments, prescriptions, or invoices. Keep the record to preserve medical history.") from exc
