from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from patients.models import Patient
from billing.models import Invoice


class BillingApiTests(APITestCase):
    def setUp(self):
        self.receptionist = User.objects.create_user("billingdesk@example.com", "StrongPassword123!", first_name="Billing", role=User.Role.RECEPTIONIST)
        self.patient = Patient.objects.create(full_name="Invoice Patient", email="invoicepatient@example.com")
        self.client.force_authenticate(self.receptionist)

    def test_invoice_calculates_items_discount_and_payment_status(self):
        response = self.client.post("/api/invoices/", {
            "patient": self.patient.id,
            "consultation_fee": "100.00",
            "discount_amount": "10.00",
            "items": [{"description": "Lab test", "quantity": 2, "unit_price": "50.00"}],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        invoice_id = response.data["id"]
        invoice = Invoice.objects.get(pk=invoice_id)
        self.assertEqual(str(invoice.subtotal), "200.00")
        self.assertEqual(str(invoice.total_amount), "190.00")
        self.assertEqual(invoice.payment_status, Invoice.PaymentStatus.UNPAID)

        first_payment = self.client.post("/api/payments/", {
            "invoice": invoice.id, "amount": "100.00", "method": "CASH", "reference": "CASH-1"
        }, format="json")
        self.assertEqual(first_payment.status_code, status.HTTP_201_CREATED, first_payment.data)
        invoice.refresh_from_db()
        self.assertEqual(invoice.payment_status, Invoice.PaymentStatus.PARTIALLY_PAID)

        second_payment = self.client.post("/api/payments/", {
            "invoice": invoice.id, "amount": "90.00", "method": "CARD", "reference": "CARD-1"
        }, format="json")
        self.assertEqual(second_payment.status_code, status.HTTP_201_CREATED, second_payment.data)
        invoice.refresh_from_db()
        self.assertEqual(invoice.payment_status, Invoice.PaymentStatus.PAID)
        self.assertEqual(invoice.amount_paid, invoice.total_amount)

    def test_overpayment_is_rejected(self):
        invoice = Invoice.objects.create(patient=self.patient, consultation_fee="50.00")
        invoice.recalculate_totals()
        response = self.client.post("/api/payments/", {
            "invoice": invoice.id, "amount": "60.00", "method": "CASH"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
