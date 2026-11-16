from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum


class Invoice(models.Model):
    class PaymentStatus(models.TextChoices):
        UNPAID = "UNPAID", "Unpaid"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Partially Paid"
        PAID = "PAID", "Paid"

    invoice_number = models.CharField(max_length=16, unique=True, blank=True, editable=False)
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="invoices")
    appointment = models.OneToOneField(
        "appointments.Appointment", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="invoice"
    )
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal("0.00"))])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal("0.00"))])
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="invoices_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issue_date", "-id"]

    def save(self, *args, **kwargs):
        creating = self.pk is None
        if creating and not self.invoice_number:
            import uuid
            self.invoice_number = f"TMP{uuid.uuid4().hex[:13].upper()}"
        super().save(*args, **kwargs)
        if creating and self.invoice_number.startswith("TMP"):
            self.invoice_number = f"INV{self.pk:07d}"
            super().save(update_fields=["invoice_number"])

    @property
    def amount_paid(self):
        return self.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    @property
    def balance_due(self):
        return max(self.total_amount - self.amount_paid, Decimal("0.00"))

    def recalculate_totals(self, save=True):
        item_total = sum((item.line_total for item in self.items.all()), Decimal("0.00"))
        self.subtotal = self.consultation_fee + item_total
        self.total_amount = max(self.subtotal - self.discount_amount, Decimal("0.00"))
        paid = self.amount_paid
        if self.total_amount == 0 or paid >= self.total_amount:
            self.payment_status = self.PaymentStatus.PAID
        elif paid > 0:
            self.payment_status = self.PaymentStatus.PARTIALLY_PAID
        else:
            self.payment_status = self.PaymentStatus.UNPAID
        if save and self.pk:
            self.save(update_fields=["subtotal", "total_amount", "payment_status", "updated_at"])
        return self

    def __str__(self):
        return self.invoice_number or f"Invoice #{self.pk}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=180)
    quantity = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])

    class Meta:
        ordering = ["id"]

    @property
    def line_total(self):
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invoice.recalculate_totals()

    def delete(self, *args, **kwargs):
        invoice = self.invoice
        result = super().delete(*args, **kwargs)
        invoice.recalculate_totals()
        return result

    def __str__(self):
        return self.description


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        CARD = "CARD", "Card"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank transfer"
        MOBILE_BANKING = "MOBILE_BANKING", "Mobile banking"

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    payment_date = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.CASH)
    reference = models.CharField(max_length=120, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="payments_received")

    class Meta:
        ordering = ["-payment_date", "-id"]

    def __str__(self):
        return f"Payment {self.amount} for {self.invoice.invoice_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invoice.recalculate_totals()

    def delete(self, *args, **kwargs):
        invoice = self.invoice
        result = super().delete(*args, **kwargs)
        invoice.recalculate_totals()
        return result
