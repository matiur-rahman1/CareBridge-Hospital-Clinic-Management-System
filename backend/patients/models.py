from django.conf import settings
from django.db import models


class Patient(models.Model):
    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"
        PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer not to say"

    class BloodGroup(models.TextChoices):
        A_POS = "A+", "A+"
        A_NEG = "A-", "A-"
        B_POS = "B+", "B+"
        B_NEG = "B-", "B-"
        AB_POS = "AB+", "AB+"
        AB_NEG = "AB-", "AB-"
        O_POS = "O+", "O+"
        O_NEG = "O-", "O-"
        UNKNOWN = "UNKNOWN", "Unknown"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="patient_profile"
    )
    patient_id = models.CharField(max_length=12, unique=True, blank=True, editable=False)
    full_name = models.CharField(max_length=160)
    email = models.EmailField(null=True, blank=True, unique=True)
    phone = models.CharField(max_length=25, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    address = models.TextField(blank=True)
    blood_group = models.CharField(max_length=8, choices=BloodGroup.choices, default=BloodGroup.UNKNOWN)
    profile_picture = models.ImageField(upload_to="patients/", null=True, blank=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-registration_date"]
        indexes = [models.Index(fields=["full_name"], name="patient_full_name_idx"), models.Index(fields=["phone"], name="patient_phone_idx")]

    def save(self, *args, **kwargs):
        creating = self.pk is None
        if creating and not self.patient_id:
            import uuid
            self.patient_id = f"TMP{uuid.uuid4().hex[:9].upper()}"
        super().save(*args, **kwargs)
        if creating and self.patient_id.startswith("TMP"):
            self.patient_id = f"PAT{self.pk:04d}"
            super().save(update_fields=["patient_id"])

    def __str__(self):
        return f"{self.patient_id} - {self.full_name}"
