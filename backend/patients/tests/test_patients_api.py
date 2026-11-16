from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from patients.models import Patient


class PatientApiTests(APITestCase):
    def setUp(self):
        self.receptionist = User.objects.create_user("frontdesk@example.com", "StrongPassword123!", first_name="Front", role=User.Role.RECEPTIONIST)

    def test_receptionist_can_register_patient_and_id_is_generated(self):
        self.client.force_authenticate(self.receptionist)
        response = self.client.post("/api/patients/", {
            "full_name": "Rina Akter", "email": "rina@example.com", "phone": "01712345678",
            "gender": "FEMALE", "blood_group": "B+", "address": "Dhaka",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertRegex(response.data["patient_id"], r"^PAT\d{4,}$")

    def test_patient_can_only_list_own_patient_profile(self):
        patient_user = User.objects.create_user("self@example.com", "StrongPassword123!", first_name="Self", role=User.Role.PATIENT)
        own = Patient.objects.create(user=patient_user, full_name="Self Patient", email="self@example.com")
        Patient.objects.create(full_name="Other Patient", email="other@example.com")
        self.client.force_authenticate(patient_user)
        response = self.client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], own.id)

    def test_patient_cannot_create_patient_record_for_another_person(self):
        patient_user = User.objects.create_user("own@example.com", "StrongPassword123!", first_name="Own", role=User.Role.PATIENT)
        self.client.force_authenticate(patient_user)
        response = self.client.post("/api/patients/", {"full_name": "Someone Else"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
