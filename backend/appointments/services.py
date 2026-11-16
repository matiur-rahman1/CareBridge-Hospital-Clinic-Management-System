from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Appointment


def validate_appointment_slot(*, doctor, appointment_date, start_time, end_time, exclude_appointment_id=None):
    """Validate a time window against doctor availability and existing visits."""
    if appointment_date < timezone.localdate():
        raise ValidationError({"appointment_date": "Appointments cannot be booked in the past."})
    if appointment_date == timezone.localdate() and start_time <= timezone.localtime().time().replace(tzinfo=None):
        raise ValidationError({"start_time": "Choose a future time for today's appointment."})
    if start_time >= end_time:
        raise ValidationError({"end_time": "End time must be later than start time."})
    if not doctor.is_active:
        raise ValidationError({"doctor": "This doctor is not currently accepting appointments."})

    availability = doctor.availabilities.filter(
        weekday=appointment_date.weekday(), is_active=True,
        start_time__lte=start_time, end_time__gte=end_time,
    ).first()
    if availability is None:
        raise ValidationError({"start_time": "The selected time is outside the doctor's availability."})
    start_minutes = start_time.hour * 60 + start_time.minute
    availability_start = availability.start_time.hour * 60 + availability.start_time.minute
    duration_minutes = (end_time.hour * 60 + end_time.minute) - start_minutes
    if (start_minutes - availability_start) % availability.slot_minutes != 0 or duration_minutes % availability.slot_minutes != 0:
        raise ValidationError({"start_time": f"Choose a time aligned to the doctor's {availability.slot_minutes}-minute appointment slots."})

    conflicts = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appointment_date,
        status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED, Appointment.Status.COMPLETED],
        start_time__lt=end_time,
        end_time__gt=start_time,
    )
    if exclude_appointment_id is not None:
        conflicts = conflicts.exclude(pk=exclude_appointment_id)
    if conflicts.exists():
        raise ValidationError({"start_time": "This doctor already has an appointment during the selected time."})


@transaction.atomic
def book_appointment(*, patient, doctor, appointment_date, start_time, end_time, created_by=None, **extra):
    """Create an appointment after validating availability and overlapping bookings."""
    validate_appointment_slot(
        doctor=doctor,
        appointment_date=appointment_date,
        start_time=start_time,
        end_time=end_time,
    )
    try:
        with transaction.atomic():
            return Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_date=appointment_date,
                start_time=start_time,
                end_time=end_time,
                created_by=created_by,
                **extra,
            )
    except IntegrityError as exc:
        raise ValidationError({"start_time": "This doctor already has an appointment at that time."}) from exc
