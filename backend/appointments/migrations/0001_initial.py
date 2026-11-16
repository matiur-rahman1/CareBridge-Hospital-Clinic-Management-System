import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("doctors", "0001_initial"),
        ("patients", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="Appointment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("appointment_date", models.DateField()),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("CONFIRMED", "Confirmed"), ("COMPLETED", "Completed"), ("CANCELLED", "Cancelled")], default="PENDING", max_length=12)),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_appointments", to=settings.AUTH_USER_MODEL)),
                ("doctor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="appointments", to="doctors.doctor")),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="appointments", to="patients.patient")),
            ],
            options={"ordering": ["appointment_date", "start_time"]},
        ),
        migrations.AddConstraint(model_name="appointment", constraint=models.CheckConstraint(condition=models.Q(("end_time__gt", models.F("start_time"))), name="appointment_end_after_start")),
        migrations.AddConstraint(model_name="appointment", constraint=models.UniqueConstraint(condition=models.Q(("status__in", ["PENDING", "CONFIRMED", "COMPLETED"])), fields=("doctor", "appointment_date", "start_time"), name="unique_active_doctor_appointment_start")),
        migrations.AddIndex(model_name="appointment", index=models.Index(fields=["appointment_date", "status"], name="appt_date_status_idx")),
        migrations.AddIndex(model_name="appointment", index=models.Index(fields=["doctor", "appointment_date"], name="appt_doctor_date_idx")),
        migrations.AddIndex(model_name="appointment", index=models.Index(fields=["patient", "appointment_date"], name="appt_patient_date_idx")),
    ]
