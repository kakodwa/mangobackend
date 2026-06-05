from django.contrib import admin
from .models import Wallet, WalletTransaction, Withdrawal,CompanyWallet,CompanyWalletTransaction


admin.site.register(CompanyWallet)

admin.site.register(CompanyWalletTransaction)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "balance",
        "currency",
        "total_earnings",
        "total_withdrawn",
        "updated_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "user__phone_number",
    )

    list_filter = (
        "currency",
        "updated_at",
    )

    ordering = ("-updated_at",)


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "wallet",
        "transaction_type",
        "source",
        "amount",
        "balance_before",
        "balance_after",
        "created_at",
    )

    search_fields = (
        "wallet__user__username",
        "reference",
        "description",
    )

    list_filter = (
        "transaction_type",
        "source",
        "created_at",
    )

    ordering = ("-created_at",)


admin.site.register(Withdrawal)

