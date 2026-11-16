from django.conf import settings
from django.db import models
from django.db.models import Q


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="appointments")
    doctor = models.ForeignKey("doctors.Doctor", on_delete=models.PROTECT, related_name="appointments")
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_appointments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["appointment_date", "start_time"]
        constraints = [
            models.CheckConstraint(condition=Q(end_time__gt=models.F("start_time")), name="appointment_end_after_start"),
            models.UniqueConstraint(
                fields=["doctor", "appointment_date", "start_time"],
                condition=Q(status__in=["PENDING", "CONFIRMED", "COMPLETED"]),
                name="unique_active_doctor_appointment_start",
            ),
        ]
        indexes = [
            models.Index(fields=["appointment_date", "status"], name="appt_date_status_idx"),
            models.Index(fields=["doctor", "appointment_date"], name="appt_doctor_date_idx"),
            models.Index(fields=["patient", "appointment_date"], name="appt_patient_date_idx"),
        ]

    def __str__(self):
        return f"{self.patient} / {self.doctor} / {self.appointment_date} {self.start_time}"
