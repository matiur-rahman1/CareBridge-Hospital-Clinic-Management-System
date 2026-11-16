from django.contrib import admin
from .models import Invoice, InvoiceItem, Payment


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("payment_date",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "patient", "issue_date", "total_amount", "payment_status")
    list_filter = ("payment_status", "issue_date")
    search_fields = ("invoice_number", "patient__full_name", "patient__patient_id")
    inlines = [InvoiceItemInline, PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("invoice", "amount", "method", "payment_date", "received_by")
    list_filter = ("method", "payment_date")
    search_fields = ("invoice__invoice_number", "reference")
