from rest_framework import serializers
from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    profile_picture_url = serializers.SerializerMethodField()

    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True, validators=[])

    class Meta:
        model = Patient
        fields = (
            "id", "patient_id", "user_id", "full_name", "email", "phone",
            "date_of_birth", "gender", "address", "blood_group",
            "profile_picture", "profile_picture_url", "registration_date", "created_at", "updated_at",
        )
        read_only_fields = ("id", "patient_id", "registration_date", "created_at", "updated_at", "user_id", "profile_picture_url")

    def get_profile_picture_url(self, obj):
        request = self.context.get("request")
        if obj.profile_picture and request:
            return request.build_absolute_uri(obj.profile_picture.url)
        return obj.profile_picture.url if obj.profile_picture else None

    def validate_email(self, value):
        normalized = value.strip().lower() if value else None
        if normalized and Patient.objects.filter(email__iexact=normalized).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError("A patient with this email address already exists.")
        return normalized

    def validate_date_of_birth(self, value):
        from django.utils import timezone
        if value and value > timezone.localdate():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value
