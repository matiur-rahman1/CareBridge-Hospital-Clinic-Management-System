from django.contrib import admin
from .models import Doctor, DoctorAvailability


class AvailabilityInline(admin.TabularInline):
    model = DoctorAvailability
    extra = 0


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("doctor_id", "full_name", "specialization", "consultation_fee", "is_active")
    search_fields = ("doctor_id", "full_name", "specialization", "email")
    list_filter = ("specialization", "is_active")
    inlines = [AvailabilityInline]


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("doctor", "weekday", "start_time", "end_time", "slot_minutes", "is_active")
    list_filter = ("weekday", "is_active")
