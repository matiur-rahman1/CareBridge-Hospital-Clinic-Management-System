from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User


class AuthenticationTests(APITestCase):
    def test_user_can_obtain_jwt_token_with_email(self):
        User.objects.create_user(email="login@example.com", password="StrongPassword123!", first_name="Login")
        response = self.client.post("/api/auth/token/", {
            "email": "login@example.com", "password": "StrongPassword123!"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["user"]["role"], User.Role.PATIENT)

    def test_public_registration_creates_patient_role_and_profile(self):
        response = self.client.post("/api/auth/register/", {
            "email": "newpatient@example.com",
            "password": "SecurePass123!",
            "first_name": "New",
            "last_name": "Patient",
            "phone": "01700000000",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="newpatient@example.com")
        self.assertEqual(user.role, User.Role.PATIENT)
        self.assertTrue(hasattr(user, "patient_profile"))

    def test_patient_cannot_escalate_role_during_registration(self):
        response = self.client.post("/api/auth/register/", {
            "email": "attacker@example.com", "password": "SecurePass123!",
            "first_name": "Attacker", "role": "ADMIN",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(email="attacker@example.com").role, User.Role.PATIENT)

    def test_jwt_refresh_rotates_tokens(self):
        User.objects.create_user(email="refresh@example.com", password="StrongPassword123!", first_name="Refresh")
        login = self.client.post("/api/auth/token/", {
            "email": "refresh@example.com", "password": "StrongPassword123!"
        }, format="json")
        self.assertEqual(login.status_code, status.HTTP_200_OK, login.data)
        refreshed = self.client.post("/api/auth/token/refresh/", {
            "refresh": login.data["refresh"]
        }, format="json")
        self.assertEqual(refreshed.status_code, status.HTTP_200_OK, refreshed.data)
        self.assertIn("access", refreshed.data)
        self.assertIn("refresh", refreshed.data)
        self.assertNotEqual(refreshed.data["refresh"], login.data["refresh"])

    def test_patient_account_name_update_syncs_patient_directory(self):
        from patients.models import Patient
        patient_user = User.objects.create_user(
            email="profile@example.com", password="StrongPassword123!",
            first_name="Initial", last_name="Name", role=User.Role.PATIENT,
        )
        patient = Patient.objects.create(user=patient_user, full_name="Initial Name", email=patient_user.email)
        self.client.force_authenticate(patient_user)
        response = self.client.patch("/api/auth/me/", {
            "first_name": "Updated", "last_name": "Patient"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        patient.refresh_from_db()
        self.assertEqual(patient.full_name, "Updated Patient")
