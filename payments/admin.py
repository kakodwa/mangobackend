from django.contrib import admin
from .models import Payment, PaymentWebhook


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "payment_reference",
        "user",
        "amount",
        "payment_method",
        "status",
        "paychangu_transaction_id",
        "created_at",
        "paid_at",
    )

    search_fields = (
        "payment_reference",
        "paychangu_transaction_id",
        "user__first_name",
        "user__last_name",
        "user__phone_number",
    )

    list_filter = (
        "status",
        "payment_method",
        "created_at",
        "paid_at",
    )

    ordering = ("-created_at",)

    autocomplete_fields = ("user",)

    list_editable = ("status",)

    readonly_fields = ("payment_reference", "paychangu_transaction_id")


@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(admin.ModelAdmin):
    list_display = (
        "payment",
        "processed",
        "created_at",
    )

    search_fields = (
        "payment__payment_reference",
        "payment__paychangu_transaction_id",
    )

    list_filter = (
        "processed",
        "created_at",
    )

    ordering = ("-created_at",)

    readonly_fields = ("webhook_data",)