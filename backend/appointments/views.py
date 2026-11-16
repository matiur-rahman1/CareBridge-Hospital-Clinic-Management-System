from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from accounts.models import User
from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    filterset_fields = ["patient", "doctor", "status", "appointment_date"]
    search_fields = ["patient__full_name", "patient__patient_id", "doctor__full_name", "reason"]
    ordering_fields = ["appointment_date", "start_time", "created_at", "status"]

    def get_queryset(self):
        qs = Appointment.objects.select_related("patient", "doctor", "created_by")
        user = self.request.user
        if user.role in {User.Role.ADMIN, User.Role.RECEPTIONIST}:
            return qs
        if user.role == User.Role.DOCTOR:
            return qs.filter(doctor__user=user)
        if user.role == User.Role.PATIENT:
            return qs.filter(patient__user=user)
        return qs.none()

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        if self.request.user.role not in {User.Role.ADMIN, User.Role.RECEPTIONIST, User.Role.PATIENT}:
            raise PermissionDenied("Only administrators, receptionists, or patients can book appointments.")
        serializer.save()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        if user.role in {User.Role.ADMIN, User.Role.RECEPTIONIST}:
            return super().update(request, *args, **kwargs)
        if user.role == User.Role.DOCTOR:
            if instance.doctor.user_id != user.id:
                raise PermissionDenied("You can only update your own appointments.")
            if set(request.data.keys()) - {"status"} or request.data.get("status") != Appointment.Status.COMPLETED:
                raise PermissionDenied("Doctors may only mark their own appointments as completed.")
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        if user.role == User.Role.PATIENT:
            if instance.patient.user_id != user.id or set(request.data.keys()) != {"status"} or request.data.get("status") != Appointment.Status.CANCELLED:
                raise PermissionDenied("Patients may only cancel their own appointments.")
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        raise PermissionDenied("You do not have permission to update appointments.")

    def destroy(self, request, *args, **kwargs):
        if request.user.role not in {User.Role.ADMIN, User.Role.RECEPTIONIST}:
            raise PermissionDenied("Only administrators and receptionists can delete appointments.")
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="today")
    def today(self, request):
        from django.utils import timezone
        qs = self.filter_queryset(self.get_queryset()).filter(appointment_date=timezone.localdate())
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)
