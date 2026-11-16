import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("appointments", "0001_initial"),
        ("doctors", "0001_initial"),
        ("patients", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="Prescription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("prescription_date", models.DateField(auto_now_add=True)),
                ("diagnosis", models.CharField(blank=True, max_length=255)),
                ("instructions", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("appointment", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="prescription", to="appointments.appointment")),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="prescriptions_created", to=settings.AUTH_USER_MODEL)),
                ("doctor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="prescriptions", to="doctors.doctor")),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="prescriptions", to="patients.patient")),
            ],
            options={"ordering": ["-prescription_date", "-created_at"]},
        ),
        migrations.CreateModel(
            name="PrescriptionMedicine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("medicine_name", models.CharField(max_length=160)),
                ("dosage", models.CharField(max_length=100)),
                ("duration", models.CharField(max_length=100)),
                ("quantity", models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ("instructions", models.CharField(blank=True, max_length=255)),
                ("prescription", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="medicines", to="prescriptions.prescription")),
            ],
            options={"ordering": ["id"]},
        ),
    ]
