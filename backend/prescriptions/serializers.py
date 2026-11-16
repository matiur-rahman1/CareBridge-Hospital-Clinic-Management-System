from django.db import transaction
from rest_framework import serializers
from accounts.models import User
from .models import Prescription, PrescriptionMedicine


class PrescriptionMedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionMedicine
        fields = ("id", "medicine_name", "dosage", "duration", "quantity", "instructions")
        read_only_fields = ("id",)


class PrescriptionSerializer(serializers.ModelSerializer):
    medicines = PrescriptionMedicineSerializer(many=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.full_name", read_only=True)

    class Meta:
        model = Prescription
        fields = (
            "id", "appointment", "patient", "patient_name", "doctor", "doctor_name",
            "prescription_date", "diagnosis", "instructions", "medicines", "created_by", "created_at", "updated_at",
        )
        read_only_fields = ("id", "prescription_date", "created_by", "created_at", "updated_at")

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        appointment = attrs.get("appointment", getattr(self.instance, "appointment", None))
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        doctor = attrs.get("doctor", getattr(self.instance, "doctor", None))
        medicines = attrs.get("medicines", None)

        if medicines is not None and len(medicines) == 0:
            raise serializers.ValidationError({"medicines": "Add at least one medicine to the prescription."})
        if appointment and patient and appointment.patient_id != patient.id:
            raise serializers.ValidationError({"appointment": "The appointment belongs to a different patient."})
        if appointment and doctor and appointment.doctor_id != doctor.id:
            raise serializers.ValidationError({"appointment": "The appointment belongs to a different doctor."})
        if user and user.role == User.Role.DOCTOR and self.instance is not None:
            if self.instance.doctor.user_id != user.id or (doctor and doctor.user_id != user.id):
                raise serializers.ValidationError({"doctor": "You can only edit prescriptions under your own doctor profile."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        medicines = validated_data.pop("medicines")
        validated_data["created_by"] = self.context["request"].user
        prescription = Prescription.objects.create(**validated_data)
        PrescriptionMedicine.objects.bulk_create([
            PrescriptionMedicine(prescription=prescription, **medicine) for medicine in medicines
        ])
        return prescription

    @transaction.atomic
    def update(self, instance, validated_data):
        medicines = validated_data.pop("medicines", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if medicines is not None:
            instance.medicines.all().delete()
            PrescriptionMedicine.objects.bulk_create([
                PrescriptionMedicine(prescription=instance, **medicine) for medicine in medicines
            ])
        return instance
