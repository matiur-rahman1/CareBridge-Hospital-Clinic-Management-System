from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("patient_id", "full_name", "phone", "email", "blood_group", "registration_date")
    search_fields = ("patient_id", "full_name", "phone", "email")
    list_filter = ("gender", "blood_group")
