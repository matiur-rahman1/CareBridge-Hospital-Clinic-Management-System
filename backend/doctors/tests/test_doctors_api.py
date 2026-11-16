from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from doctors.models import Doctor


class DoctorApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin@example.com", "StrongPassword123!", first_name="Admin")

    def test_admin_can_create_doctor(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/doctors/", {
            "full_name": "Dr. New Person", "specialization": "Dermatology",
            "qualifications": "MBBS, MD", "email": "doctor.new@example.com",
            "phone": "01712345678", "consultation_fee": "850.00", "is_active": True,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertRegex(response.data["doctor_id"], r"^DOC\d{4,}$")
        self.assertTrue(Doctor.objects.filter(email="doctor.new@example.com").exists())

    def test_patient_can_browse_but_cannot_create_doctor(self):
        patient = User.objects.create_user("patient@example.com", "StrongPassword123!", first_name="Patient")
        self.client.force_authenticate(patient)
        response = self.client.post("/api/doctors/", {"full_name": "Unauthorized", "specialization": "ENT"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
