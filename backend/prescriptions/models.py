from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Prescription(models.Model):
    appointment = models.OneToOneField(
        "appointments.Appointment", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="prescription"
    )
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="prescriptions")
    doctor = models.ForeignKey("doctors.Doctor", on_delete=models.PROTECT, related_name="prescriptions")
    prescription_date = models.DateField(auto_now_add=True)
    diagnosis = models.CharField(max_length=255, blank=True)
    instructions = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="prescriptions_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-prescription_date", "-created_at"]

    def __str__(self):
        return f"Prescription #{self.pk} - {self.patient.full_name}"


class PrescriptionMedicine(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="medicines")
    medicine_name = models.CharField(max_length=160)
    dosage = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    quantity = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    instructions = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.medicine_name} ({self.dosage})"
