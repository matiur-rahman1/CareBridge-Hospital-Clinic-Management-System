from django.contrib import admin
from .models import Prescription, PrescriptionMedicine


class MedicineInline(admin.TabularInline):
    model = PrescriptionMedicine
    extra = 1


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "prescription_date", "patient", "doctor", "diagnosis")
    search_fields = ("patient__full_name", "patient__patient_id", "doctor__full_name", "diagnosis")
    list_filter = ("prescription_date",)
    inlines = [MedicineInline]
