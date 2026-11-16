import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [(migrations.swappable_dependency(settings.AUTH_USER_MODEL))]
    operations = [
        migrations.CreateModel(
            name="Doctor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("doctor_id", models.CharField(blank=True, editable=False, max_length=12, unique=True)),
                ("full_name", models.CharField(max_length=160)),
                ("specialization", models.CharField(max_length=120)),
                ("qualifications", models.CharField(blank=True, max_length=255)),
                ("email", models.EmailField(blank=True, max_length=254, null=True, unique=True)),
                ("phone", models.CharField(blank=True, max_length=25)),
                ("consultation_fee", models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ("bio", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="doctor_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["full_name"]},
        ),
        migrations.CreateModel(
            name="DoctorAvailability",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("weekday", models.PositiveSmallIntegerField(choices=[(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday")])),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("slot_minutes", models.PositiveSmallIntegerField(default=30, validators=[django.core.validators.MinValueValidator(5)])),
                ("is_active", models.BooleanField(default=True)),
                ("doctor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="availabilities", to="doctors.doctor")),
            ],
            options={"ordering": ["weekday", "start_time"]},
        ),
        migrations.AddConstraint(model_name="doctoravailability", constraint=models.CheckConstraint(condition=models.Q(("end_time__gt", models.F("start_time"))), name="availability_end_after_start")),
        migrations.AddConstraint(model_name="doctoravailability", constraint=models.UniqueConstraint(fields=("doctor", "weekday", "start_time", "end_time"), name="unique_doctor_availability_window")),
        migrations.AddIndex(model_name="doctor", index=models.Index(fields=["specialization"], name="doctor_specialization_idx")),
        migrations.AddIndex(model_name="doctor", index=models.Index(fields=["is_active"], name="doctor_active_idx")),
    ]
