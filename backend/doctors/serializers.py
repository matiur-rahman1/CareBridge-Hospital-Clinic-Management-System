from rest_framework import serializers
from accounts.models import User
from .models import Doctor, DoctorAvailability


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    weekday_name = serializers.CharField(source="get_weekday_display", read_only=True)

    class Meta:
        model = DoctorAvailability
        fields = ("id", "doctor", "weekday", "weekday_name", "start_time", "end_time", "slot_minutes", "is_active")
        read_only_fields = ("id", "weekday_name")

    def validate(self, attrs):
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        doctor = attrs.get("doctor", getattr(self.instance, "doctor", None))
        weekday = attrs.get("weekday", getattr(self.instance, "weekday", None))
        active = attrs.get("is_active", getattr(self.instance, "is_active", True))
        if start and end and start >= end:
            raise serializers.ValidationError({"end_time": "End time must be later than start time."})
        if doctor and start and end and active:
            overlaps = DoctorAvailability.objects.filter(
                doctor=doctor, weekday=weekday, is_active=True,
                start_time__lt=end, end_time__gt=start,
            )
            if self.instance:
                overlaps = overlaps.exclude(pk=self.instance.pk)
            if overlaps.exists():
                raise serializers.ValidationError({"start_time": "This availability overlaps another active availability window."})
        return attrs


class DoctorSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True, validators=[])
    availabilities = DoctorAvailabilitySerializer(many=True, read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = Doctor
        fields = (
            "id", "doctor_id", "user", "user_id", "full_name", "specialization",
            "qualifications", "email", "phone", "consultation_fee", "bio",
            "is_active", "availabilities", "created_at", "updated_at",
        )
        read_only_fields = ("id", "doctor_id", "user_id", "created_at", "updated_at")

    def validate_email(self, value):
        normalized = value.strip().lower() if value else None
        if normalized and Doctor.objects.filter(email__iexact=normalized).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError("A doctor with this email address already exists.")
        return normalized

    def validate_user(self, user):
        if user and user.role != User.Role.DOCTOR:
            raise serializers.ValidationError("The linked account must have the Doctor role.")
        return user
