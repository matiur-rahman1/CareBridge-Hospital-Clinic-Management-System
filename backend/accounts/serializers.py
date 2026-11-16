from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[])
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "full_name", "role", "date_joined")
        read_only_fields = ("id", "role", "date_joined")

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return normalized


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[])
    password = serializers.CharField(write_only=True, validators=[validate_password])
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ("id", "email", "password", "first_name", "last_name", "phone", "date_of_birth")
        read_only_fields = ("id",)

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return normalized

    @transaction.atomic
    def create(self, validated_data):
        from patients.models import Patient
        phone = validated_data.pop("phone", "")
        dob = validated_data.pop("date_of_birth", None)
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, role=User.Role.PATIENT, **validated_data)
        Patient.objects.create(
            user=user,
            full_name=user.get_full_name(),
            email=user.email,
            phone=phone,
            date_of_birth=dob,
        )
        return user


class CareBridgeTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["name"] = user.get_full_name()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
