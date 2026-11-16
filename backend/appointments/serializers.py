from rest_framework import serializers
from accounts.models import User
from .models import Appointment
from .services import book_appointment, validate_appointment_slot


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    doctor_name = serializers.CharField(source="doctor.full_name", read_only=True)
    doctor_code = serializers.CharField(source="doctor.doctor_id", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Appointment
        fields = (
            "id", "patient", "patient_name", "patient_code", "doctor", "doctor_name", "doctor_code",
            "appointment_date", "start_time", "end_time", "status", "status_display", "reason", "notes",
            "created_by", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        doctor = attrs.get("doctor", getattr(self.instance, "doctor", None))
        status_value = attrs.get("status", getattr(self.instance, "status", None))

        if user and user.role == User.Role.PATIENT and patient and patient.user_id != user.id:
            raise serializers.ValidationError({"patient": "You can only book appointments for your own patient profile."})
        if user and user.role == User.Role.PATIENT and self.instance is not None:
            if self.instance.patient.user_id != user.id or set(attrs.keys()) - {"status"} or status_value != Appointment.Status.CANCELLED:
                raise serializers.ValidationError("Patients may only cancel their own appointments.")
            if self.instance.status in {Appointment.Status.COMPLETED, Appointment.Status.CANCELLED}:
                raise serializers.ValidationError({"status": "This appointment can no longer be cancelled."})
        if user and user.role == User.Role.DOCTOR:
            if self.instance is None:
                raise serializers.ValidationError("Doctors cannot book appointments through this endpoint.")
            if self.instance.doctor.user_id != user.id:
                raise serializers.ValidationError("You can only update your own appointments.")
            if set(attrs.keys()) - {"status"}:
                raise serializers.ValidationError("Doctors may only update appointment status.")
            if status_value != Appointment.Status.COMPLETED:
                raise serializers.ValidationError({"status": "Doctors may mark their appointments as completed only."})

        if patient and doctor and self.instance is None:
            if not doctor.is_active:
                raise serializers.ValidationError({"doctor": "Selected doctor is not active."})

        # Admin/receptionist edits that move an appointment (or reactivate a
        # cancelled slot) must obey the same availability and conflict rules
        # as a new booking. Status-only completion/cancellation does not need
        # to revalidate a slot that was already reserved.
        if self.instance is not None:
            schedule_fields = {"doctor", "appointment_date", "start_time", "end_time"}
            schedule_changed = bool(schedule_fields.intersection(attrs))
            reactivating = (
                "status" in attrs
                and self.instance.status == Appointment.Status.CANCELLED
                and attrs["status"] != Appointment.Status.CANCELLED
            )
            if schedule_changed or reactivating:
                validate_appointment_slot(
                    doctor=doctor,
                    appointment_date=attrs.get("appointment_date", self.instance.appointment_date),
                    start_time=attrs.get("start_time", self.instance.start_time),
                    end_time=attrs.get("end_time", self.instance.end_time),
                    exclude_appointment_id=self.instance.pk,
                )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return book_appointment(created_by=request.user, **validated_data)
