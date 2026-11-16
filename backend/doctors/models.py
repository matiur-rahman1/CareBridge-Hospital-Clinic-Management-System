from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Doctor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="doctor_profile"
    )
    doctor_id = models.CharField(max_length=12, unique=True, blank=True, editable=False)
    full_name = models.CharField(max_length=160)
    specialization = models.CharField(max_length=120)
    qualifications = models.CharField(max_length=255, blank=True)
    email = models.EmailField(null=True, blank=True, unique=True)
    phone = models.CharField(max_length=25, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]
        indexes = [models.Index(fields=["specialization"], name="doctor_specialization_idx"), models.Index(fields=["is_active"], name="doctor_active_idx")]

    def save(self, *args, **kwargs):
        creating = self.pk is None
        if creating and not self.doctor_id:
            import uuid
            self.doctor_id = f"TMP{uuid.uuid4().hex[:9].upper()}"
        super().save(*args, **kwargs)
        if creating and self.doctor_id.startswith("TMP"):
            self.doctor_id = f"DOC{self.pk:04d}"
            super().save(update_fields=["doctor_id"])

    def __str__(self):
        return f"{self.doctor_id} - Dr. {self.full_name}"


class DoctorAvailability(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="availabilities")
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_minutes = models.PositiveSmallIntegerField(default=30, validators=[MinValueValidator(5)])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["weekday", "start_time"]
        constraints = [
            models.CheckConstraint(condition=Q(end_time__gt=models.F("start_time")), name="availability_end_after_start"),
            models.UniqueConstraint(fields=["doctor", "weekday", "start_time", "end_time"], name="unique_doctor_availability_window"),
        ]

    def __str__(self):
        return f"{self.doctor} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"
