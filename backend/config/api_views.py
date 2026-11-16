from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from appointments.models import Appointment
from appointments.serializers import AppointmentSerializer
from billing.models import Payment
from doctors.models import Doctor
from patients.models import Patient


class DashboardSummaryView(APIView):
    """Role-aware summary endpoint used by the React dashboard."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        appointments = Appointment.objects.select_related("patient", "doctor")
        payments = Payment.objects.select_related("invoice", "invoice__patient")
        if user.role == User.Role.DOCTOR:
            appointments = appointments.filter(doctor__user=user)
            payments = payments.filter(invoice__appointment__doctor__user=user)
            patient_count = Patient.objects.filter(appointments__doctor__user=user).distinct().count()
            doctor_count = 1
        elif user.role == User.Role.PATIENT:
            appointments = appointments.filter(patient__user=user)
            payments = payments.filter(invoice__patient__user=user)
            patient_count = Patient.objects.filter(user=user).count()
            doctor_count = Doctor.objects.filter(is_active=True).count()
        else:
            patient_count = Patient.objects.count()
            doctor_count = Doctor.objects.filter(is_active=True).count()

        today = timezone.localdate()
        total_revenue = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        chart_start = today - timedelta(days=183)
        monthly_appointments = list(
            appointments.filter(appointment_date__gte=chart_start)
            .annotate(month=TruncMonth("appointment_date"))
            .values("month").annotate(count=Count("id")).order_by("month")
        )
        monthly_revenue = list(
            payments.filter(payment_date__date__gte=chart_start)
            .annotate(month=TruncMonth("payment_date"))
            .values("month").annotate(amount=Sum("amount")).order_by("month")
        )
        recent = appointments.order_by("-appointment_date", "-start_time")[:8]
        recent_data = AppointmentSerializer(recent, many=True, context={"request": request}).data

        return Response({
            "total_patients": patient_count,
            "total_doctors": doctor_count,
            "today_appointments": appointments.filter(appointment_date=today).count(),
            "pending_appointments": appointments.filter(status=Appointment.Status.PENDING).count(),
            "completed_appointments": appointments.filter(status=Appointment.Status.COMPLETED).count(),
            "total_revenue": str(total_revenue),
            "recent_appointments": recent_data,
            "monthly_appointments": [
                {"month": row["month"].strftime("%Y-%m"), "count": row["count"]}
                for row in monthly_appointments if row["month"]
            ],
            "monthly_revenue": [
                {"month": row["month"].strftime("%Y-%m"), "amount": str(row["amount"] or Decimal("0.00"))}
                for row in monthly_revenue if row["month"]
            ],
        })
