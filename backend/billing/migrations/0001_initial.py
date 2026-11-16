import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("appointments", "0001_initial"),
        ("patients", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="Invoice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("invoice_number", models.CharField(blank=True, editable=False, max_length=16, unique=True)),
                ("issue_date", models.DateField(auto_now_add=True)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("consultation_fee", models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
                ("discount_amount", models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
                ("subtotal", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("total_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("payment_status", models.CharField(choices=[("UNPAID", "Unpaid"), ("PARTIALLY_PAID", "Partially Paid"), ("PAID", "Paid")], default="UNPAID", max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("appointment", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="invoice", to="appointments.appointment")),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="invoices_created", to=settings.AUTH_USER_MODEL)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="invoices", to="patients.patient")),
            ],
            options={"ordering": ["-issue_date", "-id"]},
        ),
        migrations.CreateModel(
            name="InvoiceItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("description", models.CharField(max_length=180)),
                ("quantity", models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
                ("invoice", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="billing.invoice")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))])),
                ("payment_date", models.DateTimeField(auto_now_add=True)),
                ("method", models.CharField(choices=[("CASH", "Cash"), ("CARD", "Card"), ("BANK_TRANSFER", "Bank transfer"), ("MOBILE_BANKING", "Mobile banking")], default="CASH", max_length=20)),
                ("reference", models.CharField(blank=True, max_length=120)),
                ("notes", models.CharField(blank=True, max_length=255)),
                ("invoice", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="billing.invoice")),
                ("received_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="payments_received", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-payment_date", "-id"]},
        ),
    ]
