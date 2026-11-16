from datetime import time, timedelta
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from patients.models import Patient
from doctors.models import Doctor, DoctorAvailability
from appointments.models import Appointment


class AppointmentBookingTests(APITestCase):
    def setUp(self):
        self.receptionist = User.objects.create_user("desk@example.com", "StrongPassword123!", first_name="Desk", role=User.Role.RECEPTIONIST)
        self.patient = Patient.objects.create(full_name="Booking Patient", email="booking@example.com")
        self.doctor_user = User.objects.create_user("doc@example.com", "StrongPassword123!", first_name="Doctor", role=User.Role.DOCTOR)
        self.doctor = Doctor.objects.create(user=self.doctor_user, full_name="Dr Test", specialization="Cardiology", email="doc@example.com")
        self.day = timezone.localdate() + timedelta(days=7)
        DoctorAvailability.objects.create(doctor=self.doctor, weekday=self.day.weekday(), start_time=time(9), end_time=time(17), slot_minutes=15)
        self.client.force_authenticate(self.receptionist)

    def payload(self, start="09:00:00", end="09:30:00"):
        return {
            "patient": self.patient.id, "doctor": self.doctor.id,
            "appointment_date": self.day.isoformat(), "start_time": start, "end_time": end,
            "reason": "Routine appointment",
        }

    def test_receptionist_can_book_appointment(self):
        response = self.client.post("/api/appointments/", self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_overlapping_doctor_booking_is_rejected(self):
        first = self.client.post("/api/appointments/", self.payload(), format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED, first.data)
        second = self.client.post("/api/appointments/", self.payload("09:15:00", "09:45:00"), format="json")
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_cancelled_booking_releases_time_slot(self):
        Appointment.objects.create(patient=self.patient, doctor=self.doctor, appointment_date=self.day,
                                   start_time=time(9), end_time=time(9, 30), status=Appointment.Status.CANCELLED)
        response = self.client.post("/api/appointments/", self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_receptionist_cannot_move_appointment_into_an_overlapping_slot(self):
        first = self.client.post("/api/appointments/", self.payload("09:00:00", "09:30:00"), format="json")
        second = self.client.post("/api/appointments/", self.payload("10:00:00", "10:30:00"), format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED, first.data)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED, second.data)
        response = self.client.patch(
            f"/api/appointments/{second.data['id']}/",
            {"start_time": "09:15:00", "end_time": "09:45:00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_cancelled_appointment_can_only_be_reactivated_when_slot_is_free(self):
        cancelled = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor, appointment_date=self.day,
            start_time=time(9), end_time=time(9, 30), status=Appointment.Status.CANCELLED,
        )
        booked = self.client.post("/api/appointments/", self.payload("09:00:00", "09:30:00"), format="json")
        self.assertEqual(booked.status_code, status.HTTP_201_CREATED, booked.data)
        response = self.client.patch(
            f"/api/appointments/{cancelled.id}/", {"status": "CONFIRMED"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_patient_can_book_only_their_own_profile(self):
        patient_user = User.objects.create_user(
            "portalpatient@example.com", "StrongPassword123!", first_name="Portal",
            role=User.Role.PATIENT,
        )
        own_profile = Patient.objects.create(user=patient_user, full_name="Portal Patient", email=patient_user.email)
        self.client.force_authenticate(patient_user)
        payload = self.payload()
        payload["patient"] = own_profile.id
        response = self.client.post("/api/appointments/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        payload["patient"] = self.patient.id
        denied = self.client.post("/api/appointments/", payload, format="json")
        self.assertEqual(denied.status_code, status.HTTP_400_BAD_REQUEST, denied.data)
