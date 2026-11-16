"""Create repeatable, fictional CareBridge demonstration data.

The command is deliberately idempotent: known demo profiles are upserted, demo
appointments are identified by their creator + participants + reason (not by a
moving calendar date), and invoice lines/payments are reconciled on every run.
It does not delete unrelated users, appointments, invoices, or clinical records.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import User
from appointments.models import Appointment
from billing.models import Invoice, InvoiceItem, Payment
from doctors.models import Doctor, DoctorAvailability
from patients.models import Patient
from prescriptions.models import Prescription, PrescriptionMedicine


DEMO_PASSWORDS = {
    "admin@carebridge.demo": "Admin@12345",
    "reception@carebridge.demo": "Reception@12345",
    "doctor@carebridge.demo": "Doctor@12345",
    "patient@carebridge.demo": "Patient@12345",
}


class Command(BaseCommand):
    help = "Create or refresh fictional CareBridge demonstration users and hospital data."

    def _user(self, email, first_name, last_name, role, *, is_staff=False):
        email = email.strip().lower()
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "is_staff": is_staff or role == User.Role.ADMIN,
                "is_superuser": role == User.Role.ADMIN,
                "is_active": True,
            },
        )
        changed = []
        expected = {
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
            "is_staff": is_staff or role == User.Role.ADMIN,
            "is_superuser": role == User.Role.ADMIN,
            "is_active": True,
        }
        for field, value in expected.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                changed.append(field)

        password = DEMO_PASSWORDS[email]
        if created or not user.check_password(password):
            user.set_password(password)
            changed.append("password")
        if changed:
            user.save(update_fields=changed)
        return user

    @staticmethod
    def _patient(user, *, full_name, email, phone, dob, gender, blood_group, address):
        # Prefer the linked account profile so reruns repair a stale email or
        # detached profile instead of creating a second one-to-one relation.
        patient = Patient.objects.filter(user=user).first() if user else None
        if patient is None:
            patient = Patient.objects.filter(email=email).first()
        if patient is None:
            patient = Patient(user=user)
        patient.user = user
        patient.full_name = full_name
        patient.email = email
        patient.phone = phone
        patient.date_of_birth = date.fromisoformat(dob)
        patient.gender = gender
        patient.blood_group = blood_group
        patient.address = address
        patient.save()
        return patient

    @staticmethod
    def _doctor(user, *, full_name, specialization, qualifications, email, phone, fee):
        doctor = Doctor.objects.filter(user=user).first() if user else None
        if doctor is None:
            doctor = Doctor.objects.filter(email=email).first()
        if doctor is None:
            doctor = Doctor(user=user)
        doctor.user = user
        doctor.full_name = full_name
        doctor.specialization = specialization
        doctor.qualifications = qualifications
        doctor.email = email
        doctor.phone = phone
        doctor.consultation_fee = Decimal(fee)
        doctor.is_active = True
        doctor.save()
        return doctor

    @staticmethod
    def _ensure_availability(doctor):
        for weekday in range(7):
            DoctorAvailability.objects.update_or_create(
                doctor=doctor,
                weekday=weekday,
                start_time=time(9, 0),
                end_time=time(17, 0),
                defaults={"slot_minutes": 30, "is_active": True},
            )

    @staticmethod
    def _has_conflict(doctor, day, start, end, *, exclude_id=None):
        conflicts = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=day,
            status__in=(
                Appointment.Status.PENDING,
                Appointment.Status.CONFIRMED,
                Appointment.Status.COMPLETED,
            ),
            start_time__lt=end,
            end_time__gt=start,
        )
        if exclude_id:
            conflicts = conflicts.exclude(pk=exclude_id)
        return conflicts.exists()

    def _available_demo_slot(self, doctor, day, preferred_start, *, exclude_id=None):
        """Keep preferred demo times where possible; otherwise find a free slot."""
        starts = [time(hour, minute) for hour in range(9, 17) for minute in (0, 30)]
        preferred_minutes = preferred_start.hour * 60 + preferred_start.minute
        starts.sort(key=lambda value: abs(value.hour * 60 + value.minute - preferred_minutes))
        for start in starts:
            end_dt = datetime.combine(day, start) + timedelta(minutes=30)
            end = end_dt.time()
            if self._has_conflict(doctor, day, start, end, exclude_id=exclude_id):
                continue
            return start, end
        raise CommandError(
            f"No available 30-minute demo slot for {doctor.full_name} on {day}. "
            "Clear a conflicting appointment or rerun after changing clinic availability."
        )

    def _appointment(self, *, admin_user, patient, doctor, day, preferred_start, status, reason):
        # The tuple below is stable across days. The old implementation keyed
        # on appointment_date/start_time and accumulated a new set every day.
        appointment = Appointment.objects.filter(
            created_by=admin_user,
            patient=patient,
            doctor=doctor,
            reason=reason,
        ).order_by("pk").first()
        start, end = self._available_demo_slot(
            doctor, day, preferred_start, exclude_id=appointment.pk if appointment else None
        )
        if appointment is None:
            appointment = Appointment(
                created_by=admin_user,
                patient=patient,
                doctor=doctor,
                appointment_date=day,
                start_time=start,
                end_time=end,
                status=status,
                reason=reason,
            )
        else:
            appointment.patient = patient
            appointment.doctor = doctor
            appointment.appointment_date = day
            appointment.start_time = start
            appointment.end_time = end
            appointment.status = status
            appointment.reason = reason
        appointment.created_by = admin_user
        appointment.save()
        return appointment

    @staticmethod
    def _invoice(*, admin_user, appointment, patient, fee, discount, notes, item_specs):
        invoice, _ = Invoice.objects.get_or_create(
            appointment=appointment,
            defaults={
                "patient": patient,
                "consultation_fee": Decimal(fee),
                "discount_amount": Decimal(discount),
                "notes": notes,
                "created_by": admin_user,
            },
        )
        invoice.patient = patient
        invoice.consultation_fee = Decimal(fee)
        invoice.discount_amount = Decimal(discount)
        invoice.notes = notes
        invoice.created_by = admin_user
        invoice.save()

        expected_descriptions = []
        for description, quantity, unit_price in item_specs:
            expected_descriptions.append(description)
            InvoiceItem.objects.update_or_create(
                invoice=invoice,
                description=description,
                defaults={
                    "quantity": quantity,
                    "unit_price": Decimal(unit_price),
                },
            )
        invoice.items.exclude(description__in=expected_descriptions).delete()
        invoice.recalculate_totals()
        return invoice

    @staticmethod
    def _payment(invoice, *, reference, amount, method, notes, received_by):
        payment, _ = Payment.objects.update_or_create(
            invoice=invoice,
            reference=reference,
            defaults={
                "amount": Decimal(amount),
                "method": method,
                "notes": notes,
                "received_by": received_by,
            },
        )
        # The demo invoice is owned by this seed scenario; remove only stale
        # seeded payments while preserving unrelated payment references.
        expected_prefix = f"DEMO-{invoice.pk}-"
        invoice.payments.filter(
            Q(reference="DEMO-PAY-001") | Q(reference__startswith=expected_prefix)
        ).exclude(pk=payment.pk).delete()
        invoice.recalculate_totals()
        return payment

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding CareBridge demonstration data...")

        admin_user = self._user(
            "admin@carebridge.demo", "CareBridge", "Administrator", User.Role.ADMIN, is_staff=True
        )
        self._user(
            "reception@carebridge.demo", "Demo", "Receptionist", User.Role.RECEPTIONIST
        )
        doctor_user = self._user(
            "doctor@carebridge.demo", "Ayesha", "Rahman", User.Role.DOCTOR
        )
        patient_user = self._user(
            "patient@carebridge.demo", "Arif", "Hasan", User.Role.PATIENT
        )

        doctor_specs = [
            (doctor_user, "Ayesha Rahman", "Cardiology", "MBBS, FCPS (Cardiology)", "doctor@carebridge.demo", "01710000001", "1200.00"),
            (None, "Farhan Ahmed", "Neurology", "MBBS, MD (Neurology)", "farhan.ahmed@carebridge.demo", "01710000002", "1500.00"),
            (None, "Nusrat Jahan", "Pediatrics", "MBBS, DCH", "nusrat.jahan@carebridge.demo", "01710000003", "1000.00"),
        ]
        doctors = [
            self._doctor(
                user,
                full_name=name,
                specialization=specialty,
                qualifications=qualification,
                email=email,
                phone=phone,
                fee=fee,
            )
            for user, name, specialty, qualification, email, phone, fee in doctor_specs
        ]
        for doctor in doctors:
            self._ensure_availability(doctor)

        patient_specs = [
            (patient_user, "Arif Hasan", "patient@carebridge.demo", "01711000001", "1995-03-14", "MALE", "O+", "12 Lake Road, Dhaka"),
            (None, "Samira Akter", "samira.akter@carebridge.demo", "01711000002", "1988-07-22", "FEMALE", "A+", "Dhanmondi, Dhaka"),
            (None, "Tanvir Hossain", "tanvir.hossain@carebridge.demo", "01711000003", "2001-11-09", "MALE", "B+", "Uttara, Dhaka"),
            (None, "Maliha Chowdhury", "maliha.chowdhury@carebridge.demo", "01711000004", "1992-01-31", "FEMALE", "AB+", "Mirpur, Dhaka"),
            (None, "Sabbir Alam", "sabbir.alam@carebridge.demo", "01711000005", "1979-05-18", "MALE", "A-", "Banani, Dhaka"),
        ]
        patients = [
            self._patient(
                user,
                full_name=name,
                email=email,
                phone=phone,
                dob=dob,
                gender=gender,
                blood_group=blood_group,
                address=address,
            )
            for user, name, email, phone, dob, gender, blood_group, address in patient_specs
        ]

        today = timezone.localdate()
        appointment_specs = [
            (patients[0], doctors[0], today, time(10, 0), Appointment.Status.COMPLETED, "Cardiology follow-up"),
            (patients[1], doctors[0], today, time(11, 0), Appointment.Status.CONFIRMED, "Routine check-up"),
            (patients[2], doctors[1], today, time(12, 0), Appointment.Status.PENDING, "Headache consultation"),
            (patients[3], doctors[2], today + timedelta(days=1), time(14, 0), Appointment.Status.CONFIRMED, "Child wellness visit"),
            (patients[4], doctors[1], today + timedelta(days=2), time(15, 0), Appointment.Status.CANCELLED, "Follow-up visit"),
        ]
        appointments = [
            self._appointment(
                admin_user=admin_user,
                patient=patient,
                doctor=doctor,
                day=day,
                preferred_start=preferred_start,
                status=status,
                reason=reason,
            )
            for patient, doctor, day, preferred_start, status, reason in appointment_specs
        ]

        prescription, _ = Prescription.objects.update_or_create(
            appointment=appointments[0],
            defaults={
                "patient": patients[0],
                "doctor": doctors[0],
                "diagnosis": "Essential hypertension",
                "instructions": "Monitor blood pressure and return for follow-up in four weeks.",
                "created_by": doctor_user,
            },
        )
        medicine_specs = [
            ("Amlodipine", "5 mg", "30 days", 30, "Take one tablet once daily after breakfast."),
            ("Losartan", "25 mg", "30 days", 30, "Take one tablet once daily."),
        ]
        expected_medicines = []
        for name, dosage, duration, quantity, instructions in medicine_specs:
            expected_medicines.append(name)
            PrescriptionMedicine.objects.update_or_create(
                prescription=prescription,
                medicine_name=name,
                defaults={
                    "dosage": dosage,
                    "duration": duration,
                    "quantity": quantity,
                    "instructions": instructions,
                },
            )
        prescription.medicines.exclude(medicine_name__in=expected_medicines).delete()

        partial_invoice = self._invoice(
            admin_user=admin_user,
            appointment=appointments[0],
            patient=patients[0],
            fee=doctors[0].consultation_fee,
            discount="100.00",
            notes="Demo consultation invoice with a partial payment.",
            item_specs=[
                ("ECG", 1, "800.00"),
                ("Cardiology assessment", 1, "300.00"),
            ],
        )
        self._payment(
            partial_invoice,
            reference=f"DEMO-{partial_invoice.pk}-PARTIAL",
            amount="1000.00",
            method=Payment.Method.MOBILE_BANKING,
            notes="Fictional demonstration partial payment.",
            received_by=admin_user,
        )

        unpaid_invoice = self._invoice(
            admin_user=admin_user,
            appointment=appointments[1],
            patient=patients[1],
            fee=doctors[0].consultation_fee,
            discount="0.00",
            notes="Unpaid demonstration invoice.",
            item_specs=[],
        )
        # Remove only payments created by this command if the invoice was
        # converted from a prior seed iteration to the unpaid scenario.
        unpaid_invoice.payments.filter(
            Q(reference="DEMO-PAY-001")
            | Q(reference__startswith=f"DEMO-{unpaid_invoice.pk}-")
        ).delete()
        unpaid_invoice.recalculate_totals()

        paid_invoice = self._invoice(
            admin_user=admin_user,
            appointment=appointments[2],
            patient=patients[2],
            fee=doctors[1].consultation_fee,
            discount="0.00",
            notes="Paid demonstration invoice.",
            item_specs=[("Neurology assessment", 1, "500.00")],
        )
        self._payment(
            paid_invoice,
            reference=f"DEMO-{paid_invoice.pk}-PAID",
            amount=paid_invoice.total_amount,
            method=Payment.Method.CASH,
            notes="Fictional demonstration payment settled in full.",
            received_by=admin_user,
        )

        self.stdout.write(self.style.SUCCESS("CareBridge demo data is ready."))
        self.stdout.write(
            f"Created/updated: {User.objects.filter(email__in=DEMO_PASSWORDS).count()} demo users, "
            f"{len(doctors)} doctors, {len(patients)} patients, {len(appointments)} appointments, "
            f"{DoctorAvailability.objects.filter(doctor__in=doctors).count()} availability windows, "
            f"1 prescription, {Invoice.objects.filter(appointment__in=appointments).count()} invoices."
        )
        self.stdout.write("Demo accounts (fictional local data only):")
        for email, password in DEMO_PASSWORDS.items():
            self.stdout.write(f"  {email}  |  {password}")
