from decimal import Decimal

from wallet.models import (
    Wallet,
    WalletTransaction,
    CompanyWallet,
    CompanyWalletTransaction
)

from payments.models import EscrowWallet


class SettlementService:

    @staticmethod
    def release(escrow: EscrowWallet):

        if escrow.status != "held":
            return escrow

        commission_rate = escrow.commission_rate or Decimal("0")

        beneficiary_wallet, _ = Wallet.objects.get_or_create(
            user=escrow.beneficiary
        )


        company_wallet, _ = CompanyWallet.objects.get_or_create(
            name="Main Company Wallet"
            )

        # =========================
        # CALCULATIONS
        # =========================
        commission = (escrow.amount * commission_rate) / Decimal("100")
        beneficiary_amount = escrow.amount - commission

        # =========================
        # BENEFICIARY PAYMENT
        # =========================
        before_beneficiary = beneficiary_wallet.balance

        beneficiary_wallet.balance += beneficiary_amount
        beneficiary_wallet.total_earnings += beneficiary_amount
        beneficiary_wallet.save()

        WalletTransaction.objects.create(
            wallet=beneficiary_wallet,
            transaction_type="credit",
            source=f"escrow_{escrow.escrow_type}",
            amount=beneficiary_amount,
            transaction_rate=commission_rate,
            balance_before=before_beneficiary,
            balance_after=beneficiary_wallet.balance,
            reference=str(escrow.payment.payment_reference),
            description=f"Escrow release ({escrow.escrow_type})"
        )

        # =========================
        # COMPANY PAYMENT
        # =========================
        before_company = company_wallet.balance

        company_wallet.balance += commission
        company_wallet.total_earnings += commission
        company_wallet.save()

        CompanyWalletTransaction.objects.create(
            wallet=company_wallet,
            transaction_type="credit",
            source=f"{escrow.escrow_type}_commission",
            amount=commission,
            transaction_rate=commission_rate,
            balance_before=before_company,
            balance_after=company_wallet.balance,
            reference=str(escrow.payment.payment_reference),
            description=f"Commission from {escrow.escrow_type}"
        )

        # =========================
        # MARK AS RELEASED
        # =========================
        escrow.status = "released"
        escrow.save()

        return escrow