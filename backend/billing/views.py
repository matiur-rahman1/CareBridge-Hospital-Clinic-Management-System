from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models.deletion import ProtectedError
from accounts.models import User
from .models import Invoice, Payment
from .serializers import InvoiceSerializer, PaymentSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    filterset_fields = ["patient", "payment_status", "issue_date"]
    search_fields = ["invoice_number", "patient__full_name", "patient__patient_id"]
    ordering_fields = ["issue_date", "total_amount", "payment_status"]

    def get_queryset(self):
        qs = Invoice.objects.select_related("patient", "appointment").prefetch_related("items", "payments")
        user = self.request.user
        if user.role in {User.Role.ADMIN, User.Role.RECEPTIONIST}:
            return qs
        if user.role == User.Role.PATIENT:
            return qs.filter(patient__user=user)
        if user.role == User.Role.DOCTOR:
            return qs.filter(appointment__doctor__user=user)
        return qs.none()

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        if self.request.user.role not in {User.Role.ADMIN, User.Role.RECEPTIONIST}:
            raise PermissionDenied("Only administrators and receptionists can generate invoices.")
        serializer.save()

    def update(self, request, *args, **kwargs):
        if request.user.role not in {User.Role.ADMIN, User.Role.RECEPTIONIST}:
            raise PermissionDenied("Only administrators and receptionists can edit invoices.")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.role != User.Role.ADMIN:
            raise PermissionDenied("Only administrators can delete invoices.")
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as exc:
            raise ValidationError("This invoice has payments recorded. Preserve the invoice and issue an adjustment instead.") from exc


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    http_method_names = ["get", "post", "head", "options"]
    filterset_fields = ["invoice", "method", "payment_date"]
    search_fields = ["invoice__invoice_number", "invoice__patient__full_name", "reference"]
    ordering_fields = ["payment_date", "amount"]

    def get_queryset(self):
        qs = Payment.objects.select_related("invoice", "invoice__patient", "received_by")
        user = self.request.user
        if user.role in {User.Role.ADMIN, User.Role.RECEPTIONIST}:
            return qs
        if user.role == User.Role.PATIENT:
            return qs.filter(invoice__patient__user=user)
        if user.role == User.Role.DOCTOR:
            return qs.filter(invoice__appointment__doctor__user=user)
        return qs.none()

    def create(self, request, *args, **kwargs):
        if request.user.role not in {User.Role.ADMIN, User.Role.RECEPTIONIST}:
            raise PermissionDenied("Only administrators and receptionists can record payments.")
        return super().create(request, *args, **kwargs)
