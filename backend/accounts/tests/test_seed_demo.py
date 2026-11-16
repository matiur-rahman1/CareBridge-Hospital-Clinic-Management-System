from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from accounts.management.commands.seed_demo import DEMO_PASSWORDS
from accounts.models import User
from appointments.models import Appointment
from billing.models import Invoice, InvoiceItem, Payment
from doctors.models import Doctor, DoctorAvailability
from patients.models import Patient
from prescriptions.models import Prescription, PrescriptionMedicine


class SeedDemoCommandTests(TestCase):
    def run_seed(self):
        call_command("seed_demo", stdout=StringIO())

    def snapshot(self):
        return {
            "demo_users": User.objects.filter(email__in=DEMO_PASSWORDS).count(),
            "doctors": Doctor.objects.count(),
            "patients": Patient.objects.count(),
            "appointments": Appointment.objects.count(),
            "availability": DoctorAvailability.objects.count(),
            "prescriptions": Prescription.objects.count(),
            "medicines": PrescriptionMedicine.objects.count(),
            "invoices": Invoice.objects.count(),
            "invoice_items": InvoiceItem.objects.count(),
            "payments": Payment.objects.count(),
        }

    def test_seed_creates_all_four_accounts_and_expected_demo_graph(self):
        self.run_seed()

        self.assertEqual(self.snapshot(), {
            "demo_users": 4,
            "doctors": 3,
            "patients": 5,
            "appointments": 5,
            "availability": 21,
            "prescriptions": 1,
            "medicines": 2,
            "invoices": 3,
            "invoice_items": 3,
            "payments": 2,
        })

        expected_roles = {
            "admin@carebridge.demo": User.Role.ADMIN,
            "reception@carebridge.demo": User.Role.RECEPTIONIST,
            "doctor@carebridge.demo": User.Role.DOCTOR,
            "patient@carebridge.demo": User.Role.PATIENT,
        }
        for email, role in expected_roles.items():
            account = User.objects.get(email=email)
            self.assertEqual(account.role, role)
            self.assertTrue(account.is_active)
            self.assertTrue(account.check_password(DEMO_PASSWORDS[email]))

        admin = User.objects.get(email="admin@carebridge.demo")
        doctor_user = User.objects.get(email="doctor@carebridge.demo")
        patient_user = User.objects.get(email="patient@carebridge.demo")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(doctor_user.doctor_profile.email, doctor_user.email)
        self.assertEqual(patient_user.patient_profile.email, patient_user.email)

        self.assertEqual(set(Appointment.objects.values_list("status", flat=True)), {
            Appointment.Status.PENDING,
            Appointment.Status.CONFIRMED,
            Appointment.Status.COMPLETED,
            Appointment.Status.CANCELLED,
        })
        for doctor in Doctor.objects.all():
            self.assertEqual(
                set(doctor.availabilities.values_list("weekday", flat=True)),
                set(range(7)),
            )
            self.assertTrue(doctor.availabilities.filter(is_active=True).exists())

        prescription = Prescription.objects.select_related("appointment", "patient", "doctor").get()
        self.assertEqual(prescription.patient_id, prescription.appointment.patient_id)
        self.assertEqual(prescription.doctor_id, prescription.appointment.doctor_id)
        self.assertEqual(prescription.medicines.count(), 2)

        invoices_by_status = {
            invoice.payment_status: invoice
            for invoice in Invoice.objects.prefetch_related("payments").all()
        }
        self.assertEqual(set(invoices_by_status), {
            Invoice.PaymentStatus.UNPAID,
            Invoice.PaymentStatus.PARTIALLY_PAID,
            Invoice.PaymentStatus.PAID,
        })
        partial = invoices_by_status[Invoice.PaymentStatus.PARTIALLY_PAID]
        paid = invoices_by_status[Invoice.PaymentStatus.PAID]
        unpaid = invoices_by_status[Invoice.PaymentStatus.UNPAID]
        self.assertEqual(partial.amount_paid, partial.total_amount - partial.balance_due)
        self.assertGreater(partial.balance_due, 0)
        self.assertEqual(unpaid.amount_paid, 0)
        self.assertEqual(unpaid.balance_due, unpaid.total_amount)
        self.assertEqual(paid.amount_paid, paid.total_amount)
        self.assertEqual(paid.balance_due, 0)

        for invoice in Invoice.objects.select_related("appointment", "patient"):
            if invoice.appointment_id:
                self.assertEqual(invoice.patient_id, invoice.appointment.patient_id)

    def test_running_seed_twice_is_idempotent(self):
        self.run_seed()
        first = self.snapshot()
        self.run_seed()
        second = self.snapshot()
        self.assertEqual(second, first)

        self.assertEqual(
            DoctorAvailability.objects.values("doctor_id", "weekday", "start_time", "end_time").distinct().count(),
            21,
        )
        self.assertEqual(
            Appointment.objects.filter(reason="Cardiology follow-up").count(),
            1,
        )
        self.assertEqual(Payment.objects.filter(reference__startswith="DEMO-").count(), 2)

    def test_seed_updates_existing_demo_accounts_to_documented_roles_and_passwords(self):
        self.run_seed()
        receptionist = User.objects.get(email="reception@carebridge.demo")
        receptionist.role = User.Role.ADMIN
        receptionist.is_staff = True
        receptionist.set_password("TemporaryWrongPassword123!")
        receptionist.save()

        self.run_seed()
        receptionist.refresh_from_db()
        self.assertEqual(receptionist.role, User.Role.RECEPTIONIST)
        self.assertFalse(receptionist.is_staff)
        self.assertFalse(receptionist.is_superuser)
        self.assertTrue(receptionist.check_password(DEMO_PASSWORDS[receptionist.email]))

    def test_seed_reuses_appointments_when_demo_calendar_date_changes(self):
        first_day = timezone.localdate()
        shifted_day = first_day + timedelta(days=10)
        with patch("accounts.management.commands.seed_demo.timezone.localdate", return_value=first_day):
            self.run_seed()
        first_snapshot = self.snapshot()

        with patch("accounts.management.commands.seed_demo.timezone.localdate", return_value=shifted_day):
            self.run_seed()
        second_snapshot = self.snapshot()

        self.assertEqual(second_snapshot, first_snapshot)
        self.assertEqual(
            set(Appointment.objects.values_list("appointment_date", flat=True)),
            {shifted_day, shifted_day + timedelta(days=1), shifted_day + timedelta(days=2)},
        )

    def test_seed_does_not_delete_unrelated_appointments(self):
        self.run_seed()
        manual_user = User.objects.create_user(
            email="manual-reception@example.com",
            password="ManualPassword123!",
            first_name="Manual",
            role=User.Role.RECEPTIONIST,
        )
        manual_patient = Patient.objects.create(full_name="Independent Patient")
        manual_doctor = Doctor.objects.create(
            full_name="Independent Doctor",
            specialization="General Medicine",
        )
        manual_appointment = Appointment.objects.create(
            patient=manual_patient,
            doctor=manual_doctor,
            appointment_date=timezone.localdate() + timedelta(days=5),
            start_time="09:00",
            end_time="09:30",
            status=Appointment.Status.CONFIRMED,
            reason="Independent clinic booking",
            created_by=manual_user,
        )

        self.run_seed()
        self.assertTrue(Appointment.objects.filter(pk=manual_appointment.pk).exists())
        self.assertEqual(manual_appointment.reason, "Independent clinic booking")

    def test_seed_reconciles_legacy_demo_payment_reference(self):
        self.run_seed()
        partial = Invoice.objects.get(appointment__reason="Cardiology follow-up")
        admin = User.objects.get(email="admin@carebridge.demo")
        Payment.objects.create(
            invoice=partial,
            amount="1000.00",
            method=Payment.Method.MOBILE_BANKING,
            reference="DEMO-PAY-001",
            received_by=admin,
        )

        self.run_seed()
        partial.refresh_from_db()
        self.assertEqual(partial.payments.count(), 1)
        seeded_payment = partial.payments.get()
        self.assertEqual(seeded_payment.reference, f"DEMO-{partial.pk}-PARTIAL")
        self.assertEqual(seeded_payment.amount, partial.total_amount - partial.balance_due)
        self.assertEqual(partial.payment_status, Invoice.PaymentStatus.PARTIALLY_PAID)
