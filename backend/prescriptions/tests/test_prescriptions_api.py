from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from patients.models import Patient
from doctors.models import Doctor
from prescriptions.models import Prescription


class PrescriptionApiTests(APITestCase):
    def setUp(self):
        self.doctor_user = User.objects.create_user("prescriber@example.com", "StrongPassword123!", first_name="Prescriber", role=User.Role.DOCTOR)
        self.doctor = Doctor.objects.create(user=self.doctor_user, full_name="Dr Prescriber", specialization="Medicine", email="prescriber@example.com")
        self.patient = Patient.objects.create(full_name="Prescription Patient", email="rxpatient@example.com")
        self.client.force_authenticate(self.doctor_user)

    def test_doctor_can_create_prescription_with_multiple_medicines(self):
        response = self.client.post("/api/prescriptions/", {
            "patient": self.patient.id, "doctor": self.doctor.id,
            "diagnosis": "Seasonal allergy", "instructions": "Drink water and rest.",
            "medicines": [
                {"medicine_name": "Cetirizine", "dosage": "10 mg", "duration": "5 days", "quantity": 5, "instructions": "At night"},
                {"medicine_name": "Saline spray", "dosage": "2 sprays", "duration": "7 days", "quantity": 1, "instructions": "Twice daily"},
            ],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Prescription.objects.get().medicines.count(), 2)

    def test_doctor_cannot_prescribe_under_another_doctors_profile(self):
        other_user = User.objects.create_user("otherdoc@example.com", "StrongPassword123!", first_name="Other", role=User.Role.DOCTOR)
        other_doctor = Doctor.objects.create(user=other_user, full_name="Other Doctor", specialization="ENT", email="otherdoc@example.com")
        response = self.client.post("/api/prescriptions/", {
            "patient": self.patient.id, "doctor": other_doctor.id,
            "medicines": [{"medicine_name": "Test", "dosage": "1", "duration": "1 day"}],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
