from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers
from .models import Invoice, InvoiceItem, Payment


class InvoiceItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = InvoiceItem
        fields = ("id", "description", "quantity", "unit_price", "line_total")
        read_only_fields = ("id", "line_total")


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, required=False)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    appointment_id = serializers.IntegerField(source="appointment.id", read_only=True)
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    payment_status_display = serializers.CharField(source="get_payment_status_display", read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "id", "invoice_number", "patient", "patient_name", "appointment", "appointment_id",
            "issue_date", "due_date", "consultation_fee", "discount_amount", "items", "subtotal",
            "total_amount", "amount_paid", "balance_due", "payment_status", "payment_status_display",
            "notes", "created_by", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "invoice_number", "issue_date", "subtotal", "total_amount", "amount_paid", "balance_due",
            "payment_status", "payment_status_display", "appointment_id", "created_by", "created_at", "updated_at",
        )

    def validate(self, attrs):
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        appointment = attrs.get("appointment", getattr(self.instance, "appointment", None))
        discount = attrs.get("discount_amount", getattr(self.instance, "discount_amount", Decimal("0.00")))
        fee = attrs.get("consultation_fee", getattr(self.instance, "consultation_fee", Decimal("0.00")))
        items = attrs.get("items", None)
        if appointment and patient and appointment.patient_id != patient.id:
            raise serializers.ValidationError({"appointment": "The appointment belongs to a different patient."})
        if appointment and "consultation_fee" not in attrs and self.instance is None:
            attrs["consultation_fee"] = appointment.doctor.consultation_fee
            fee = attrs["consultation_fee"]
        if discount > fee + sum((item["quantity"] * item["unit_price"] for item in (items or [])), Decimal("0.00")) and items is not None:
            raise serializers.ValidationError({"discount_amount": "Discount cannot exceed the invoice subtotal."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items", [])
        validated_data["created_by"] = self.context["request"].user
        invoice = Invoice.objects.create(**validated_data)
        InvoiceItem.objects.bulk_create([InvoiceItem(invoice=invoice, **item) for item in items])
        invoice.recalculate_totals()
        if invoice.discount_amount > invoice.subtotal:
            raise serializers.ValidationError({"discount_amount": "Discount cannot exceed the invoice subtotal."})
        return invoice

    @transaction.atomic
    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if items is not None:
            instance.items.all().delete()
            InvoiceItem.objects.bulk_create([InvoiceItem(invoice=instance, **item) for item in items])
        instance.recalculate_totals()
        if instance.discount_amount > instance.subtotal:
            raise serializers.ValidationError({"discount_amount": "Discount cannot exceed the invoice subtotal."})
        if instance.amount_paid > instance.total_amount:
            raise serializers.ValidationError({"discount_amount": "The new total cannot be lower than payments already received."})
        return instance


class PaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)
    patient_name = serializers.CharField(source="invoice.patient.full_name", read_only=True)

    class Meta:
        model = Payment
        fields = ("id", "invoice", "invoice_number", "patient_name", "amount", "payment_date", "method", "reference", "notes", "received_by")
        read_only_fields = ("id", "payment_date", "received_by", "invoice_number", "patient_name")

    def validate(self, attrs):
        invoice = attrs.get("invoice")
        amount = attrs.get("amount", Decimal("0.00"))
        if invoice:
            already_paid = invoice.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            if amount <= 0:
                raise serializers.ValidationError({"amount": "Payment must be greater than zero."})
            if already_paid + amount > invoice.total_amount:
                raise serializers.ValidationError({"amount": f"Payment exceeds the outstanding balance of {max(invoice.total_amount - already_paid, Decimal('0.00'))}."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        invoice_id = validated_data["invoice"].id
        invoice = Invoice.objects.select_for_update().get(pk=invoice_id)
        already_paid = invoice.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        if already_paid + validated_data["amount"] > invoice.total_amount:
            raise serializers.ValidationError({"amount": "Payment exceeds the outstanding balance."})
        validated_data["invoice"] = invoice
        validated_data["received_by"] = self.context["request"].user
        return Payment.objects.create(**validated_data)
