from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("appointment_date", "start_time", "patient", "doctor", "status")
    list_filter = ("status", "appointment_date", "doctor")
    search_fields = ("patient__full_name", "patient__patient_id", "doctor__full_name")
    date_hierarchy = "appointment_date"
