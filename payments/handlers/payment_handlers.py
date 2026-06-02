from decimal import Decimal
from collections import defaultdict

from django.db import transaction
from django.db.models import F
from payments.core.escrow import EscrowService
from products.models import Product
from delivery.models import Delivery
from wallet.models import (
    Wallet,
    WalletTransaction,
    CompanyWalletTransaction
)
from events.models import EventTicketType

# =========================================================
# PROPERTY UNLOCK HANDLER
# =========================================================
def handle_property_unlock(payment, company_wallet):

    with transaction.atomic():

        unlock = payment.property_unlock

        unlock.is_unlocked = True
        unlock.save()

        owner = unlock.property.owner

        owner_wallet, _ = Wallet.objects.get_or_create(
            user=owner
        )

        commission_rate = Decimal("15.00")

        owner_amount = payment.amount * (
            Decimal("1") - (commission_rate / Decimal("100"))
        )

        company_amount = payment.amount * (
            commission_rate / Decimal("100")
        )

        owner_before = owner_wallet.balance

        owner_wallet.balance += owner_amount
        owner_wallet.total_earnings += owner_amount
        owner_wallet.save()

        WalletTransaction.objects.create(
            wallet=owner_wallet,
            transaction_type="credit",
            source="property_unlock",
            amount=owner_amount,
            transaction_rate=commission_rate,
            balance_before=owner_before,
            balance_after=owner_wallet.balance,
            reference=payment.payment_reference,
            description=f"Property unlock #{unlock.id}"
        )

        company_before = company_wallet.balance

        company_wallet.balance += company_amount
        company_wallet.total_earnings += company_amount
        company_wallet.save()

        CompanyWalletTransaction.objects.create(
            wallet=company_wallet,
            transaction_type="credit",
            source="property_unlock_commission",
            amount=company_amount,
            transaction_rate=commission_rate,
            balance_before=company_before,
            balance_after=company_wallet.balance,
            reference=payment.payment_reference,
            description=f"Commission from property unlock #{unlock.id}"
        )

# =========================================================
# BOOKING HANDLER
# =========================================================
def handle_booking(payment, company_wallet):

    with transaction.atomic():

        booking = payment.booking

        if not booking:
            raise Exception("Booking not linked to payment")

        if booking.payment_status == "paid":
            return

        booking.booking_status = "confirmed"
        booking.payment_status = "paid"
        booking.save()

        owner = booking.room.lodge.owner

        EscrowService.hold(
            payment=payment,
            beneficiary=owner,
            escrow_type="booking",
            amount=payment.amount,
            commission_rate=Decimal("10.00")
        )
# =========================================================
# TICKET HANDLER
# =========================================================
def handle_ticket(payment, company_wallet):

    with transaction.atomic():

        ticket = payment.ticket_purchase

        if not ticket:
            raise Exception("Ticket not linked to payment")

        if ticket.payment_status == "paid":
            return

        event = ticket.event

        for item in ticket.items.select_related("ticket_type"):

            updated = EventTicketType.objects.filter(
                id=item.ticket_type.id,
                available_seats__gte=item.quantity
            ).update(
                available_seats=F("available_seats") - item.quantity
            )

            if updated == 0:
                raise Exception(
                    f"Not enough seats for {item.ticket_type.name}"
                )

        ticket.payment_status = "paid"
        ticket.save()

        EscrowService.hold(
            payment=payment,
            beneficiary=event.organizer,
            escrow_type="ticket",
            amount=payment.amount,
            commission_rate=Decimal("10.00")
        )
# =========================================================
# WALLET TOPUP
# =========================================================
def handle_wallet_topup(payment):

    with transaction.atomic():

        wallet, _ = Wallet.objects.get_or_create(
            user=payment.user
        )

        before = wallet.balance

        wallet.balance += payment.amount
        wallet.save()

        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type="credit",
            source="wallet_topup",
            amount=payment.amount,
            transaction_rate=Decimal("0.00"),
            balance_before=before,
            balance_after=wallet.balance,
            reference=payment.payment_reference,
            description="Wallet Topup"
        )